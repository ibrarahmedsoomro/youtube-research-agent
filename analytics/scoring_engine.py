"""
scoring_engine.py: vidIQ-style deterministic scoring for the YouTube agent.

Scores: Keyword, Title, Content, Channel Review.
No LLM and no network calls: pure functions, so the same input always gives the same output.
Missing inputs are dropped and the remaining weights are renormalised (see combine()),
and every result reports `coverage` so the UI can show how much data backed the score.
"""
from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass, field
from typing import Optional, Sequence

RUBRIC_VERSION = "2026.09-a"      # store this in the `scores` table; bump on any weight change

# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def unit(x: float, lo: float, hi: float) -> float:
    """Map x from [lo, hi] to [0, 1], clipped."""
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def band(score: float) -> str:
    """Badge colour buckets: great=green, good=lime, fair=amber, poor=red."""
    return "great" if score >= 80 else "good" if score >= 60 else "fair" if score >= 40 else "poor"


def level(score: float) -> str:
    return "Low" if score < 25 else "Medium" if score < 50 else "High" if score < 75 else "Very High"


def combine(parts: dict[str, tuple[Optional[float], float]]) -> tuple[float, float]:
    """parts: name -> (score 0..100 or None, weight).
    None parts are dropped and remaining weights renormalised.
    Returns (weighted_score, coverage) where coverage = share of total weight that had data."""
    avail = {k: (s, w) for k, (s, w) in parts.items() if s is not None}
    total_w = sum(w for _, w in parts.values())
    if not avail or total_w == 0:
        return 0.0, 0.0
    aw = sum(w for _, w in avail.values())
    return sum(s * w for s, w in avail.values()) / aw, aw / total_w


# ----------------------------------------------------------------------------
# 1. KEYWORD SCORE  (all outputs are ESTIMATED: no public API gives real search volume)
# ----------------------------------------------------------------------------

@dataclass
class ResultVideo:
    title: str
    views: int
    age_days: float
    channel_subs: int


@dataclass
class KeywordSignals:
    keyword: str
    # 1..10 = position in YouTube autocomplete, 0 = checked but not suggested, None = not fetched
    autocomplete_position: Optional[int] = None
    trends_index: Optional[float] = None                       # 0..100 relative interest, None = not fetched
    top_results: list[ResultVideo] = field(default_factory=list)   # top 10-20 search results
    user_channel_subs: int = 0


def score_keyword(sig: KeywordSignals) -> dict:
    res = sig.top_results[:20]
    top10 = res[:10]
    kw_tokens = set(tokens(sig.keyword))

    # ---- volume proxy (0..100)
    if sig.autocomplete_position is None:
        ac = None
    elif sig.autocomplete_position == 0:
        ac = 0.0
    else:
        ac = clamp(100 - (sig.autocomplete_position - 1) * 9)

    rv = None
    if res:
        vpd = statistics.mean(v.views / max(v.age_days, 1.0) for v in res)
        rv = 100 * unit(math.log10(vpd + 1), 1.0, 4.5)          # ~10 views/day -> 0, ~30k/day -> 100

    volume, vol_cov = combine({"autocomplete": (ac, 0.40),
                               "trends": (sig.trends_index, 0.30),
                               "result_velocity": (rv, 0.30)})
    if vol_cov == 0:
        volume = None

    # ---- competition (0..100, higher = harder)
    competition = winnable = None
    if top10:
        med_views = statistics.median(v.views for v in top10)
        med_s = 100 * unit(math.log10(med_views + 1), 3.0, 6.5)             # 1k -> 0, ~3M -> 100
        big_s = 100 * sum(v.channel_subs >= 1_000_000 for v in top10) / len(top10)
        exact_s = 100 * sum(kw_tokens <= set(tokens(v.title)) for v in top10) / len(top10)
        competition, _ = combine({"median_views": (med_s, 0.45),
                                  "big_channels": (big_s, 0.35),
                                  "exact_match": (exact_s, 0.20)})

        # winnable: small channels or fresh uploads ranking = the SERP is beatable
        thresh = max(sig.user_channel_subs * 5, 10_000)
        small = sum(v.channel_subs <= thresh for v in top10) / len(top10)
        fresh = sum(v.age_days <= 90 for v in top10) / len(top10)
        winnable = 100 * (0.6 * small + 0.4 * fresh)

    overall, cov = combine({"volume": (volume, 0.50),
                            "ease": (None if competition is None else 100 - competition, 0.30),
                            "winnable": (winnable, 0.20)})
    return {
        "keyword": sig.keyword,
        "overall": round(overall),
        "volume": None if volume is None else round(volume),
        "competition": None if competition is None else round(competition),
        "winnable": None if winnable is None else round(winnable),
        "volume_level": None if volume is None else level(volume),
        "competition_level": None if competition is None else level(competition),
        "band": band(overall),
        "coverage": round(cov, 2),
        "truth_label": "estimated",
        "rubric_version": RUBRIC_VERSION,
    }


# ----------------------------------------------------------------------------
# 2. TITLE SCORE
# ----------------------------------------------------------------------------

# Lexicons are per-niche config: load a different set for horror / finance / gaming, etc.
LEX = {
    "open_loop": ("nobody", "no one", "never", "secret", "hidden", "unseen", "supposed to",
                  "the truth", "what happens", "won't believe", "leaked", "exposed", "revealed",
                  "discovered", "found", "before it"),
    "stakes": ("dead", "death", "danger", "warning", "banned", "last", "final", "deadly", "survive",
               "trapped", "haunted", "cursed", "forbidden", "illegal", "mistake", "failed"),
    "power": ("ultimate", "proven", "instantly", "shocking", "insane", "impossible", "brutal",
              "terrifying", "untold", "real", "truth"),
    "contrast": (" vs ", " versus ", " but ", "instead of", "without"),
}
VAGUE = ("stuff", "things", "amazing", "awesome", "epic", "crazy", "video", "content", "thing")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")

TITLE_WEIGHTS = {"length": 15, "front": 15, "curiosity": 15, "specificity": 10,
                 "clarity": 10, "demand": 15, "diff": 10, "hygiene": 10}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def score_title(title: str,
                primary_kw: Optional[str] = None,
                keyword_cluster: Optional[dict[str, float]] = None,   # keyword -> volume score 0..100
                competitor_titles: Optional[Sequence[str]] = None,
                deception_flag: bool = False,                          # set by the Critic agent
                banned_words: Sequence[str] = (),
                lex: dict = LEX) -> dict:
    t = (title or "").strip()
    n, low = len(t), t.lower()
    toks = tokens(t)
    words = t.split()
    emojis = len(EMOJI.findall(t))
    caps_words = [w for w in words
                  if len(re.sub(r"[^A-Za-z]", "", w)) >= 3
                  and re.sub(r"[^A-Za-z]", "", w).isupper()]

    # length: 35-75 chars full marks; -2 per char outside the band
    dist = 0 if 35 <= n <= 75 else (35 - n if n < 35 else n - 75)
    length_s = clamp(100 - 2.5 * dist)

    # keyword front-loading
    front_s = None
    if primary_kw:
        kw = primary_kw.lower()
        idx = low.find(kw)
        if idx >= 0:
            front_s = 100.0 if idx <= 20 else (100 - 30 * unit(idx, 20, 50) if idx <= 50 else 50.0)
        else:
            kt = tokens(primary_kw)
            share = sum(k in toks for k in kt) / len(kt) if kt else 0
            front_s = clamp(70 * share + 30)

    # curiosity / emotion / stakes (base 65 for clean title + boosts)
    cats = sum(any(p in f" {low} " for p in phrases) for phrases in lex.values())
    cats += 1 if "?" in t or any(q in low for q in ["why", "how", "what", "where", "which"]) else 0
    curiosity_s = clamp(65 + 18 * cats)

    # specificity: numbers, names, codes; vague words hurt (base 65)
    cap = [w for w in words[1:] if w[:1].isupper()]
    title_case = len(cap) / max(len(words) - 1, 1) > 0.6           # Title Case makes every word look like a name
    names = 0 if title_case else len(cap)
    has_num = bool(re.search(r"\d", t))
    vague_hits = sum(v in toks for v in VAGUE)
    specificity_s = clamp(65 + (20 if has_num else 0) + (15 if names >= 1 else 0)
                          - 10 * vague_hits)

    # clarity
    wc = len(words)
    clarity_s = 100 - 8 * (0 if 4 <= wc <= 14 else (4 - wc if wc < 4 else wc - 14))
    if words and statistics.mean(len(w) for w in words) > 9:
        clarity_s -= 10
    clarity_s = clamp(clarity_s)

    # demand alignment with the keyword cluster
    demand_s = None
    if keyword_cluster:
        hits = [vol for term, vol in keyword_cluster.items() if set(tokens(term)) <= set(toks)]
        demand_s = max(hits) if hits else 0.0

    # differentiation vs competitor titles (use embeddings cosine in production)
    diff_s = None
    if competitor_titles:
        sim = max(_jaccard(set(toks), set(tokens(c))) for c in competitor_titles)
        diff_s = 100 * (1 - sim)

    # hygiene: mobile truncation, separators, emoji, spacing
    hyg = 100.0
    hyg -= 20 if n > 85 else (10 if n > 75 else 0)
    hyg -= 15 if (t.count("|") + t.count(" - ")) > 2 else 0
    hyg -= 15 if emojis > 3 else 0
    hyg -= 10 if ("  " in t or t != title) else 0
    hygiene_s = clamp(hyg)

    parts = {
        "length": (length_s, TITLE_WEIGHTS["length"]),
        "front": (front_s, TITLE_WEIGHTS["front"]),
        "curiosity": (curiosity_s, TITLE_WEIGHTS["curiosity"]),
        "specificity": (specificity_s, TITLE_WEIGHTS["specificity"]),
        "clarity": (clarity_s, TITLE_WEIGHTS["clarity"]),
        "demand": (demand_s, TITLE_WEIGHTS["demand"]),
        "diff": (diff_s, TITLE_WEIGHTS["diff"]),
        "hygiene": (hygiene_s, TITLE_WEIGHTS["hygiene"]),
    }
    base, cov = combine(parts)

    penalties = {
        "caps": min(12, 4 * max(0, len(caps_words) - 1)),
        "emoji": 3 * max(0, emojis - 2),
        "banned": 10 * sum(b.lower() in low for b in banned_words),
        "deception": 25 if deception_flag else 0,
    }
    final = clamp(base - sum(penalties.values()))

    tips = []
    if n > 65:
        tips.append(f"Title is {n} chars: mobile feed may truncate it. Aim for 40-65.")
    elif n < 40:
        tips.append(f"Title is only {n} chars: add a specific detail or the keyword (aim for 40-65).")
    if front_s is not None and front_s < 60:
        tips.append("Move the primary keyword into the first 40 characters.")
    if curiosity_s < 35:
        tips.append("Add a hook: open loop, stakes, contrast, or a question.")
    if specificity_s < 50:
        tips.append("Add a number, a name, or a concrete detail.")
    if demand_s is not None and demand_s < 40:
        tips.append("Title does not match any high-demand keyword in the cluster.")
    if penalties["caps"]:
        tips.append("Too many ALL-CAPS words.")
    if penalties["deception"]:
        tips.append("Critic flagged the title as promising more than the video delivers.")

    return {
        "score": round(final),
        "band": band(final),
        "chars": n,
        "parts": {k: (None if s is None else round(s)) for k, (s, _) in parts.items()},
        "penalties": penalties,
        "coverage": round(cov, 2),
        "tips": tips,
        "truth_label": "rubric",
        "rubric_version": RUBRIC_VERSION,
    }


# ----------------------------------------------------------------------------
# 3. CONTENT SCORE  (description, chapters, hashtags, tags)
# ----------------------------------------------------------------------------

CHAPTER_RE = re.compile(r"^\s*(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\s+\S", re.M)


def parse_chapters(description: str) -> list[int]:
    return [int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            for m in CHAPTER_RE.finditer(description or "")]


def chapters_valid(stamps: list[int]) -> bool:
    """YouTube rules: starts at 0:00, at least 3 chapters, each at least 10 seconds."""
    return len(stamps) >= 3 and stamps[0] == 0 and all(b - a >= 10 for a, b in zip(stamps, stamps[1:]))


def score_content(description: str,
                  tags: Sequence[str] = (),
                  primary_kw: Optional[str] = None,
                  transcript_first_60s: Optional[str] = None,
                  has_captions: Optional[bool] = None) -> dict:
    d = description or ""
    lines = [ln for ln in d.splitlines() if ln.strip()]
    above = " ".join(lines[:2])[:200]

    fold, _ = combine({
        "kw": (None if not primary_kw else (100.0 if primary_kw.lower() in above.lower() else 0.0), 0.5),
        "len": (100.0 if len(above) >= 60 else (40.0 if above else 0.0), 0.25),
        "nolink": (100.0 if lines and "http" not in lines[0].lower() else 0.0, 0.25),
    })

    depth = 100 * unit(len(d), 100, 600)
    if len(d) > 4500:
        depth -= 30
    if primary_kw and d:
        density = d.lower().count(primary_kw.lower()) * len(primary_kw.split()) / max(len(tokens(d)), 1)
        if density > 0.04:                                    # keyword stuffing
            depth -= 40
    depth = clamp(depth)

    stamps = parse_chapters(d)
    chapters = 0.0 if not stamps else (100.0 if chapters_valid(stamps) else 40.0)

    tag_hash = len(re.findall(r"#\w+", d))
    hashtags = (0.0 if tag_hash == 0 else 60.0 if tag_hash <= 2 else 100.0 if tag_hash <= 5
                else 70.0 if tag_hash <= 8 else 30.0)

    total_tag_chars = sum(len(t) for t in tags)
    tags_s = (0.0 if not tags else 40.0 if total_tag_chars > 500
              else 50.0 if len(tags) < 5 else 100.0 if len(tags) <= 15 else 80.0)

    spoken = None
    if primary_kw and transcript_first_60s is not None:
        spoken = 100.0 if set(tokens(primary_kw)) <= set(tokens(transcript_first_60s)) else 0.0

    parts = {
        "above_fold": (fold, 20), "depth": (depth, 15), "chapters": (chapters, 15),
        "hashtags": (hashtags, 5), "tags": (tags_s, 5),
        "spoken_keyword": (spoken, 10),
        "captions": (None if has_captions is None else (100.0 if has_captions else 0.0), 10),
    }
    total, cov = combine(parts)

    tips = []
    if fold < 60:
        tips.append("First two lines: include the keyword and a hook, and keep links out of line 1.")
    if chapters == 0:
        tips.append("Add chapters (start at 0:00, at least 3, each 10s+).")
    elif chapters < 100:
        tips.append("Chapters are invalid: first must be 0:00, at least 3, each at least 10s apart.")
    if hashtags < 60:
        tips.append("Add 3-5 relevant hashtags (first three show above the title).")
    if spoken == 0.0:
        tips.append("Say the primary keyword in the first 60 seconds of the video.")

    return {"score": round(total), "band": band(total),
            "parts": {k: (None if s is None else round(s)) for k, (s, _) in parts.items()},
            "coverage": round(cov, 2), "tips": tips,
            "truth_label": "rubric", "rubric_version": RUBRIC_VERSION}


# ----------------------------------------------------------------------------
# 4. CHANNEL REVIEW SCORE
# ----------------------------------------------------------------------------

@dataclass
class VideoRec:
    id: str
    title: str
    views: int
    age_days: float
    description: str = ""
    tags: list[str] = field(default_factory=list)
    likes: int = 0
    comments: int = 0
    format: str = "long"              # "long" | "short" | "live"


def outlier_multiplier(target: VideoRec, videos: Sequence[VideoRec]) -> dict:
    """Age-adjusted, same-format outlier multiplier (log-linear views~age curve)."""
    pool = [v for v in videos if v.id != target.id and v.format == target.format and v.age_days >= 3]
    expected = 1.0
    if len(pool) >= 12:
        try:
            xs = [math.log1p(v.age_days) for v in pool]
            ys = [math.log1p(v.views) for v in pool]
            slope, icpt = statistics.linear_regression(xs, ys)
            expected = math.expm1(icpt + slope * math.log1p(target.age_days))
        except statistics.StatisticsError:
            expected = statistics.median(v.views for v in pool)
    elif pool:
        expected = statistics.median(v.views for v in pool)
    mult = target.views / max(expected, 1.0)
    label = ("mega_outlier" if mult >= 5 else "breakout" if mult >= 2
             else "underperform" if mult <= 0.5 else "normal")
    conf = min(1.0, len(pool) / 20) * (0.5 if target.age_days < 3 else 1.0)
    return {"multiplier": round(mult, 2), "label": label, "confidence": round(conf, 2)}


CHANNEL_WEIGHTS = {"consistency": 15, "reach": 20, "breakouts": 15,
                   "metadata": 20, "engagement": 15, "momentum": 15}

CHANNEL_ADVICE = {
    "consistency": "Upload on a steadier schedule. Gaps between uploads vary a lot or the channel has gone quiet.",
    "reach": "Videos reach a small share of your subscribers. Work on titles and thumbnails, and topics your subscribers search for.",
    "breakouts": "Few videos beat the channel's own baseline. Study your top outliers and repeat the title and thumbnail pattern.",
    "metadata": "Titles and descriptions score low on the rubric. Run Bulk Optimizer on the lowest-scoring videos.",
    "engagement": "Low like and comment rates. Add a clear question or CTA and reply to early comments.",
    "momentum": "Recent uploads underperform the channel's age-adjusted baseline. Review the last 10 videos for a shared cause.",
}


def score_channel(subs: int, videos: Sequence[VideoRec], fmt: Optional[str] = None,
                  n_recent: int = 20) -> dict:
    """Run separately for fmt='short' and fmt='long'; do not mix them."""
    vs = sorted((v for v in videos if fmt is None or v.format == fmt), key=lambda v: v.age_days)
    recent = vs[:n_recent]
    mature = [v for v in recent if v.age_days >= 7]

    # 1. consistency
    consistency = None
    if len(recent) >= 4:
        ages = sorted(v.age_days for v in recent)
        gaps = [b - a for a, b in zip(ages, ages[1:])]
        mean_gap = statistics.mean(gaps)
        if mean_gap > 0:
            cv = statistics.pstdev(gaps) / mean_gap
            regularity = 100 * (1 - unit(cv, 0.3, 1.5))
            med_gap = statistics.median(gaps)
            recency = 100 * (1 - unit(ages[0], med_gap * 1.5, med_gap * 5))
            consistency = 0.6 * regularity + 0.4 * recency

    # 2. reach = median views / subscribers (log scaled)
    reach = None
    if subs > 0 and mature:
        ratio = statistics.median(v.views for v in mature) / subs
        reach = 100 * unit(math.log10(max(ratio, 1e-6)), -2.5, 0.0)

    # 3 + 6. breakouts and momentum from the age-adjusted multiplier
    mults = [outlier_multiplier(v, vs) for v in mature]
    breakouts = momentum = None
    if len(mults) >= 5:
        n = len(mults)
        rate = sum(m["label"] in ("breakout", "mega_outlier") for m in mults) / n
        mega = sum(m["label"] == "mega_outlier" for m in mults) / n
        under = sum(m["label"] == "underperform" for m in mults) / n
        breakouts = clamp(100 * unit(rate + 0.5 * mega, 0, 0.25) - 20 * unit(under, 0.3, 0.7))
        r = statistics.median(m["multiplier"] for m in mults[:10])
        momentum = 100 * unit(math.log2(max(r, 1e-3)), -1, 1)      # 0.5x -> 0, 1x -> 50, 2x -> 100

    # 4. metadata quality = average of per-video title and content scores
    metadata = None
    if recent:
        ts = [score_title(v.title)["score"] for v in recent]
        cs = [score_content(v.description, v.tags)["score"] for v in recent]
        metadata = 0.5 * statistics.mean(ts) + 0.5 * statistics.mean(cs)

    # 5. engagement
    engagement = None
    seen = [v for v in mature if v.views > 0]
    if seen:
        like_rate = statistics.median(v.likes / v.views for v in seen)
        comment_rate = statistics.median(v.comments / v.views for v in seen)
        engagement = 100 * (0.7 * unit(like_rate, 0.005, 0.05) + 0.3 * unit(comment_rate, 0.0002, 0.004))

    parts = {"consistency": consistency, "reach": reach, "breakouts": breakouts,
             "metadata": metadata, "engagement": engagement, "momentum": momentum}
    total, cov = combine({k: (parts[k], CHANNEL_WEIGHTS[k]) for k in parts})

    # points_lost = how many of the 100 channel points this pillar cost (weight-adjusted)
    lost = sorted((((100 - s) * CHANNEL_WEIGHTS[k] / 100, k) for k, s in parts.items() if s is not None),
                  reverse=True)
    issues = [{"pillar": k, "points_lost": round(g, 1), "advice": CHANNEL_ADVICE[k]} for g, k in lost[:3] if g > 2]

    return {
        "score": round(total), "band": band(total),
        "pillars": {k: {"score": None if s is None else round(s), "weight": CHANNEL_WEIGHTS[k]}
                    for k, s in parts.items()},
        "top_issues": issues,
        "videos_analysed": len(recent),
        "coverage": round(cov, 2),
        "truth_label": "rubric",
        "rubric_version": RUBRIC_VERSION,
    }
