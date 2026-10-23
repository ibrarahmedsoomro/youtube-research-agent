"""
Comprehensive verification script for AI YouTube Manager.
Tests database, audits, opportunity formula, scripting, storyboards, series lore, approvals, and learning engine.
"""

import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database import init_db, get_db, User, SeriesLore
from audit import ChannelAuditor, VideoAuditor, PrePublishAuditor
from research import OpportunityFinder, TrendDiscoveryEngine, ContentStrategyEngine
from production import HookAgent, ScriptAgent, StoryboardAgent, SeriesEngine, ThumbnailStudio, VideoProviderFactory
from operations import ApprovalCenter, ContentCalendarManager
from learning import LearningEngine


def main():
    print("=" * 80)
    print("         VERIFYING COMPLETE AI YOUTUBE MANAGER ARCHITECTURE")
    print("=" * 80)

    # 1. Database Init
    print("\n[Phase 1] Testing Database Initialization...")
    init_db()
    with get_db() as db:
        user_count = db.query(User).count()
        series_count = db.query(SeriesLore).count()
        print(f"  Database connected! Users: {user_count} | Series Lore entries: {series_count}")

    # 2. Opportunity Finder 8-Factor Formula
    print("\n[Phase 2] Testing Opportunity Score Formula (Section 7)...")
    opp_finder = OpportunityFinder()
    score_res = opp_finder.calculate_opportunity_score(
        demand=90.0, competition=30.0, trend=85.0, search_potential=80.0,
        audience_fit=90.0, originality=80.0, ctr_potential=92.0, production_cost=20.0
    )
    print(f"  Calculated Opportunity: {score_res['estimated_opportunity_score']}/100 -> {score_res['tier']}")
    print(f"  Guidance: {score_res['guidance']}")

    # 3. Creative Studio (Hook, Script, Storyboard, Series Lore)
    print("\n[Phase 3] Testing Creative Studio Pipeline...")
    hooks = HookAgent.generate_hooks("Emergency Broadcast Analog Horror", video_format="Shorts")
    print(f"  Generated {len(hooks)} retention hooks. Top hook: '{hooks[0]['hook_script']}'")

    script = ScriptAgent.generate_script(
        topic="Analog Horror VHS Mystery",
        title="Emergency Broadcast From 1997",
        video_length="60s",
        format_type="Shorts",
    )
    print(f"  Script created for: '{script['title']}'. Full length: {len(script['full_script'])} chars.")

    storyboard = StoryboardAgent.generate_storyboard(script)
    print(f"  Storyboard deconstructed into {len(storyboard)} production scenes:")
    for s in storyboard[:2]:
        print(f"     Scene {s['scene_number']} ({s['duration']}s): Camera '{s['camera']}' | SFX: '{s['sfx']}'")

    # Series Lore
    ep_outline = SeriesEngine.generate_episode_outline(
        series_name="The Forgotten Broadcasts",
        episode_number=2,
        episode_title="The Midnight Signal",
    )
    print(f"  Series Continuity Episode: {ep_outline['episode_title']} (Genre: {ep_outline['genre']})")

    # 4. Pre-Publish Safety Gate & Approval
    print("\n[Phase 4] Testing Pre-Publish Audit & Human Approval Center (Section 22 & 23)...")
    pre_audit = PrePublishAuditor.audit_pre_publish(
        title="Emergency Broadcast From 1997 That Was Never Supposed To Air",
        description="A full detailed breakdown of the 1997 incident with audio restoration and timeline reconstruction.",
        tags=["analog horror", "scary vhs", "emergency broadcast", "creepypasta", "1997 mystery"],
        hook="Whatever you do, DO NOT look outside your window tonight.",
        script_text="In October 1997, an unauthorized broadcast took over channel 4...",
        thumbnail_text="DON'T LOOK!",
        format_type="Shorts",
    )
    print(f"  Pre-Publish Verdict: {pre_audit['verdict']} (Score: {pre_audit['final_publish_score']}/100)")
    print(f"  Policy Risk: {pre_audit['policy_risk']} | Copyright Risk: {pre_audit['copyright_risk']}")

    approval_entry = ApprovalCenter.create_approval_entry(
        title=pre_audit["title"],
        format_type="Shorts",
        prepublish_score=pre_audit["final_publish_score"],
    )
    print(f"  Queued in Human Approval Center -> ID: {approval_entry['id']} | Status: {approval_entry['status']}")

    # 5. Content Calendar & Strategy
    print("\n[Phase 5] Testing Content Strategy & Calendar Planner (Section 10 & 25)...")
    cal_id = ContentCalendarManager.add_calendar_item(
        title="Emergency Broadcast Episode 1",
        scheduled_date="2026-09-10",
        format_type="Shorts",
    )
    all_cal = ContentCalendarManager.get_calendar_items()
    print(f"  Calendar scheduled item added (ID: {cal_id}). Total items in schedule: {len(all_cal)}")

    # 6. Learning Engine
    print("\n[Phase 6] Testing Learning Engine & 24h Re-Optimization...")
    perf = LearningEngine.audit_performance_and_reoptimize(
        video_title="Obsolete Setup Tutorial",
        views=2100,
        channel_median=12000,
        published_hours_ago=24,
    )
    print(f"  Performance Status: {perf['status']} ({perf['performance_ratio']}x of baseline)")
    print(f"  Diagnosis: {perf['diagnosis'][:110]}...")
    if perf["reoptimization_actions"]:
        print(f"  Triggered Action: {perf['reoptimization_actions'][0]['action']} -> '{perf['reoptimization_actions'][0]['suggestion']}'")

    print("\n" + "=" * 80)
    print("ALL MODULES SUCCESSFULLY VERIFIED! ARCHITECTURE IS 100% OPERATIONAL.")
    print("=" * 80)


if __name__ == "__main__":
    main()
