"""
Verification script for Module 4 & 5:
- Verifies Competitor Multi-Channel Tracker
- Verifies Streamlit app.py syntax & dependencies
"""

import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from competitors import CompetitorTracker


def main():
    print("=" * 75)
    print("      TESTING MODULE 4: COMPETITOR MULTI-CHANNEL TRACKER")
    print("=" * 75)

    tracker = CompetitorTracker()
    test_channels = ["@freecodecamp"]
    print(f"\n[Step 1] Tracking channels: {test_channels} (depth: 5 videos each)...")
    report = tracker.track_multiple_channels(test_channels, max_videos_per_channel=5)

    print(f"  Total channels monitored: {report['total_channels']}")
    print(f"  Total videos analyzed:    {report['total_videos_analyzed']}")
    print(f"  Breakouts found:          {report['total_breakouts_found']}")
    
    for ch in report["channels"]:
        print(f"  Channel: {ch['channel']} | Median Baseline: {ch['median_views']:,} views")

    print("\n  Top Ranked Outlier Videos:")
    for i, v in enumerate(report["top_outliers"][:4], 1):
        print(f"  {i}. [{v['badge']}] ({v['outlier_multiplier']}x) {v['views']:,} views -> {v['title'][:55]}...")

    if report["trending_themes"]:
        print("\n  Trending breakout keywords:")
        for th in report["trending_themes"]:
            print(f"     - {th['keyword']} ({th['frequency']}x)")

    # Test App Compilation
    print("\n[Step 2] Verifying app.py syntax and imports...")
    import app
    print("  app.py imported successfully with zero errors!")

    print("\n" + "=" * 75)
    print("MODULES 4 & 5 VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
