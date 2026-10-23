"""
Database initialization and session management for AI YouTube Manager.
Uses SQLite for zero-configuration, robust local persistence with auto-migration.
"""

import os
import json
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .models import (
    Base,
    User,
    Channel,
    ChannelMetrics,
    Video,
    VideoSnapshot,
    TranscriptData,
    TopicCluster,
    QuestionOpportunity,
    Topic,
    OpportunityEvidence,
    ResearchRun,
    HumanReview,
    SeriesLore,
    SystemLog,
    ContentPackage,
    CalendarEntry,
    ChannelAudit,
    VideoAudit,
    TitleAnalysis,
    TitleSuggestion,
    ThumbnailAnalysis,
    DescriptionAnalysis,
    KeywordAnalysis,
    PerformanceSnapshot,
    LearningSignal,
    ModelVersion,
    DataQualityLog,
    ChatMessage,
    DailyMemory,
    ConnectedAccount,
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_manager.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes database schema, runs lightweight migrations, and seeds defaults."""
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate missing columns for existing SQLite DB
    try:
        with engine.connect() as conn:
            # Check existing columns in videos
            res = conn.execute(text("PRAGMA table_info(videos)")).fetchall()
            existing_cols = [r[1] for r in res]
            
            new_cols = [
                ("published_at", "DATETIME"),
                ("scraped_at", "DATETIME"),
                ("data_age_hours", "FLOAT DEFAULT 0.0"),
                ("vph", "FLOAT DEFAULT 0.0"),
                ("age_cohort", "VARCHAR(50) DEFAULT '0-6h'"),
                ("age_adjusted_outlier", "FLOAT DEFAULT 1.0"),
                ("outlier_tier", "VARCHAR(50) DEFAULT 'NORMAL'"),
                ("confidence", "VARCHAR(20) DEFAULT 'MEDIUM'"),
            ]
            for col_name, col_type in new_cols:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE videos ADD COLUMN {col_name} {col_type}"))
            
            # Check existing columns in channels
            ch_res = conn.execute(text("PRAGMA table_info(channels)")).fetchall()
            ch_existing = [r[1] for r in ch_res]
            if "scraped_at" not in ch_existing:
                conn.execute(text("ALTER TABLE channels ADD COLUMN scraped_at DATETIME"))

            # Check existing columns in topics
            t_res = conn.execute(text("PRAGMA table_info(topics)")).fetchall()
            t_existing = [r[1] for r in t_res]
            if "confidence" not in t_existing:
                conn.execute(text("ALTER TABLE topics ADD COLUMN confidence VARCHAR(20) DEFAULT 'MEDIUM'"))
            if "status" not in t_existing:
                conn.execute(text("ALTER TABLE topics ADD COLUMN status VARCHAR(50) DEFAULT 'Discovered'"))

            # Check existing columns in approvals
            app_res = conn.execute(text("PRAGMA table_info(approvals)")).fetchall()
            app_existing = [r[1] for r in app_res]
            app_new_cols = [
                ("title", "VARCHAR(500) DEFAULT ''"),
                ("format", "VARCHAR(50) DEFAULT 'Shorts'"),
                ("prepublish_score", "FLOAT DEFAULT 90.0"),
                ("policy_risk", "VARCHAR(50) DEFAULT 'LOW'"),
                ("copyright_risk", "VARCHAR(50) DEFAULT 'LOW'"),
                ("notes", "TEXT DEFAULT ''"),
                ("reviewer", "VARCHAR(100) DEFAULT 'Human Gatekeeper'"),
                ("item_type", "VARCHAR(50) DEFAULT 'package'"),
                ("item_id", "INTEGER"),
                ("created_at", "DATETIME"),
                ("updated_at", "DATETIME"),
            ]
            for col_name, col_type in app_new_cols:
                if col_name not in app_existing:
                    conn.execute(text(f"ALTER TABLE approvals ADD COLUMN {col_name} {col_type}"))
            
            # Check existing columns in content_calendar_items
            cal_res = conn.execute(text("PRAGMA table_info(content_calendar_items)")).fetchall()
            cal_existing = [r[1] for r in cal_res]
            cal_new_cols = [
                ("scheduled_date", "VARCHAR(50) DEFAULT ''"),
                ("format", "VARCHAR(50) DEFAULT 'Shorts'"),
                ("notes", "TEXT DEFAULT ''"),
                ("created_at", "DATETIME"),
            ]
            for col_name, col_type in cal_new_cols:
                if col_name not in cal_existing:
                    conn.execute(text(f"ALTER TABLE content_calendar_items ADD COLUMN {col_name} {col_type}"))

            conn.commit()
    except Exception as e:
        print(f"[DB] Migration Notice: {e}")

    # Seed default user and demo horror series lore
    db = SessionLocal()
    try:
        if not db.query(User).first():
            user = User(username="Creator", email="creator@youtube.local")
            db.add(user)

        if not db.query(SeriesLore).first():
            lore = SeriesLore(
                series_name="The Forgotten Broadcasts (Analog Horror)",
                genre="Analog Horror / Creepy VHS",
                lore_bible=(
                    "In October 1997, a small town's local broadcast station started emitting unauthorized "
                    "emergency alerts late at night. The broadcasts claimed that shadows were taking over residents' houses. "
                    "Visuals feature authentic VHS artifacts, scanlines, distorted audio frequencies, and disturbing public warnings."
                ),
                characters_json='["Officer Dan - Night Patrol", "Dr. Clara Reed - Radio Operator", "The Static Entity"]',
                locations_json='["Echo Peak Broadcast Tower", "Abandoned Oak School", "Highway 40 Mile Marker 12"]',
                visual_style="Grainy VHS 1997 cassette tape, glitching NTSC color bleed, ominous amber warning screens",
                rules_json='["Never reveal the entity in full light", "Broadcasts must always open with the Emergency Alert Sound", "Episodes end on an unresolved cliffhanger audio cue"]',
            )
            db.add(lore)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[DB] Seed Notice: {e}")
    finally:
        db.close()


@contextmanager
def get_db():
    """Context manager for transactional database operations."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def log_system_event(agent_name: str, action: str, status: str = "SUCCESS", details: str = ""):
    """Helper to log system operations for auditability."""
    try:
        with get_db() as db:
            log_entry = SystemLog(
                agent_name=agent_name,
                action=action,
                status=status,
                details=str(details)[:1000],
            )
            db.add(log_entry)
    except Exception:
        pass


def save_chat_message(channel_handle: str, role: str, content: str, message_type: str = "chat", metadata: dict = None) -> bool:
    """Persists a chat message to the database for daily conversational memory."""
    try:
        with get_db() as db:
            msg = ChatMessage(
                channel_handle=channel_handle,
                role=role,
                content=content,
                message_type=message_type,
                metadata_json=json.dumps(metadata or {})
            )
            db.add(msg)
        return True
    except Exception as e:
        print(f"[DB] Error saving chat message: {e}")
        return False


def get_chat_history(channel_handle: str, limit: int = 50) -> list:
    """Fetches ordered historical conversation messages for a channel."""
    try:
        with get_db() as db:
            messages = (
                db.query(ChatMessage)
                .filter(ChatMessage.channel_handle == channel_handle)
                .order_by(ChatMessage.created_at.asc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "message_type": m.message_type,
                    "metadata": json.loads(m.metadata_json or "{}"),
                    "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else ""
                }
                for m in messages
            ]
    except Exception as e:
        print(f"[DB] Error getting chat history: {e}")
        return []


def clear_chat_history(channel_handle: str) -> bool:
    """Clears conversation messages for a fresh session while keeping daily summaries."""
    try:
        with get_db() as db:
            db.query(ChatMessage).filter(ChatMessage.channel_handle == channel_handle).delete()
        return True
    except Exception as e:
        print(f"[DB] Error clearing chat history: {e}")
        return False


def save_daily_memory(channel_handle: str, summary_text: str, key_topics: list = None) -> bool:
    """Saves daily summarized topic memory."""
    from datetime import date
    try:
        today_str = date.today().isoformat()
        with get_db() as db:
            mem = DailyMemory(
                channel_handle=channel_handle,
                memory_date=today_str,
                summary_text=summary_text,
                key_topics_json=json.dumps(key_topics or [])
            )
            db.add(mem)
        return True
    except Exception as e:
        print(f"[DB] Error saving daily memory: {e}")
        return False


def get_daily_memories(channel_handle: str, limit: int = 10) -> list:
    """Fetches chronological daily memory summaries."""
    try:
        with get_db() as db:
            memories = (
                db.query(DailyMemory)
                .filter(DailyMemory.channel_handle == channel_handle)
                .order_by(DailyMemory.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "date": m.memory_date,
                    "summary": m.summary_text,
                    "topics": json.loads(m.key_topics_json or "[]")
                }
                for m in memories
            ]
    except Exception as e:
        print(f"[DB] Error getting daily memories: {e}")
        return []


def save_or_update_connected_account(
    channel_id: str,
    channel_handle: str,
    channel_name: str,
    email: str = "",
    avatar_url: str = "",
    subscriber_count: int = 0,
    video_count: int = 0,
    credentials_data: dict = None,
    set_active: bool = True,
) -> ConnectedAccount:
    """Saves or updates a connected YouTube channel account in the database."""
    with get_db() as db:
        acc = db.query(ConnectedAccount).filter(ConnectedAccount.channel_id == channel_id).first()
        if not acc:
            acc = db.query(ConnectedAccount).filter(ConnectedAccount.channel_handle == channel_handle).first()

        creds_str = json.dumps(credentials_data) if credentials_data else None

        if set_active:
            # Mark all others as inactive
            db.query(ConnectedAccount).update({ConnectedAccount.is_active: False})

        if acc:
            acc.channel_name = channel_name or acc.channel_name
            acc.channel_handle = channel_handle or acc.channel_handle
            acc.email = email or acc.email
            acc.avatar_url = avatar_url or acc.avatar_url
            if subscriber_count:
                acc.subscriber_count = subscriber_count
            if video_count:
                acc.video_count = video_count
            if creds_str:
                acc.credentials_json = creds_str
            acc.is_active = set_active
        else:
            acc = ConnectedAccount(
                channel_id=channel_id,
                channel_handle=channel_handle,
                channel_name=channel_name,
                email=email,
                avatar_url=avatar_url,
                subscriber_count=subscriber_count,
                video_count=video_count,
                credentials_json=creds_str,
                is_active=set_active,
            )
            db.add(acc)
        return acc


def get_connected_accounts() -> list:
    """Returns all connected YouTube accounts."""
    try:
        with get_db() as db:
            accounts = db.query(ConnectedAccount).order_by(ConnectedAccount.created_at.desc()).all()
            return [
                {
                    "id": a.id,
                    "channel_id": a.channel_id,
                    "channel_handle": a.channel_handle,
                    "channel_name": a.channel_name,
                    "email": a.email,
                    "avatar_url": a.avatar_url,
                    "subscriber_count": a.subscriber_count,
                    "video_count": a.video_count,
                    "is_active": a.is_active,
                    "has_credentials": bool(a.credentials_json),
                }
                for a in accounts
            ]
    except Exception as e:
        print(f"[DB] Error listing connected accounts: {e}")
        return []


def get_active_account() -> dict:
    """Returns the currently active connected YouTube account."""
    try:
        with get_db() as db:
            acc = db.query(ConnectedAccount).filter(ConnectedAccount.is_active == True).first()
            if not acc:
                acc = db.query(ConnectedAccount).first()
            if acc:
                return {
                    "id": acc.id,
                    "channel_id": acc.channel_id,
                    "channel_handle": acc.channel_handle,
                    "channel_name": acc.channel_name,
                    "email": acc.email,
                    "avatar_url": acc.avatar_url,
                    "subscriber_count": acc.subscriber_count,
                    "video_count": acc.video_count,
                    "is_active": acc.is_active,
                    "credentials_json": acc.credentials_json,
                }
            return None
    except Exception as e:
        print(f"[DB] Error getting active account: {e}")
        return None


def set_active_account(channel_identifier: str) -> bool:
    """Switches active channel by channel_id or channel_handle."""
    try:
        with get_db() as db:
            db.query(ConnectedAccount).update({ConnectedAccount.is_active: False})
            acc = (
                db.query(ConnectedAccount)
                .filter(
                    (ConnectedAccount.channel_id == channel_identifier)
                    | (ConnectedAccount.channel_handle == channel_identifier)
                )
                .first()
            )
            if acc:
                acc.is_active = True
                return True
            return False
    except Exception as e:
        print(f"[DB] Error switching active account: {e}")
        return False


def delete_connected_account(channel_identifier: str) -> bool:
    """Removes a connected channel account."""
    try:
        with get_db() as db:
            db.query(ConnectedAccount).filter(
                (ConnectedAccount.channel_id == channel_identifier)
                | (ConnectedAccount.channel_handle == channel_identifier)
            ).delete()
            # If any remaining, make first one active
            remaining = db.query(ConnectedAccount).first()
            if remaining:
                remaining.is_active = True
            return True
    except Exception as e:
        print(f"[DB] Error deleting account: {e}")
        return False


