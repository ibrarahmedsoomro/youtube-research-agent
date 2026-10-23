"""Run with: python test_scoring_engine.py   (or: pytest -q)"""
import random
from scoring_engine import (KeywordSignals, ResultVideo, VideoRec, score_keyword, score_title,
                            score_content, score_channel, outlier_multiplier, parse_chapters,
                            chapters_valid, CHANNEL_WEIGHTS, TITLE_WEIGHTS)


def rv(views, age, subs, title="analog horror explained"):
    return ResultVideo(title=title, views=views, age_days=age, channel_subs=subs)


def test_keyword_strong_beats_weak():
    strong = KeywordSignals("analog horror", autocomplete_position=1, trends_index=80,
                            top_results=[rv(50_000, 30, 20_000) for _ in range(10)], user_channel_subs=5_000)
    weak = KeywordSignals("obscure phrase xyz", autocomplete_position=0, trends_index=5,
                          top_results=[rv(2_000_000, 900, 5_000_000) for _ in range(10)], user_channel_subs=5_000)
    s, w = score_keyword(strong), score_keyword(weak)
    assert s["overall"] > w["overall"]
    assert all(0 <= x["overall"] <= 100 for x in (s, w))
    assert s["truth_label"] == "estimated"


def test_keyword_missing_data_does_not_crash():
    r = score_keyword(KeywordSignals("anything"))
    assert r["coverage"] == 0.0 and r["overall"] == 0


def test_title_length_and_keyword():
    good = score_title("Nobody Was Supposed To Find TAPE 047 Analog Horror", primary_kw="analog horror")
    bad = score_title("analog horror " + "very long padding words " * 5, primary_kw="analog horror")
    assert good["score"] > bad["score"]
    assert any("truncate" in t for t in bad["tips"])


def test_title_deception_penalty_and_determinism():
    a = score_title("The message you weren't supposed to see 2026", primary_kw="message")
    b = score_title("The message you weren't supposed to see 2026", primary_kw="message", deception_flag=True)
    assert a["score"] - b["score"] == 25 or b["score"] == 0
    assert a == score_title("The message you weren't supposed to see 2026", primary_kw="message")


def test_title_caps_penalty():
    calm = score_title("Why this tape was never aired 1999")
    loud = score_title("WHY THIS TAPE WAS NEVER AIRED 1999")
    assert loud["penalties"]["caps"] > 0 and loud["score"] < calm["score"]


def test_weights_sum():
    assert sum(TITLE_WEIGHTS.values()) == 100 and sum(CHANNEL_WEIGHTS.values()) == 100


def test_chapters():
    good = "Intro\n0:00 Start\n0:45 Middle\n2:10 End"
    bad = "1:00 Start\n2:00 Middle\n3:00 End"
    assert chapters_valid(parse_chapters(good))
    assert not chapters_valid(parse_chapters(bad))
    assert score_content(good, ["a", "b", "c", "d", "e"], primary_kw="start")["parts"]["chapters"] == 100


def _channel(seed, healthy=True, n=30):
    rnd = random.Random(seed)
    vids = []
    for i in range(n):
        age = 4 + i * (6 if healthy else rnd.choice([3, 40, 90]))
        views = int(2000 * (1 + rnd.random() * (3 if healthy else 0.3)) * (1 + age / 60))
        vids.append(VideoRec(id=f"v{i}", title="Nobody Was Supposed To Find Tape 047" if healthy else "video stuff",
                             views=views, age_days=age, likes=int(views * (0.04 if healthy else 0.004)),
                             comments=int(views * (0.003 if healthy else 0.0001)),
                             description="Intro line about analog horror.\n0:00 Start\n0:30 Mid\n1:20 End\n#horror #analog #shorts"
                             if healthy else ""))
    return vids


def test_outlier_flags_mega():
    vids = _channel(1)
    vids.append(VideoRec(id="viral", title="x", views=2_000_000, age_days=30))
    assert outlier_multiplier(vids[-1], vids)["label"] == "mega_outlier"


def test_channel_healthy_beats_neglected():
    good = score_channel(20_000, _channel(1, True))
    poor = score_channel(20_000, _channel(2, False))
    assert good["score"] > poor["score"]
    assert 0 <= poor["score"] <= 100 and poor["top_issues"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
    import json
    print(json.dumps(score_title("Nobody Was Supposed To Find TAPE 047", primary_kw="analog horror",
                                 keyword_cluster={"analog horror": 85}), indent=2))
    print(json.dumps(score_channel(20_000, _channel(2, False)), indent=2))
