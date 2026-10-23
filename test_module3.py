"""
Verification script for Module 3: AI Intelligence Core (Research & Strategy Agent).
Tests Viral Titles, Content Gap Finder, Thumbnail Blueprints, and SEO Package.
"""

import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scraper import VideoScraper, TranscriptScraper
from ai import YouTubeAIAgent


def main():
    print("=" * 75)
    print("         TESTING MODULE 3: AI RESEARCH & STRATEGY AGENT")
    print("=" * 75)

    topic = "Build AI Agents in Python"
    agent = YouTubeAIAgent()
    video_scraper = VideoScraper()

    # 1. Fetch real competitor data to ground the AI
    print(f"\n[Step 1] Fetching live competitor data for ground truth on '{topic}'...")
    competitors = video_scraper.search_videos(query=topic, max_results=3)
    comp_titles = [c.title for c in competitors]
    for i, t in enumerate(comp_titles, 1):
        print(f"  Competitor {i}: {t}")

    # 2. Test Viral Title Generation
    print(f"\n[Step 2] Generating High-CTR Viral Titles across 5 Psychological Angles...")
    titles_data = agent.generate_viral_titles(
        topic=topic,
        competitor_titles=comp_titles,
        niche_tags=["ai agent", "python", "automation", "llm", "tutorial"],
    )

    for i, item in enumerate(titles_data.get("titles", []), 1):
        print(f"  {i}. [{item['angle']}] {item['title']}")
        print(f"     Why it works: {item['why_it_works']}")
        print(f"     Predicted CTR: {item.get('predicted_ctr_tier', 'High')}")

    # 3. Test Content Gap Analysis
    print(f"\n[Step 3] Analyzing Content Gaps & Retention Hooks...")
    # Fetch real transcript snippet from the top video
    transcript_text = None
    if competitors:
        ts = TranscriptScraper()
        tr_data = ts.fetch_transcript(competitors[0].video_id)
        if tr_data:
            transcript_text = tr_data.full_text[:1500]
            print(f"  Loaded {len(transcript_text)} chars from competitor transcript.")

    gap_data = agent.find_content_gaps(
        topic=topic,
        competitor_titles=comp_titles,
        transcript_snippet=transcript_text,
    )

    print(f"  ❌ The Missing Link: {gap_data['missing_link']}")
    print("  ❓ Burning Questions Viewers Still Have:")
    for q in gap_data["burning_questions"]:
        print(f"     - {q}")
    print(f"  🚀 10x Unfair Advantage Angle: {gap_data['unfair_advantage_angle']}")
    print(f"  🎯 First 30s Hook Script:\n     \"{gap_data['first_30s_hook_script']}\"")

    # 4. Test Thumbnail Concepts
    print(f"\n[Step 4] Generating High-Contrast Thumbnail Concepts...")
    thumb_data = agent.generate_thumbnail_concepts(topic=topic, angle="High Contrast / Warning")
    for i, c in enumerate(thumb_data.get("concepts", []), 1):
        print(f"  Concept {i}: {c['concept_name']}")
        print(f"     Composition: {c['visual_composition']}")
        print(f"     Text Overlay: '{c['text_overlay']}'")
        print(f"     Color Palette: {c['color_palette']}")
        print(f"     Vibe: {c['emotion_or_vibe']}")

    # 5. Test Full SEO Pack
    chosen_title = titles_data.get("titles", [{}])[0].get("title", f"Build {topic}")
    print(f"\n[Step 5] Generating SEO Package for: '{chosen_title}'...")
    seo_pack = agent.generate_seo_pack(topic=topic, chosen_title=chosen_title)
    print(f"  Above The Fold Hook:\n     \"{seo_pack['above_the_fold_hook']}\"")
    print(f"  Timestamps ({len(seo_pack['chapter_timestamps'])} chapters):")
    for ch in seo_pack["chapter_timestamps"][:4]:
        print(f"     [{ch['time']}] {ch['title']}")
    print(f"  Tags ({len(seo_pack['recommended_tags'])} tags): {', '.join(seo_pack['recommended_tags'][:6])}...")
    print(f"  Hashtags: {' '.join(seo_pack['hashtags'])}")

    print("\n" + "=" * 75)
    print("MODULE 3 TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
