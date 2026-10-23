"""
Verification script for Module 2: VidIQ Metrics & Analytics Engine.
Tests VPH, Outlier Score, SEO Audit, and Keyword Opportunity Score.
"""

import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scraper import VideoScraper, ChannelScraper
from analytics import (
    calculate_video_age_hours,
    calculate_view_velocity,
    calculate_engagement_rate,
    calculate_channel_baseline,
    calculate_outlier_score,
    SEOScorer,
    KeywordAnalyzer,
)


def main():
    print("=" * 75)
    print("       TESTING MODULE 2: VIDIQ METRICS & ANALYTICS ENGINE")
    print("=" * 75)

    video_scraper = VideoScraper()

    # 1. Test Keyword Opportunity & Search Demand
    keyword = "LangGraph Tutorial"
    print(f"\n[Test 1] Analyzing Keyword Niche: '{keyword}'...")
    results = video_scraper.search_videos(query=keyword, max_results=4)
    print(f"  Retrieved {len(results)} search results.")

    niche_analysis = KeywordAnalyzer.analyze_keyword_niche(query=keyword, search_results=results)
    print(f"  📊 Search Demand Score: {niche_analysis['demand_score']}/100")
    print(f"  ⚔️ Competition Score:   {niche_analysis['competition_score']}/100")
    print(f"  🎯 Overall Opportunity: {niche_analysis['opportunity_score']}/100 -> {niche_analysis['verdict']}")
    print(f"  📈 Average Views:       {niche_analysis['avg_views']:,}")
    print(f"  ⚡ Average Velocity:    {niche_analysis['avg_vph']} VPH")
    print("  🏷️ Top Shared Tags across ranking videos:")
    for tag_info in niche_analysis["top_tags"][:5]:
        print(f"     - {tag_info['tag']} (Used in {tag_info['frequency']} videos / {tag_info['relevance_pct']}%)")

    # 2. Test Single Video VPH, Engagement & SEO Audit
    test_video = results[0] if results else None
    if test_video:
        print(f"\n[Test 2] Deep Metrics & SEO Audit for: '{test_video.title}'")
        
        # Velocity
        age = calculate_video_age_hours(upload_date=test_video.upload_date, timestamp=test_video.timestamp)
        velocity = calculate_view_velocity(test_video.views, age)
        print(f"  ⏱️ Video Age: {velocity['age_days']} days ({velocity['age_hours']} hours)")
        print(f"  ⚡ View Velocity: {velocity['vph']} Views Per Hour (VPH) | {velocity['views_per_day']:,} Views/Day")

        # Engagement
        engagement = calculate_engagement_rate(test_video.views, test_video.likes or 0, test_video.comment_count or 0)
        print(f"  💬 Engagement Rate: {engagement['raw_rate_percent']}% -> {engagement['grade']}")

        # SEO Audit
        seo_audit = SEOScorer.audit_video(test_video)
        print(f"  🎯 VidIQ SEO Score: {seo_audit['overall_seo_score']}/100 ({seo_audit['tier']})")
        print("  Checklist:")
        for check in seo_audit["checks"]:
            status_icon = "✅" if check["status"] == "PASS" else ("⚠️" if check["status"] == "WARN" else "❌")
            print(f"     {status_icon} {check['item']}: {check['detail']} (+{check['points']} pts)")

        if seo_audit["suggestions"]:
            print("  Optimization Suggestions:")
            for sug in seo_audit["suggestions"][:3]:
                print(f"     💡 {sug}")

    # 3. Test Channel Outlier Engine
    channel_handle = "@freecodecamp"
    print(f"\n[Test 3] Testing Outlier Engine on Channel '{channel_handle}'...")
    channel_scraper = ChannelScraper()
    channel_vids = channel_scraper.fetch_channel_videos(channel_handle, limit=6)
    
    if channel_vids:
        all_views = [cv.views for cv in channel_vids if cv.views and cv.views > 0]
        baseline = calculate_channel_baseline(all_views)
        print(f"  Channel Median Baseline: {baseline['median_views']:,} views (from {baseline['sample_size']} videos)")

        print("  Checking Outlier Multipliers:")
        for i, cv in enumerate(channel_vids, 1):
            outlier = calculate_outlier_score(cv.views or 0, baseline["median_views"])
            print(f"  {i}. [{outlier['badge']}] {cv.views:,} views ({outlier['outlier_multiplier']}x) -> {cv.title[:55]}...")

    print("\n" + "=" * 75)
    print("MODULE 2 TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
