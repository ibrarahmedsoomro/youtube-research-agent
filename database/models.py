"""
SQLAlchemy ORM Models for AI YouTube Manager (Tier 1 & 2 - Data & Decision Layers).
Includes Temporal Provenance, Video Snapshots, Transcript Intelligence,
Topic Clusters, Question Opportunity Graph, Evidence Ledger, and Legacy Compatibility.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, default="Creator")
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(100), unique=True, nullable=True)
    handle = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    subscriber_count = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    thumbnail_url = Column(String(500), nullable=True)
    is_connected = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    metrics = relationship("ChannelMetrics", back_populates="channel", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="channel", cascade="all, delete-orphan")


class ChannelMetrics(Base):
    __tablename__ = "channel_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    health_score = Column(Float, default=0.0)
    seo_score = Column(Float, default=0.0)
    content_score = Column(Float, default=0.0)
    thumbnail_score = Column(Float, default=0.0)
    retention_score = Column(Float, default=0.0)
    growth_score = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    channel = relationship("Channel", back_populates="metrics")


class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)
    video_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)
    duration_seconds = Column(Integer, default=0)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    upload_date = Column(String(50), nullable=True)
    is_short = Column(Boolean, default=False)
    tags_json = Column(Text, default="[]")
    description = Column(Text, default="")
    thumbnail_url = Column(String(500), nullable=True)
    
    # Temporal & Provenance Fields
    published_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data_age_hours = Column(Float, default=0.0)
    
    # Computed Telemetry
    vph = Column(Float, default=0.0)
    age_cohort = Column(String(50), default="0-6h")
    age_adjusted_outlier = Column(Float, default=1.0)
    outlier_tier = Column(String(50), default="NORMAL")
    confidence = Column(String(20), default="MEDIUM")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    channel = relationship("Channel", back_populates="videos")
    snapshots = relationship("VideoSnapshot", back_populates="video", cascade="all, delete-orphan")


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(50), ForeignKey("videos.video_id"), nullable=False, index=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    vph = Column(Float, default=0.0)
    outlier_score = Column(Float, default=1.0)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    video = relationship("Video", back_populates="snapshots")


class TranscriptData(Base):
    __tablename__ = "transcripts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(50), unique=True, nullable=False, index=True)
    full_text = Column(Text, default="")
    language = Column(String(20), default="en")
    
    # Structured Narrative Breakdown
    hook_text = Column(Text, default="")
    hook_type = Column(String(100), default="Standard")
    hook_duration_seconds = Column(Float, default=0.0)
    core_promise = Column(Text, default="")
    pattern_interrupts_count = Column(Integer, default=0)
    open_loops_json = Column(Text, default="[]")
    key_claims_json = Column(Text, default="[]")
    payoff_text = Column(Text, default="")
    cta_text = Column(Text, default="")
    
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TopicCluster(Base):
    __tablename__ = "topic_clusters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(String(100), unique=True, nullable=False, index=True)
    cluster_name = Column(String(255), nullable=False)
    keywords_json = Column(Text, default="[]")
    video_count = Column(Integer, default=0)
    competitor_count = Column(Integer, default=0)
    avg_views = Column(Float, default=0.0)
    median_views = Column(Float, default=0.0)
    outlier_count = Column(Integer, default=0)
    dominant_creators_json = Column(Text, default="[]")
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class QuestionOpportunity(Base):
    __tablename__ = "question_opportunities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_text = Column(Text, nullable=False)
    cluster_id = Column(String(100), nullable=True, index=True)
    frequency_count = Column(Integer, default=1)
    answered_ratio = Column(Float, default=0.0)
    content_coverage = Column(String(20), default="LOW")
    opportunity_strength = Column(Float, default=0.0)
    first_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    niche = Column(String(100), nullable=True)
    content_type = Column(String(50), default="Long-form")
    demand_score = Column(Float, default=0.0)
    competition_score = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)
    search_score = Column(Float, default=0.0)
    audience_fit = Column(Float, default=0.0)
    originality = Column(Float, default=0.0)
    ctr_potential = Column(Float, default=0.0)
    production_cost = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)
    tier = Column(String(50), default="Average")
    confidence = Column(String(20), default="MEDIUM")
    status = Column(String(50), default="Discovered")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    evidences = relationship("OpportunityEvidence", back_populates="topic", cascade="all, delete-orphan")


class OpportunityEvidence(Base):
    __tablename__ = "opportunity_evidence"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    claim_text = Column(Text, nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(100), nullable=False)
    source_video_id = Column(String(50), nullable=True)
    source_channel = Column(String(255), nullable=True)
    observed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    topic = relationship("Topic", back_populates="evidences")


class ResearchRun(Base):
    __tablename__ = "research_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), unique=True, nullable=False, index=True)
    query = Column(String(255), nullable=False)
    target_channel = Column(String(100), nullable=True)
    collected_videos_count = Column(Integer, default=0)
    outliers_detected_count = Column(Integer, default=0)
    clusters_count = Column(Integer, default=0)
    opportunities_count = Column(Integer, default=0)
    status = Column(String(50), default="RUNNING")
    summary_report = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class HumanReview(Base):
    __tablename__ = "human_reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gate_name = Column(String(50), nullable=False)
    target_id = Column(String(100), nullable=False)
    decision = Column(String(50), nullable=False)
    reviewer_notes = Column(Text, default="")
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(255), nullable=False, index=True)
    search_volume = Column(Float, default=0.0)
    competition = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Audit(Base):
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_type = Column(String(50), default="channel")
    target_identifier = Column(String(255), nullable=False)
    overall_score = Column(Float, default=0.0)
    report_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Script(Base):
    __tablename__ = "scripts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Scene(Base):
    __tablename__ = "scenes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    script_id = Column(Integer, nullable=True)
    scene_number = Column(Integer, default=1)
    visual_description = Column(Text, default="")
    audio_dialogue = Column(Text, default="")


class ThumbnailConcept(Base):
    __tablename__ = "thumbnail_concepts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    concept_description = Column(Text, default="")


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, default="")
    format = Column(String(50), default="Shorts")
    status = Column(String(50), default="WAITING_APPROVAL")
    prepublish_score = Column(Float, default=90.0)
    policy_risk = Column(String(50), default="LOW")
    copyright_risk = Column(String(50), default="LOW")
    notes = Column(Text, default="")
    reviewer = Column(String(100), default="Human Gatekeeper")
    item_type = Column(String(50), default="package")
    item_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ContentCalendarItem(Base):
    __tablename__ = "content_calendar_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    scheduled_date = Column(String(50), nullable=False, default="")
    scheduled_for = Column(String(50), nullable=True, default="")
    format = Column(String(50), default="Shorts")
    status = Column(String(50), default="PLANNED")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        if "scheduled_date" in kwargs and "scheduled_for" not in kwargs:
            kwargs["scheduled_for"] = kwargs["scheduled_date"]
        elif "scheduled_for" in kwargs and "scheduled_date" not in kwargs:
            kwargs["scheduled_date"] = kwargs["scheduled_for"]
        super().__init__(**kwargs)


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), default="General")
    recommendation = Column(Text, default="")
    confidence = Column(String(50), default="HIGH")


class SeriesLore(Base):
    __tablename__ = "series_lore"
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_name = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=False)
    lore_bible = Column(Text, nullable=False)
    characters_json = Column(Text, default="[]")
    locations_json = Column(Text, default="[]")
    visual_style = Column(Text, default="")
    rules_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    status = Column(String(50), default="SUCCESS")
    details = Column(Text, default="")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ContentPackage(Base):
    __tablename__ = "content_packages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, nullable=True)
    title = Column(String(500), nullable=False)
    format = Column(String(50), default="Long-form")
    hook = Column(Text, default="")
    script = Column(Text, default="")
    storyboard_json = Column(Text, default="[]")
    thumbnail_concept = Column(Text, default="")
    seo_tags_json = Column(Text, default="[]")
    description = Column(Text, default="")
    status = Column(String(50), default="Draft")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CalendarEntry(Base):
    __tablename__ = "calendar_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(Integer, nullable=True)
    title = Column(String(500), nullable=False)
    scheduled_date = Column(String(50), nullable=False)
    status = Column(String(50), default="Scheduled")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChannelAudit(Base):
    __tablename__ = "channel_audits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_handle = Column(String(100), nullable=False, index=True)
    channel_title = Column(String(255), nullable=True)
    overall_health = Column(String(50), default="GOOD")
    subscriber_count = Column(Integer, default=0)
    median_views_30d = Column(Float, default=0.0)
    upload_consistency_days = Column(Float, default=0.0)
    top_performing_format = Column(String(100), default="Long-form")
    bottlenecks_json = Column(Text, default="[]")
    strengths_json = Column(Text, default="[]")
    recommendations_json = Column(Text, default="[]")
    audit_data_json = Column(Text, default="{}")
    audited_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VideoAudit(Base):
    __tablename__ = "video_audits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(50), nullable=False, index=True)
    video_title = Column(String(500), nullable=False)
    channel_handle = Column(String(100), nullable=True)
    views = Column(Integer, default=0)
    vph = Column(Float, default=0.0)
    age_cohort = Column(String(50), default="0-6h")
    performance_tier = Column(String(50), default="NORMAL")
    title_score_json = Column(Text, default="{}")
    thumbnail_score_json = Column(Text, default="{}")
    seo_score_json = Column(Text, default="{}")
    retention_risk_factors_json = Column(Text, default="[]")
    actionable_fixes_json = Column(Text, default="[]")
    audited_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TitleAnalysis(Base):
    __tablename__ = "title_analyses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    char_length = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    clarity_score = Column(Float, default=0.0)
    curiosity_score = Column(Float, default=0.0)
    power_words_json = Column(Text, default="[]")
    emotional_archetype = Column(String(100), default="Informative")
    mobile_cutoff_risk = Column(Boolean, default=False)
    recommendation = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TitleSuggestion(Base):
    __tablename__ = "title_suggestions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_topic_or_title = Column(String(500), nullable=False)
    suggested_title = Column(String(500), nullable=False)
    archetype = Column(String(100), default="Curiosity Gap")
    estimated_ctr_tier = Column(String(50), default="HIGH")
    rationale = Column(Text, default="")
    provenance_evidence = Column(Text, default="")
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ThumbnailAnalysis(Base):
    __tablename__ = "thumbnail_analyses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    thumbnail_url_or_path = Column(String(500), nullable=False)
    focal_point = Column(String(100), default="Center")
    text_readability = Column(String(50), default="HIGH")
    visual_clutter_level = Column(String(50), default="LOW")
    contrast_rating = Column(String(50), default="GOOD")
    detected_emotions_json = Column(Text, default="[]")
    mobile_preview_pass = Column(Boolean, default=True)
    recommendations_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DescriptionAnalysis(Base):
    __tablename__ = "description_analyses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(50), nullable=True)
    above_the_fold_hook = Column(Text, default="")
    has_timestamps = Column(Boolean, default=False)
    has_social_links = Column(Boolean, default=False)
    has_cta = Column(Boolean, default=False)
    keyword_density_json = Column(Text, default="{}")
    semantic_entities_json = Column(Text, default="[]")
    recommendations_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class KeywordAnalysis(Base):
    __tablename__ = "keyword_analyses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(255), nullable=False, index=True)
    search_volume_tier = Column(String(50), default="MEDIUM")
    competition_tier = Column(String(50), default="LOW")
    relevance_score = Column(Float, default=0.0)
    intent_category = Column(String(100), default="Informational")
    source_query = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(50), nullable=False, index=True)
    channel_handle = Column(String(100), nullable=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    vph = Column(Float, default=0.0)
    observed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class LearningSignal(Base):
    __tablename__ = "learning_signals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_handle = Column(String(100), nullable=False, index=True)
    signal_type = Column(String(100), nullable=False) # e.g. "top_title_archetype", "retention_hook_pattern"
    pattern_summary = Column(Text, nullable=False)
    supporting_video_ids_json = Column(Text, default="[]")
    confidence = Column(String(20), default="HIGH")
    sample_size = Column(Integer, default=1)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    engine_name = Column(String(100), nullable=False)
    version_tag = Column(String(50), nullable=False)
    parameters_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DataQualityLog(Base):
    __tablename__ = "data_quality_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), nullable=True, index=True)
    dataset_name = Column(String(100), nullable=False)
    total_records = Column(Integer, default=0)
    duplicate_records = Column(Integer, default=0)
    missing_views = Column(Integer, default=0)
    missing_transcripts = Column(Integer, default=0)
    missing_comments = Column(Integer, default=0)
    stale_records = Column(Integer, default=0)
    quality_status = Column(String(50), default="PASSED") # PASSED, WARNING, FAILED
    notes = Column(Text, default="")
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_handle = Column(String(100), default="default", index=True)
    role = Column(String(20), nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="chat") # 'chat', 'seo_package', 'script'
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DailyMemory(Base):
    __tablename__ = "daily_memories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_handle = Column(String(100), default="default", index=True)
    memory_date = Column(String(20), nullable=False, index=True) # YYYY-MM-DD
    summary_text = Column(Text, nullable=False)
    key_topics_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(100), unique=True, nullable=False, index=True)
    channel_handle = Column(String(100), nullable=False, index=True)
    channel_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    subscriber_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    credentials_json = Column(Text, nullable=True) # JSON stored OAuth token
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))



