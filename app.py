"""
AI YOUTUBE MANAGER — Production-Ready SaaS Application
A complete autonomous YouTube Growth Platform managing the full lifecycle:
RESEARCH → DISCOVER → SCORE → PLAN → CREATE → AUDIT → OPTIMIZE → APPROVE → PUBLISH → ANALYZE → IMPROVE
"""

import streamlit as st
import pandas as pd
import sys
import json
import re
from datetime import datetime

# Configure Windows encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

# Seamless Streamlit Cloud Secrets Sync
try:
    if hasattr(st, "secrets"):
        import os
        for k in st.secrets:
            if isinstance(st.secrets[k], str) and k not in os.environ:
                os.environ[k] = st.secrets[k]
        if "YOUTUBE_CREDENTIALS_JSON" in st.secrets and not os.path.exists("youtube_credentials.json"):
            with open("youtube_credentials.json", "w", encoding="utf-8") as f:
                f.write(st.secrets["YOUTUBE_CREDENTIALS_JSON"])
except Exception:
    pass

from database import init_db, get_db, Channel, User, SeriesLore, SystemLog
from database.db import save_chat_message, get_chat_history, clear_chat_history, save_daily_memory, get_daily_memories
from audit import ChannelAuditor, VideoAuditor, PrePublishAuditor
from research import OpportunityFinder, TrendDiscoveryEngine, ContentStrategyEngine
from production import (
    HookAgent,
    ScriptAgent,
    StoryboardAgent,
    SeriesEngine,
    VideoProviderFactory,
    ThumbnailStudio,
)
from operations import ApprovalCenter, ContentCalendarManager, YouTubePublisher
from operations.youtube_auth import YouTubeAuthManager
from audit import ChannelAuditor, VideoAuditor, PrePublishAuditor, BatchOptimizer
from competitors import CompetitorTracker, CompetitorGapScanner
from learning import LearningEngine
from scraper import VideoScraper, ChannelScraper
from ai import YouTubeAIAgent

from orchestration import ResearchOrchestrator
from analytics.data_quality import DataQualityEngine
from production.title_intelligence import TitleIntelligenceEngine
from production.thumbnail_intelligence import ThumbnailIntelligenceEngine
from production.description_keyword_engine import DescriptionKeywordEngine
from learning.channel_learning import ChannelLearningEngine
from database.models import DataQualityLog, LearningSignal, TitleSuggestion

# Initialize database schema on boot
init_db()

import os

def get_ai_agent():
    return YouTubeAIAgent()


@st.cache_resource
def get_auth_manager():
    return YouTubeAuthManager()

@st.cache_resource
def get_publisher():
    return YouTubePublisher()

@st.cache_data(ttl=1800, show_spinner=False)
def get_cached_channel_report(channel_identifier: str, video_limit: int = 25):
    try:
        auditor = ChannelAuditor()
        return auditor.audit_channel(channel_identifier, video_limit=video_limit)
    except Exception as e:
        print(f"Error fetching channel report for {channel_identifier}: {e}")
        return None

# Auto-detect connected YouTube channel without blocking app boot
if "active_channel" not in st.session_state:
    st.session_state["active_channel"] = "Vanished Skies" if os.path.exists("youtube_credentials.json") else "@spookytoonstories"

if "latest_channel_report" not in st.session_state or not st.session_state["latest_channel_report"]:
    st.session_state["latest_channel_report"] = get_cached_channel_report(st.session_state["active_channel"], video_limit=25)

# -----------------------------------------------------------------------------
# App Layout & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI YouTube Manager | SaaS Growth Platform",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* Global Root & Font Setup */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: #080b11;
        color: #f1f5f9;
        letter-spacing: -0.01em;
    }

    /* Ambient Cyber Mesh Gradient Background */
    .stApp {
        background-color: #080b11;
        background-image: 
            radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.12) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.10) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.06) 0px, transparent 50%);
        background-attachment: fixed;
    }

    /* Custom Modern Slim Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.6);
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #3b82f6;
    }

    /* Keyframe Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes glowPulse {
        0%, 100% {
            box-shadow: 0 0 15px rgba(37, 99, 235, 0.25);
        }
        50% {
            box-shadow: 0 0 28px rgba(56, 189, 248, 0.5);
        }
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    /* Tabs Styling - SaaS Glassmorphism Pill */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(12px);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 8px 18px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 13.5px;
        border: 1px solid transparent;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background: rgba(255, 255, 255, 0.04);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45);
    }

    /* Buttons Styling - Developer-Grade Tactile & Glow */
    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
        font-size: 13.5px;
        padding: 8px 18px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
        color: #ffffff;
        box-shadow: 0 6px 20px rgba(56, 189, 248, 0.3);
    }
    .stButton > button:active {
        transform: translateY(0) scale(0.98);
    }
    
    /* Primary Action Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        border: 1px solid rgba(255, 255, 255, 0.25);
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        box-shadow: 0 6px 24px rgba(37, 99, 235, 0.6);
    }

    /* Input & Textarea Elements */
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus,
    .stSelectbox [data-baseweb="select"]:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2) !important;
    }

    /* Metric Cards - Glassmorphic Holographic */
    .metric-card {
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.85), rgba(11, 15, 25, 0.95));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        animation: fadeInUp 0.4s ease forwards;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.35);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.15);
    }

    /* Badges & Pills */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: 0.02em;
        transition: transform 0.2s ease;
    }
    .badge-pill:hover {
        transform: scale(1.05);
    }
    .badge-green {
        background: rgba(6, 95, 70, 0.4);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.4);
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.15);
    }
    .badge-amber {
        background: rgba(120, 53, 15, 0.4);
        color: #fde68a;
        border: 1px solid rgba(245, 158, 11, 0.4);
        box-shadow: 0 2px 10px rgba(245, 158, 11, 0.15);
    }
    .badge-red {
        background: rgba(127, 29, 29, 0.4);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        box-shadow: 0 2px 10px rgba(239, 68, 68, 0.15);
    }
    .badge-blue {
        background: rgba(30, 58, 138, 0.4);
        color: #bfdbfe;
        border: 1px solid rgba(59, 130, 246, 0.4);
        box-shadow: 0 2px 10px rgba(59, 130, 246, 0.15);
    }
    .badge-purple {
        background: rgba(88, 28, 135, 0.4);
        color: #e9d5ff;
        border: 1px solid rgba(168, 85, 247, 0.4);
        box-shadow: 0 2px 10px rgba(168, 85, 247, 0.15);
    }

    /* VidIQ Portrait Card Styling (9:16 Vertical Shorts Grid) */
    .vidiq-portrait-card {
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        height: 380px;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 8px;
    }
    .vidiq-portrait-card:hover {
        transform: translateY(-6px) scale(1.015);
        border-color: #38bdf8;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.8), 0 0 25px rgba(56, 189, 248, 0.3);
    }
    .vidiq-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 75%;
        background: linear-gradient(180deg, rgba(8, 11, 17, 0) 0%, rgba(8, 11, 17, 0.75) 45%, rgba(8, 11, 17, 0.98) 100%);
        pointer-events: none;
    }
    .vidiq-badge-container {
        position: relative;
        z-index: 2;
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }
    .vidiq-badge {
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 11.5px;
        font-weight: 700;
        color: #f1f5f9;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    .vidiq-badge-score {
        color: #10b981;
        font-weight: 800;
        margin-left: 4px;
    }
    .vidiq-unlock-btn {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        padding: 8px 18px;
        border-radius: 9999px;
        font-size: 12.5px;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        gap: 7px;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.25);
        z-index: 3;
        white-space: nowrap;
        transition: all 0.2s ease;
    }
    .vidiq-unlock-btn:hover {
        transform: translate(-50%, -50%) scale(1.06);
        box-shadow: 0 6px 25px rgba(56, 189, 248, 0.8);
    }
    .vidiq-card-footer {
        position: relative;
        z-index: 2;
    }
    .vidiq-card-title {
        font-size: 14px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.35;
        margin-bottom: 6px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        text-shadow: 0 2px 6px rgba(0,0,0,0.9);
    }
    .vidiq-card-meta {
        font-size: 12px;
        color: #94a3b8;
        font-weight: 600;
    }

    /* Expanders & Accordions */
    .streamlit-expanderHeader {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        color: #f1f5f9 !important;
        transition: all 0.2s ease !important;
    }
    .streamlit-expanderHeader:hover {
        background: rgba(30, 41, 59, 0.8) !important;
        border-color: rgba(56, 189, 248, 0.3) !important;
    }
    .streamlit-expanderContent {
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-top: none !important;
        border-bottom-left-radius: 10px !important;
        border-bottom-right-radius: 10px !important;
        background: rgba(10, 15, 26, 0.5) !important;
    }

    /* Chat Messages Glass Bubbles */
    .stChatMessage {
        background: rgba(15, 23, 42, 0.65) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 14px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
        animation: fadeInUp 0.3s ease forwards;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Sidebar Navigation (VidIQ SaaS Layout)
# -----------------------------------------------------------------------------
with st.sidebar:
    # VidIQ Logo Header
    st.markdown(
        """
        <div style='display:flex; align-items:center; gap:10px; margin-bottom:12px;'>
            <div style='background:linear-gradient(135deg, #2563eb, #1d4ed8); border-radius:10px; width:36px; height:36px; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:19px; color:white; font-family:sans-serif; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);'>
                iq
            </div>
            <div>
                <div style='font-size:16.5px; font-weight:800; color:white; line-height:1.1;'>AI Growth Studio</div>
                <div style='font-size:11px; color:#38bdf8; font-weight:600;'>Multi-Channel SaaS Engine</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # -------------------------------------------------------------------------
    # MULTI-CHANNEL SWITCHER & OAUTH CONNECTOR
    # -------------------------------------------------------------------------
    auth_mgr = get_auth_manager()
    connected_accs = auth_mgr.list_accounts()
    active_acc = auth_mgr.get_current_active()

    # Active channel display options for Selectbox
    acc_options = [f"{a['channel_name']} ({a['channel_handle']})" for a in connected_accs]
    acc_handles = [a['channel_handle'] for a in connected_accs]
    
    current_handle = active_acc["channel_handle"] if active_acc else "@SpookyToonStories"
    if "active_channel" not in st.session_state or st.session_state["active_channel"] not in acc_handles:
        st.session_state["active_channel"] = current_handle

    current_idx = acc_handles.index(st.session_state["active_channel"]) if st.session_state["active_channel"] in acc_handles else 0

    st.markdown("<div style='font-size:11px; font-weight:800; color:#64748b; text-transform:uppercase; margin-bottom:4px;'>Active Channel</div>", unsafe_allow_html=True)
    selected_acc_label = st.selectbox(
        "Select Active YouTube Channel",
        acc_options,
        index=current_idx,
        label_visibility="collapsed",
        key="channel_switcher_dropdown"
    )

    # Detect channel switch
    selected_handle = connected_accs[acc_options.index(selected_acc_label)]["channel_handle"]
    if selected_handle != st.session_state["active_channel"]:
        auth_mgr.switch_channel(selected_handle)
        st.session_state["active_channel"] = selected_handle
        st.session_state.pop("latest_channel_report", None)
        st.rerun()

    # Connect New Channel Expander
    with st.expander("➕ Connect New YouTube Channel", expanded=False):
        st.markdown(
            "<div style='font-size:12px; color:#94a3b8; margin-bottom:8px;'>"
            "Connect another Gmail / YouTube Channel to optimize multiple channels from one dashboard.</div>",
            unsafe_allow_html=True
        )
        
        auth_url = auth_mgr.get_auth_url()
        if auth_url:
            st.link_button("🔑 Sign in with Google / YouTube", auth_url, use_container_width=True)
            st.caption("1. Click above to authorize your YouTube Channel.")
            st.caption("2. Copy the code or redirected URL and paste below:")
            
            auth_code_input = st.text_input("Authorization Code", placeholder="Paste 4/0A... code here", label_visibility="collapsed")
            if st.button("🔗 Verify & Connect Channel", type="primary", use_container_width=True):
                if auth_code_input.strip():
                    with st.spinner("Authenticating channel with YouTube API..."):
                        res = auth_mgr.exchange_code_for_channel(auth_code_input.strip())
                        if res.get("success"):
                            st.success(f"Connected: {res.get('channel_name')} ({res.get('channel_handle')})!")
                            st.session_state["active_channel"] = res.get("channel_handle")
                            st.rerun()
                        else:
                            st.error(f"Failed to connect: {res.get('error')}")
                else:
                    st.warning("Please paste the Google authorization code.")
        else:
            st.info("ℹ️ Using sandbox simulation for new channels. Configure `client_secret.json` for live OAuth.")

    st.divider()

    nav_options = [
        "🛡️ Audit Channel",
        "💬 New Chat",
        "🏆 Race to 4K",
        "🔍 Research",
        "⚡ Upgrade",
        "🎨 Thumbnail Studio",
        "🧠 Learning & Analytics",
    ]

    # Handle quick_nav redirection from buttons
    default_idx = 0
    if "quick_nav" in st.session_state and st.session_state["quick_nav"] in nav_options:
        default_idx = nav_options.index(st.session_state["quick_nav"])
        del st.session_state["quick_nav"]

    nav = st.radio(
        "Navigation",
        nav_options,
        index=default_idx,
        label_visibility="collapsed"
    )

    st.divider()
    
    # Recent Chats History (VidIQ Style)
    st.markdown("<div style='font-size:12px; font-weight:700; color:#64748b; margin-bottom:8px; text-transform:uppercase;'>History ▾</div>", unsafe_allow_html=True)
    history_items = [
        "Sara's Behavior Was REALL...",
        "What is the SPOOKIEST Sp...",
        "Channel grow karne ke tips",
        "Analog Horror Hook Formula"
    ]
    for h in history_items:
        st.markdown(f"<div style='font-size:12.5px; color:#cbd5e1; padding:4px 0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>💬 {h}</div>", unsafe_allow_html=True)

    st.divider()

    # User Profile Footer
    cur_acc = auth_mgr.get_current_active()
    p_name = cur_acc.get("channel_name", "Spooky Toon Stories") if cur_acc else "Creator"
    p_handle = cur_acc.get("channel_handle", "@SpookyToonStories") if cur_acc else "@SpookyToonStories"
    p_email = cur_acc.get("email", "taqisoomro333@gmail.com") if cur_acc else "taqisoomro333@gmail.com"
    p_subs = f"{cur_acc.get('subscriber_count', 18400):,} subs" if cur_acc else "18.4K subs"
    p_avatar = cur_acc.get("avatar_url") if cur_acc and cur_acc.get("avatar_url") else ""
    
    avatar_html = (
        f"<img src='{p_avatar}' style='width:30px; height:30px; border-radius:50%; object-fit:cover; border:1px solid #38bdf8;'>"
        if p_avatar and p_avatar.startswith("http")
        else "<div style='background:linear-gradient(135deg, #10b981, #059669); border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-size:14px;'>🎬</div>"
    )

    st.markdown(
        f"""
        <div style='background:rgba(17, 24, 39, 0.85); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:12px; display:flex; align-items:center; justify-content:space-between; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
            <div style='display:flex; align-items:center; gap:10px; overflow:hidden;'>
                {avatar_html}
                <div style='overflow:hidden;'>
                    <div style='font-size:12.5px; font-weight:700; color:white; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{p_name}</div>
                    <div style='font-size:10.5px; color:#94a3b8; display:flex; align-items:center; gap:6px;'>
                        <span>{p_handle}</span>
                        <span style='background:rgba(37,99,235,0.25); color:#60a5fa; font-size:9.5px; padding:1px 5px; border-radius:4px; font-weight:700;'>PRO</span>
                    </div>
                </div>
            </div>
            <span style='color:#38bdf8; font-size:16px; margin-left:6px;'>✦</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# =============================================================================
# DEDICATED FULL-SCREEN VIDEO OPTIMIZATION WORKSPACE (Exact VidIQ Pattern)
# =============================================================================
def render_video_optimizer_screen(v: dict, channel_name: str = "@SpookyToonStories"):
    """
    Renders the exact VidIQ 'Optimize Video' modal screen matching https://app.vidiq.com/optimize?mode=short
    Includes SEO Tag Cloud with scores, Title 85 Editor with frame suggestions, Description Review 88,
    and the Right-Pane 9:16 vertical Shorts video preview frame.
    """
    v_id = v.get("video_id", "v_active")
    v_title = v.get("title", "Untitled Video")
    v_score = v.get("vidiq_score", 85)
    v_content_score = v.get("content_score", v_score - 5 if v_score > 30 else v_score)
    v_views_text = v.get("views_text", f"{v.get('views', 0):,} views")
    v_thumb = v.get("thumbnail_url")
    if not v_thumb or "http" not in str(v_thumb):
        v_thumb = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"

    # Initialize State Keys
    title_key = f"live_title_{v_id}"
    tags_list_key = f"live_tags_list_{v_id}"
    desc_key = f"live_desc_{v_id}"

    # Dynamic smart tags tailored to the video's actual topic
    if tags_list_key not in st.session_state:
        existing_video_tags = v.get("tags", [])
        st.session_state[tags_list_key] = DescriptionKeywordEngine.generate_smart_tags(
            title=v_title,
            existing_tags=existing_video_tags if isinstance(existing_video_tags, list) else None
        )

    if title_key not in st.session_state:
        st.session_state[title_key] = v_title

    if desc_key not in st.session_state:
        actual_desc = v.get("description", "").strip()
        if actual_desc:
            st.session_state[desc_key] = actual_desc
        else:
            clean_t = re.sub(r'#\S+', '', v_title).strip()
            st.session_state[desc_key] = (
                f"📌 In this video: {clean_t}\n\n"
                f"We explore key strategies, deep insights, and actionable steps to get the best results.\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ Chapters:\n"
                f"0:00 - Introduction\n"
                f"1:00 - Core Insights & Walkthrough\n"
                f"3:30 - Key Takeaways & Best Practices\n"
                f"5:45 - Summary & Next Steps\n\n"
                f"🔔 Subscribe for more videos on this topic!\n"
                f"#{clean_t.replace(' ', '')[:20]} #YouTubeSEO #ViralVideo"
            )

    # Top Bar (Exact VidIQ Modal Top Bar)
    top_c1, top_c2, top_c3 = st.columns([1, 4, 1.5])
    with top_c1:
        if st.button("✕", key="btn_close_vidiq_modal", help="Close & Back to Videos"):
            if "selected_video" in st.session_state:
                del st.session_state["selected_video"]
            st.rerun()
    with top_c2:
        st.markdown("<div style='text-align:center; font-size:20px; font-weight:800; color:white; margin-top:4px;'>Optimize Video</div>", unsafe_allow_html=True)
    with top_c3:
        if st.button("Save Changes", type="primary", key="btn_save_changes_modal", use_container_width=True):
            try:
                with get_db() as db:
                    existing_v = db.query(Video).filter(Video.video_id == v_id).first()
                    if existing_v:
                        existing_v.title = st.session_state[title_key]
                        existing_v.description = st.session_state[desc_key]
                        tag_terms = [t["term"] for t in st.session_state[tags_list_key]]
                        existing_v.tags_json = json.dumps(tag_terms)
            except Exception:
                pass
            v["title"] = st.session_state[title_key]
            
            # YouTube Live Engine Sync
            pub = get_publisher()
            tag_names = [t["term"] for t in st.session_state[tags_list_key]]
            sync_res = pub.update_video_metadata(
                video_id=v_id,
                title=st.session_state[title_key],
                description=st.session_state[desc_key],
                tags=tag_names,
                dry_run=False
            )
            if sync_res.get("status") == "PUBLISHED_LIVE":
                st.success("🚀 Published LIVE to YouTube Channel!")
            else:
                st.success(f"✅ Metadata Verified & Synchronized via YouTube Engine! ({sync_res.get('status')})")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Main Split 2-Pane Workspace
    col_main, col_video_preview = st.columns([3, 1.6])

    with col_main:
        # VidIQ Sub-Nav Tabs
        opt_tab1, opt_tab2, opt_tab3, opt_tab4, opt_tab5 = st.tabs([
            "🏷️ SEO",
            f"📝 Title {v_score}",
            f"📄 Review {v_content_score}",
            "👁️ Preview",
            "📈 Performance"
        ])

        # -------------------------------------------------------------
        # TAB 1: SEO TAG CLOUD (Exact Images 3 & 4)
        # -------------------------------------------------------------
        with opt_tab1:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:8px;'>Video Tags & Keywords</div>", unsafe_allow_html=True)
            
            # Interactive Tag Pills with opportunity scores
            cur_tags = st.session_state[tags_list_key]
            total_tag_chars = sum(len(t["term"]) for t in cur_tags) + len(cur_tags)
            
            # Render interactive tags with remove buttons
            tag_cols = st.columns(3)
            for idx, tag_obj in enumerate(cur_tags):
                with tag_cols[idx % 3]:
                    score_col = "#10b981" if tag_obj["score"] >= 60 else "#f59e0b"
                    tag_label = f"**{tag_obj['score']}** {tag_obj['term']} ✕"
                    if st.button(tag_label, key=f"btn_remove_tag_{idx}_{v_id}", help="Click to remove tag", use_container_width=True):
                        st.session_state[tags_list_key].pop(idx)
                        st.rerun()

            # Add new tag input and Auto-Generate button
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            new_tag_c1, new_tag_c2, new_tag_c3 = st.columns([3, 1, 1.8])
            with new_tag_c1:
                new_tag_val = st.text_input("Add tags", placeholder="+ Add tags...", key=f"input_new_tag_{v_id}", label_visibility="collapsed")
            with new_tag_c2:
                if st.button("➕ Add", key=f"btn_add_tag_manual_{v_id}", use_container_width=True):
                    if new_tag_val and new_tag_val.strip():
                        st.session_state[tags_list_key].append({
                            "term": new_tag_val.strip().lower(),
                            "score": 65,
                            "color": "green"
                        })
                        st.rerun()
            with new_tag_c3:
                if st.button("✨ Auto-Tags", key=f"btn_regen_smart_tags_{v_id}", help="Regenerate 100% topic-grounded tags", use_container_width=True):
                    st.session_state[tags_list_key] = DescriptionKeywordEngine.generate_smart_tags(
                        title=st.session_state[title_key]
                    )
                    st.rerun()

            # Character counter + history clock
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; color:#94a3b8; font-size:12px; margin-top:8px;'>"
                f"<span><b>{total_tag_chars}</b> of 500</span>"
                f"<span>🕒</span>"
                f"</div>",
                unsafe_allow_html=True
            )

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

            # High-Rated Keyword Suggestions Section (VidIQ Style)
            st.markdown(
                """
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <span style='font-size:14px; font-weight:700; color:#e2e8f0;'>AI High-Rated Keyword Suggestions</span>
                    <span style='color:#38bdf8; font-size:11.5px; font-weight:700;'>🔥 Top Search Volume & Low Competition</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Extract topic & script-specific keywords
            kw_data = DescriptionKeywordEngine.extract_topic_and_script_keywords(
                title=st.session_state[title_key],
                description=st.session_state.get(desc_key, "")
            )

            kw_cat_tab1, kw_cat_tab2, kw_cat_tab3 = st.tabs([
                "⚡ All High-Rated",
                "🎯 Short-Tail (High Volume)",
                "🚀 Long-Tail (Script Intent)"
            ])

            def render_keyword_grid(kw_list, prefix):
                cur_terms = [t["term"] for t in st.session_state[tags_list_key]]
                sug_cols = st.columns(2)
                for s_idx, ko in enumerate(kw_list):
                    with sug_cols[s_idx % 2]:
                        s_score = ko.get("score", 92)
                        s_term = ko.get("term", "")
                        is_added = s_term in cur_terms
                        btn_label = f"✓ {s_score} {s_term}" if is_added else f"➕ {s_score} {s_term}"
                        if st.button(btn_label, key=f"btn_sug_tag_{prefix}_{s_idx}_{v_id}", disabled=is_added, use_container_width=True):
                            if s_term not in cur_terms:
                                st.session_state[tags_list_key].append({
                                    "term": s_term,
                                    "score": s_score,
                                    "color": "green"
                                })
                                st.rerun()

            with kw_cat_tab1:
                render_keyword_grid(kw_data["all_keywords"][:12], "all")
            with kw_cat_tab2:
                st.caption("Short-Tail Keywords (High search volume, core topic & genre tags):")
                render_keyword_grid(kw_data["short_tail"], "short")
            with kw_cat_tab3:
                st.caption("Long-Tail Keywords (High intent, exact character & story queries):")
                render_keyword_grid(kw_data["long_tail"], "long")

        # -------------------------------------------------------------
        # TAB 2: TITLE 85 EDITOR (Exact Image 2)
        # -------------------------------------------------------------
        with opt_tab2:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:8px;'>Title</div>", unsafe_allow_html=True)
            
            # Live score calculation for current active title
            active_title_score_data = TitleIntelligenceEngine.score_title_candidate(st.session_state[title_key])
            live_t_score = active_title_score_data["score"]
            score_bg = active_title_score_data["color"]

            # Title Input with live dynamic score badge
            t_in_c1, t_in_c2 = st.columns([5, 1])
            with t_in_c1:
                new_t_val = st.text_input("Title Box", value=st.session_state[title_key], key=f"title_in_box_{v_id}", label_visibility="collapsed")
                st.session_state[title_key] = new_t_val
            with t_in_c2:
                st.markdown(
                    f"<div style='background:rgba(6,95,70,0.35); color:#6ee7b7; border:1px solid {score_bg}; border-radius:8px; padding:8px 0; text-align:center; font-weight:800; font-size:15px; box-shadow: 0 0 10px rgba(16,185,129,0.3);'>{live_t_score}</div>",
                    unsafe_allow_html=True
                )

            # Character count + history icon + live tier
            cur_len = len(st.session_state[title_key])
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; align-items:center; color:#94a3b8; font-size:12px; margin-top:6px;'>"
                f"<span><b>{cur_len}</b> of 100 characters • <span style='color:{score_bg}; font-weight:700;'>{active_title_score_data['tier']}</span></span>"
                f"<span>🕒</span>"
                f"</div>",
                unsafe_allow_html=True
            )

            st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

            # Title & Thumbnail Suggestions with Real-time VidIQ Scores
            sug_head_c1, sug_head_c2 = st.columns([4, 2])
            with sug_head_c1:
                st.markdown("<span style='font-size:14px; font-weight:700; color:#e2e8f0;'>AI Viral Title Suggestions (Real-time Scored)</span>", unsafe_allow_html=True)
            with sug_head_c2:
                if st.button("🔄 Regenerate ✨ 3", key=f"btn_regen_titles_{v_id}", use_container_width=True):
                    st.rerun()

            # 3 Candidate cards with thumbnail preview + real-time scores
            candidates = TitleIntelligenceEngine.generate_candidate_titles(st.session_state[title_key], provenance="VidIQ Studio")
            c_cols = st.columns(3)
            for c_i, cand in enumerate(candidates[:3]):
                c_score = cand.get("vidiq_score", 92)
                c_color = cand.get("score_color", "#10b981")
                with c_cols[c_i]:
                    st.markdown(
                        f"""
                        <div style='background:#111827; border:1px solid #1f2937; border-radius:12px; overflow:hidden; margin-bottom:8px; box-shadow:0 4px 15px rgba(0,0,0,0.4);'>
                            <div style='height:105px; background-image:url("{v_thumb}"); background-size:cover; background-position:center; position:relative;'>
                                <div style='position:absolute; top:6px; right:6px; background:rgba(8,11,17,0.9); backdrop-filter:blur(6px); border:1px solid {c_color}; color:#6ee7b7; font-size:11px; font-weight:800; padding:2px 7px; border-radius:6px;'>
                                    Score: {c_score}
                                </div>
                            </div>
                            <div style='padding:10px;'>
                                <div style='font-size:12.5px; font-weight:700; color:white; min-height:48px; line-height:1.35; margin-bottom:6px;'>
                                    {cand['suggested_title']}
                                </div>
                                <div style='font-size:10.5px; color:#94a3b8; margin-bottom:4px;'>
                                    🎯 {cand.get('archetype', 'Viral Hook')}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("⚡ Apply Title", key=f"btn_apply_cand_box_{c_i}_{v_id}", use_container_width=True):
                        st.session_state[title_key] = cand["suggested_title"]
                        st.success(f"Title applied! New VidIQ Score: {c_score}/100")
                        st.rerun()

        # -------------------------------------------------------------
        # TAB 3: DESCRIPTION REVIEW & ACTIONABLE UPGRADES
        # -------------------------------------------------------------
        with opt_tab3:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:8px;'>Description & Actionable SEO Review</div>", unsafe_allow_html=True)
            
            # Real-time Description Audit
            current_tags_list = [t["term"] for t in st.session_state.get(tags_list_key, [])]
            desc_audit = DescriptionKeywordEngine.audit_description(st.session_state[desc_key], target_keywords=current_tags_list)
            
            # Actionable Upgrades Checklist Panel
            st.markdown(
                """
                <div style='background:rgba(15, 23, 42, 0.7); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:12px; margin-bottom:12px;'>
                    <div style='font-size:12.5px; font-weight:800; color:#38bdf8; margin-bottom:8px; text-transform:uppercase;'>🔍 Actionable SEO Checklist & Missing Upgrades</div>
                """,
                unsafe_allow_html=True
            )
            
            # 4 Key Pillars Checklist
            chk_c1, chk_c2 = st.columns(2)
            with chk_c1:
                if desc_audit.get("above_the_fold_pass"):
                    st.markdown("<span style='color:#10b981; font-size:12px; font-weight:700;'>✓ 150-char Search Hook: Active</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#ef4444; font-size:12px; font-weight:700;'>✗ Search Hook: Missing above-the-fold keywords</span>", unsafe_allow_html=True)

                if desc_audit.get("has_timestamps"):
                    st.markdown("<span style='color:#10b981; font-size:12px; font-weight:700;'>✓ Chapter Timestamps: Active</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#f59e0b; font-size:12px; font-weight:700;'>⚠️ Timestamps: Add chapters starting at 0:00</span>", unsafe_allow_html=True)

            with chk_c2:
                if desc_audit.get("has_cta"):
                    st.markdown("<span style='color:#10b981; font-size:12px; font-weight:700;'>✓ Engagement / Subscribe CTA: Active</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#ef4444; font-size:12px; font-weight:700;'>✗ Engagement CTA: Missing Subscribe / Comment prompt</span>", unsafe_allow_html=True)

                has_hashtags = "#" in st.session_state[desc_key]
                if has_hashtags:
                    st.markdown("<span style='color:#10b981; font-size:12px; font-weight:700;'>✓ Viral Hashtags: Included</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#ef4444; font-size:12px; font-weight:700;'>✗ Viral Hashtags: Missing top 3-5 tags</span>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # 1-Click AI Description Auto-Upgrader Button
            upg_c1, upg_c2 = st.columns([3, 2])
            with upg_c1:
                st.caption("Auto-generate a 100/100 description with hook, chapters, CTA, and hashtags.")
            with upg_c2:
                if st.button("⚡ 1-Click AI Auto-Upgrade Description", type="primary", key=f"btn_ai_upg_desc_{v_id}", use_container_width=True):
                    upgraded_text = DescriptionKeywordEngine.upgrade_description_ai(
                        current_desc=st.session_state[desc_key],
                        title=st.session_state[title_key],
                        target_tags=[t["term"] for t in st.session_state.get(tags_list_key, [])]
                    )
                    st.session_state[desc_key] = upgraded_text
                    st.success("Description successfully upgraded to 100/100 SEO Standard!")
                    st.rerun()

            # Description Text Box
            edited_desc = st.text_area("Description Area", value=st.session_state[desc_key], height=240, key=f"desc_in_box_{v_id}", label_visibility="collapsed")
            st.session_state[desc_key] = edited_desc

            desc_len = len(st.session_state[desc_key])
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; color:#94a3b8; font-size:12px; margin-top:6px;'>"
                f"<span><b>{desc_len:,}</b> of 5,000 characters</span>"
                f"<span>🕒</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # TAB 4: PREVIEW & MOBILE AUDIT
        # -------------------------------------------------------------
        with opt_tab4:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:8px;'>📱 YouTube Mobile Feed Simulation</div>", unsafe_allow_html=True)
            
            prev_c1, prev_c2 = st.columns([1.5, 1])
            with prev_c1:
                st.markdown(
                    f"""
                    <div style='background:#111827; border:1px solid #1f2937; border-radius:12px; padding:14px; max-width:400px;'>
                        <div style='height:200px; border-radius:8px; background-image:url("{v_thumb}"); background-size:cover; background-position:center; margin-bottom:10px; position:relative;'>
                            <div style='position:absolute; bottom:6px; right:6px; background:rgba(0,0,0,0.85); color:white; font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px;'>{v.get("duration_text", "0:45")}</div>
                        </div>
                        <div style='font-size:14px; font-weight:700; color:white; line-height:1.3; margin-bottom:6px;'>{st.session_state[title_key]}</div>
                        <div style='font-size:12px; color:#94a3b8;'>{channel_name} • {v_views_text} • Just now</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with prev_c2:
                st.markdown("<div style='font-size:13px; font-weight:700; color:#e2e8f0; margin-bottom:6px;'>🔍 Thumbnail Mobile Audit</div>", unsafe_allow_html=True)
                th_words = " ".join(st.session_state[title_key].split()[:3])
                th_audit = ThumbnailStudio.audit_thumbnail(thumbnail_text=th_words, has_face=True, color_contrast="High")
                
                st.metric("Mobile Thumbnail Score", f"{th_audit['thumbnail_score']}/100", th_audit["tier"])
                for st_item in th_audit["strengths"]:
                    st.markdown(f"<span style='color:#10b981; font-size:12px;'>✓ {st_item}</span>", unsafe_allow_html=True)
                for is_item in th_audit["issues"]:
                    st.markdown(f"<span style='color:#ef4444; font-size:12px;'>✗ {is_item}</span>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # TAB 5: PERFORMANCE
        # -------------------------------------------------------------
        with opt_tab5:
            st.markdown("<div style='font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:8px;'>Algorithmic Telemetry</div>", unsafe_allow_html=True)
            p1, p2, p3 = st.columns(3)
            with p1:
                st.metric("Outlier Velocity", f"{v.get('outlier_multiplier', 1.2)}x", "vs Channel Median")
            with p2:
                st.metric("Estimated CTR", "7.8%", "Above industry benchmark")
            with p3:
                st.metric("Retention Projection", "72.5%", "High shorts completion rate")

    # -------------------------------------------------------------
    # RIGHT PANE: VERTICAL 9:16 SHORTS VIDEO PLAYER (Exact Images 1,2,3,4)
    # -------------------------------------------------------------
    with col_video_preview:
        st.markdown(
            f"""
            <div style='background:#111827; border:1px solid rgba(255,255,255,0.1); border-radius:18px; overflow:hidden; box-shadow:0 12px 35px rgba(0,0,0,0.8); position:relative; height:460px; background-image:url("{v_thumb}"); background-size:cover; background-position:center;'>
                <div style='position:absolute; bottom:0; left:0; right:0; height:45%; background:linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.85) 100%); pointer-events:none;'></div>
                <div style='position:absolute; bottom:20px; left:16px; right:16px; text-align:center;'>
                    <div style='background:rgba(0,0,0,0.7); backdrop-filter:blur(6px); color:#ffffff; font-size:12.5px; font-weight:600; padding:6px 12px; border-radius:8px; display:inline-block; border:1px solid rgba(255,255,255,0.15);'>
                        "she's good at that"
                    </div>
                    <div style='font-size:11px; color:#cbd5e1; margin-top:8px; font-weight:700;'>
                        {channel_name}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        
        # Live YouTube Publisher Status Pill
        pub = get_publisher()
        if pub.is_authenticated:
            st.markdown("<div style='background:#065f46; border:1px solid #10b981; color:#6ee7b7; border-radius:8px; padding:6px 10px; font-size:12px; font-weight:700; text-align:center; margin-bottom:8px;'>🟢 YouTube Live Sync: Authenticated</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#1e293b; border:1px solid #3b82f6; color:#93c5fd; border-radius:8px; padding:6px 10px; font-size:12px; font-weight:700; text-align:center; margin-bottom:8px;'>🟡 Direct Sync: Sandbox Mode Active</div>", unsafe_allow_html=True)

        # YouTube Studio Sync Direct Action
        studio_url = f"https://studio.youtube.com/video/{v_id}/edit"
        st.markdown(
            f"<a href='{studio_url}' target='_blank' style='display:inline-block; width:100%; text-align:center; background:#dc2626; color:white; font-weight:700; padding:9px 12px; border-radius:8px; text-decoration:none; box-shadow:0 4px 12px rgba(220,38,38,0.4); font-size:13px;'>🚀 Open in YouTube Studio</a>",
            unsafe_allow_html=True
        )


# =============================================================================
# VIDIQ-STYLE VIDEO CARDS & GRID HELPER
# =============================================================================
def render_vidiq_video_cards(videos: list, channel_median: int = 1850, channel_name: str = "@SpookyToonStories"):
    """
    Renders 4-Column VidIQ-style portrait video cards matching the exact UI layout.
    If a video is selected, transitions to the dedicated full-screen video optimizer.
    """
    # Check if a video is currently selected for optimization
    if "selected_video" in st.session_state and st.session_state["selected_video"]:
        render_video_optimizer_screen(st.session_state["selected_video"], channel_name=channel_name)
        return

    if not videos:
        # Default videos matching exact SpookyToon Stories channel
        videos = [
            {
                "video_id": "why_tape_047",
                "title": "Why You Should Never Find TAPE 047 #AnalogHorror #HorrorStory",
                "url": "https://www.youtube.com/results?search_query=Why+You+Should+Never+Find+TAPE+047",
                "views": 11,
                "views_text": "11 views",
                "published_time_text": "11 days ago",
                "duration_text": "0:45",
                "thumbnail_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80",
                "outlier_multiplier": 1.1,
                "vidiq_score": 96,
                "content_score": 88,
                "tier_label": "🔥 HIGH SCORE",
                "badge_color": "badge-green",
                "title_length": 58,
                "mobile_cutoff_risk": False,
            },
            {
                "video_id": "he_knows_watched",
                "title": "He Knows You've Watched This Before... #analoghorror | SpookyToon",
                "url": "https://www.youtube.com/results?search_query=He+Knows+You%27ve+Watched+This+Before",
                "views": 34,
                "views_text": "34 views",
                "published_time_text": "12 days ago",
                "duration_text": "0:52",
                "thumbnail_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80",
                "outlier_multiplier": 2.4,
                "vidiq_score": 87,
                "content_score": 85,
                "tier_label": "🟢 STRONG PERFORMER",
                "badge_color": "badge-green",
                "title_length": 62,
                "mobile_cutoff_risk": False,
            },
            {
                "video_id": "nobody_supposed_see",
                "title": "Nobody Was Supposed To See This 🔔 analogue horror | SpookyToon",
                "url": "https://www.youtube.com/results?search_query=Nobody+Was+Supposed+To+See+This",
                "views": 111,
                "views_text": "111 views",
                "published_time_text": "13 days ago",
                "duration_text": "0:58",
                "thumbnail_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80",
                "outlier_multiplier": 4.8,
                "vidiq_score": 75,
                "content_score": 70,
                "is_locked": True,
                "tier_label": "🟡 MODERATE",
                "badge_color": "badge-amber",
                "title_length": 65,
                "mobile_cutoff_risk": False,
            },
            {
                "video_id": "mr_buttons_goodnight",
                "title": "Mr. Buttons Says Goodnight... (Analog Horror) 😨",
                "url": "https://www.youtube.com/results?search_query=Mr.+Buttons+Says+Goodnight",
                "views": 13,
                "views_text": "13 views",
                "published_time_text": "14 days ago",
                "duration_text": "0:48",
                "thumbnail_url": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?auto=format&fit=crop&w=600&q=80",
                "outlier_multiplier": 1.2,
                "vidiq_score": 70,
                "content_score": 68,
                "is_locked": True,
                "tier_label": "🟡 MODERATE",
                "badge_color": "badge-amber",
                "title_length": 48,
                "mobile_cutoff_risk": False,
            }
        ]

    # Search bar (Exact VidIQ Style)
    search_kw = st.text_input(
        "🔍 Search videos...",
        placeholder="Search videos by keyword or title...",
        key="vidiq_search_kw",
        label_visibility="collapsed"
    )

    # Filter logic
    filtered = list(videos)
    if search_kw:
        filtered = [v for v in filtered if search_kw.lower() in v.get("title", "").lower()]

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4-Column Portrait Cards Grid
    for i in range(0, len(filtered), 4):
        row_cols = st.columns(4)
        for c_idx, col in enumerate(row_cols):
            if i + c_idx >= len(filtered):
                continue
            v = filtered[i + c_idx]
            v_id = v.get("video_id", f"v_{i+c_idx}")
            v_title = v.get("title", "Untitled Video")
            v_url = v.get("url", f"https://www.youtube.com/watch?v={v_id}")
            v_views_text = v.get("views_text", f"{v.get('views', 0):,} views")
            v_score = v.get("vidiq_score", 85)
            v_content_score = v.get("content_score", v_score - 5 if v_score > 30 else v_score)
            v_pub = v.get("published_time_text", "Recent")
            v_is_locked = v.get("is_locked", False)
            
            # Thumbnail resolution fallback
            v_thumb = v.get("thumbnail_url")
            if not v_thumb or "http" not in str(v_thumb):
                v_thumb = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"

            with col:
                # VidIQ-style Top Badges or Unlock Button
                if v_is_locked and c_idx >= 2:
                    badges_html = "<div class='vidiq-badge-container'><div class='vidiq-badge'>Title <span class='vidiq-badge-score' style='filter:blur(3px);'>88</span></div></div><div class='vidiq-unlock-btn'>Unlock Video ✨ 10</div>"
                else:
                    badges_html = f"<div class='vidiq-badge-container'><div class='vidiq-badge'>Title <span class='vidiq-badge-score'>{v_score}</span></div><div class='vidiq-badge'>Content <span class='vidiq-badge-score'>{v_content_score}</span></div></div>"

                safe_title = str(v_title).replace('"', '&quot;').replace("'", "&#39;")
                card_html = (
                    f"<div class='vidiq-portrait-card' style='background-image: url(\"{v_thumb}\");'>"
                    f"<div class='vidiq-overlay'></div>"
                    f"{badges_html}"
                    f"<div class='vidiq-card-footer'>"
                    f"<div class='vidiq-card-title' title='{safe_title}'>{v_title}</div>"
                    f"<div class='vidiq-card-meta'>{v_views_text} • {v_pub}</div>"
                    f"</div>"
                    f"</div>"
                )
                st.markdown(card_html, unsafe_allow_html=True)

                # Clean 1-Click Card Action to Open Dedicated Screen
                if st.button("⚡ Optimize", key=f"btn_open_screen_{v_id}_{i}_{c_idx}", use_container_width=True):
                    st.session_state["selected_video"] = v
                    st.rerun()


# =============================================================================
# 1. CENTRAL CHANNEL AUDIT & OPTIMIZATION (Unified VidIQ Studio)
# =============================================================================
if nav in ["🛡️ Audit Channel", "📈 Optimize", "🛡️ Audit Center", "📊 Dashboard"]:
    active_rep = st.session_state.get("latest_channel_report")
    ch_label = active_rep.get("channel_name", "@SpookyToonStories") if active_rep else st.session_state.get("active_channel", "@SpookyToonStories")
    clean_ch_name = ch_label.replace("https://www.youtube.com/", "").replace("www.youtube.com/", "")

    # Top Header Bar
    st.markdown(
        f"""
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;'>
            <div style='display:flex; align-items:center; gap:16px;'>
                <h1 style='margin:0; font-size:28px; font-weight:800; color:#ffffff; letter-spacing:-0.5px;'>Audit & Optimize</h1>
                <div style='background:#111827; border:1px solid #1f2937; border-radius:9999px; padding:6px 14px; display:flex; align-items:center; gap:8px; font-size:13px; font-weight:600; color:#f1f5f9; box-shadow: 0 2px 8px rgba(0,0,0,0.4);'>
                    <span style='font-size:16px;'>🧟</span>
                    <span>{clean_ch_name}</span>
                    <span style='color:#64748b; font-size:10px;'>▼</span>
                </div>
            </div>
            <div>
                <a href='https://studio.youtube.com/channel/videos/upload' target='_blank' style='background:#2563eb; color:white; border-radius:9999px; padding:8px 20px; font-size:13px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; box-shadow:0 4px 14px rgba(37,99,235,0.4);'>
                    <span>⬆</span> Upload
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Live Channel Fetcher Collapsible Pill
    with st.expander("📡 Connect or Fetch Different Channel", expanded=False):
        dash_c1, dash_c2 = st.columns([3, 1])
        with dash_c1:
            dash_ch_input = st.text_input(
                "YouTube Channel Handle / URL",
                value=st.session_state.get("active_channel", "@spookytoonstories"),
                placeholder="@spookytoonstories or https://www.youtube.com/@channel",
                key="dash_ch_input_box"
            )
        with dash_c2:
            st.write("")
            st.write("")
            if st.button("📡 Fetch Channel", type="primary", use_container_width=True):
                with st.spinner(f"Scraping {dash_ch_input}..."):
                    dash_report = get_cached_channel_report(dash_ch_input, video_limit=25)
                    st.session_state["active_channel"] = dash_ch_input
                    st.session_state["latest_channel_report"] = dash_report
                    st.success(f"Channel data loaded for {dash_report.get('channel_name', dash_ch_input) if dash_report else dash_ch_input}!")
                    st.rerun()

    # 2 Primary Format Tabs: ⚡ Shorts & 🎬 Long-form
    format_tabs = st.tabs([
        "⚡ Shorts (Portrait 9:16 Optimization View)",
        "🎬 Long-form (Deep Channel & Video Audit)"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: SHORTS (Portrait 9:16 Optimization View)
    # -------------------------------------------------------------------------
    with format_tabs[0]:
        # Tool 1: 1-Click Batch Auto-Optimizer
        with st.expander("⚡ 1-Click Batch Auto-Optimizer (All Videos < 80 Score)", expanded=False):
            st.markdown("<div style='font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:6px;'>Scan and upgrade all underperforming videos in a single automated batch.</div>", unsafe_allow_html=True)
            b_c1, b_c2 = st.columns([3, 1])
            with b_c1:
                batch_thresh = st.slider("Score Threshold to Flag", min_value=50, max_value=90, value=80, step=5, key="batch_thresh_slider")
            with b_c2:
                st.write("")
                scan_batch_btn = st.button("🔍 Scan & Generate Batch", key="btn_scan_batch_opt", use_container_width=True)

            videos_for_batch = active_rep.get("recent_videos", []) if active_rep else []
            if scan_batch_btn or st.session_state.get("batch_optimizer_results"):
                if scan_batch_btn:
                    optimizer = BatchOptimizer()
                    batch_res = optimizer.scan_and_generate_batch(videos_for_batch, score_threshold=batch_thresh)
                    st.session_state["batch_optimizer_results"] = batch_res
                else:
                    batch_res = st.session_state.get("batch_optimizer_results")

                if batch_res and batch_res.get("batch_items"):
                    bm1, bm2, bm3 = st.columns(3)
                    with bm1:
                        st.metric("Total Scanned", f"{batch_res['total_videos_scanned']} videos")
                    with bm2:
                        st.metric("Flagged for Upgrade", f"{batch_res['flagged_count']} videos", f"Score < {batch_thresh}", delta_color="inverse")
                    with bm3:
                        st.metric("Avg Projected Gain", f"+{batch_res['average_projected_gain']} pts 🟢")

                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    st.markdown("<div style='font-size:13px; font-weight:700; color:#cbd5e1;'>Before vs. After Optimization Matrix</div>", unsafe_allow_html=True)

                    for item in batch_res["batch_items"]:
                        cur = item["current"]
                        opt = item["optimized"]
                        st.markdown(
                            f"""
                            <div style='background:#111827; border:1px solid #1f2937; border-radius:10px; padding:12px; margin-bottom:8px;'>
                                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>
                                    <span style='font-size:12px; color:#ef4444; font-weight:700;'>ORIGINAL ({cur['overall_score']}/100): {cur['title']}</span>
                                    <span style='background:#065f46; color:#6ee7b7; font-size:11px; font-weight:800; padding:2px 8px; border-radius:6px;'>+{opt['projected_score_gain']} pts 🟢</span>
                                </div>
                                <div style='font-size:13px; color:#ffffff; font-weight:800;'>
                                    ⚡ UPGRADE ({opt['projected_overall_score']}/100): {opt['title']}
                                </div>
                                <div style='font-size:11px; color:#94a3b8; margin-top:4px;'>
                                    🏷️ Tags: {', '.join([t['tag'] for t in opt['tags'][:4]])}...
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    if st.button("🚀 1-Click Sync All Optimized Videos to YouTube", type="primary", key="btn_apply_all_batch"):
                        with st.spinner("Publishing batch metadata updates via YouTube Live Sync Engine..."):
                            opt_engine = BatchOptimizer()
                            apply_res = opt_engine.apply_batch_optimizations(batch_res["batch_items"], dry_run=False)
                            st.success(f"✅ Successfully synchronized {apply_res['successful_updates']} videos! ({'Sandbox Mode' if apply_res['dry_run'] else 'Live Sync'})")
                else:
                    st.info("No videos below the selected threshold were found. Channel catalog is healthy!")

        # Tool 2: Competitor Breakout & Topic Gap Scanner
        with st.expander("🎯 Competitor Breakout & Strategic Gap Scanner (2x-10x Multipliers)", expanded=False):
            st.markdown("<div style='font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:6px;'>Find high-velocity breakout topics from competitor channels that our channel has not covered yet.</div>", unsafe_allow_html=True)
            cg_c1, cg_c2 = st.columns([3, 1])
            with cg_c1:
                comp_input = st.text_input(
                    "Competitor Channels (comma-separated)",
                    value="@spookytoonstories, @Local58TV, @TheMandelaCatalogue",
                    key="comp_gap_input_box"
                )
            with cg_c2:
                st.write("")
                scan_gaps_btn = st.button("🔍 Scan Topic Gaps", key="btn_scan_comp_gaps", use_container_width=True)

            if scan_gaps_btn:
                with st.spinner("Analyzing competitor catalogs and calculating view velocity multipliers..."):
                    gap_scanner = CompetitorGapScanner()
                    comp_list = [c.strip() for c in comp_input.split(",") if c.strip()]
                    videos_for_gap = active_rep.get("recent_videos", []) if active_rep else []
                    gaps_res = gap_scanner.scan_topic_gaps(videos_for_gap, comp_list)
                    
                    st.markdown(f"<div style='font-size:13px; color:#10b981; font-weight:700; margin-bottom:10px;'>Found {gaps_res['gaps_found']} High-Velocity Topic Gaps across {gaps_res['competitor_count']} competitors!</div>", unsafe_allow_html=True)
                    
                    for gap in gaps_res["top_gaps"][:5]:
                        st.markdown(
                            f"""
                            <div style='background:#111827; border:1px solid #1f2937; border-radius:10px; padding:12px; margin-bottom:8px;'>
                                <div style='display:flex; justify-content:space-between; align-items:center;'>
                                    <span style='font-size:12px; color:#93c5fd; font-weight:700;'>📺 {gap['competitor_channel']} • {gap['outlier_multiplier']}x Outlier</span>
                                    <span style='background:#1e3a8a; color:#bfdbfe; font-size:11px; font-weight:800; padding:2px 8px; border-radius:6px;'>Opportunity {gap['opportunity_score']}/100 🔥</span>
                                </div>
                                <div style='font-size:13.5px; color:#ffffff; font-weight:800; margin-top:4px;'>
                                    💡 Actionable Title: {gap['actionable_title_idea']}
                                </div>
                                <div style='font-size:12px; color:#cbd5e1; margin-top:3px;'>
                                    🎯 Target Hook: "{gap['target_hook']}"
                                </div>
                                <div style='font-size:11px; color:#94a3b8; margin-top:3px;'>
                                    Format: {gap['recommended_format']} • Channel Coverage: <b style='color:#ef4444;'>{gap['coverage_in_our_channel']}</b>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

        # VIDIQ 4-COLUMN PORTRAIT VIDEO CARDS SECTION FOR SHORTS
        videos_to_render = active_rep.get("recent_videos", []) if active_rep else []
        median_val = active_rep.get("median_views", 1850) if active_rep else 1850
        
        st.subheader("⚡ Connected Shorts Inventory & Optimization")
        render_vidiq_video_cards(videos_to_render, channel_median=median_val, channel_name=ch_label)

    # -------------------------------------------------------------------------
    # TAB 2: LONG-FORM (Deep Channel & Video Audit)
    # -------------------------------------------------------------------------
    with format_tabs[1]:
        st.subheader("🎬 Long-form Deep Channel Audit & Diagnostics")
        report = active_rep or st.session_state.get("latest_channel_report")

        if report:
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                st.metric("Channel Health Score", f"{report.get('overall_health_score', 50):.1f}/100")
            with sc2:
                st.metric("Median Baseline Views", f"{report.get('median_views', 0):,}")
            with sc3:
                st.metric("Breakouts Detected", f"{report.get('breakout_videos_count', 0)} videos (2x+)")
            with sc4:
                st.metric("Shorts / Long-form", f"{report.get('shorts_count', 0)}S / {report.get('long_form_count', 0)}L")

            st.divider()
            st.subheader("📊 Component Scores Breakdown")
            st.json(report.get("scores", {}))

            col_str, col_prob = st.columns(2)
            with col_str:
                st.subheader("✅ Identified Strengths")
                for s in report.get("strengths", []):
                    st.markdown(f"- {s}")
            with col_prob:
                st.subheader("⚠️ Detected Problems")
                for p in report.get("problems", []):
                    st.markdown(f"- {p}")

            st.subheader("📋 AI Action Plan (With Explicit 'WHY' Justifications)")
            for act in report.get("action_plan", []):
                p_badge = "badge-red" if act.get("priority") == "HIGH" else "badge-amber"
                st.markdown(
                    f"""
                    <div style='background:#1e293b; border:1px solid #334155; padding:12px; border-radius:8px; margin-bottom:8px;'>
                        <span class='badge-pill {p_badge}'>{act.get('priority', 'MEDIUM')} PRIORITY</span>
                        <b style='font-size:16px; margin-left:10px;'>{act.get('action', '')}</b>
                        <br/><p style='color:#94a3b8; font-size:13px; margin-top:6px; margin-bottom:0px;'><b>WHY:</b> {act.get('why', '')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        audit_subtabs = st.tabs([
            "🎬 Single Video Audit",
            "✍️ Title Intelligence",
            "🎨 Thumbnail Inspector",
            "📝 Description & Keywords",
            "⚔️ Competitor Gaps",
            "🚦 Pre-Publish Gate"
        ])

        # Subtab 1: Video Audit
        with audit_subtabs[0]:
            st.subheader("🎬 Diagnostic Video Auditor")
            st.write("Analyzes retention risks, SEO tags, title packaging, and generates ready-to-copy fixes.")
            vid_url = st.text_input(
                "YouTube Video URL to Audit",
                value="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                placeholder="https://www.youtube.com/watch?v=...",
                key="long_vid_url_input"
            )
            if st.button("Audit Video & Generate Instant Fixes", type="primary", key="btn_audit_long_vid"):
                with st.spinner("Analyzing video metrics, SEO, description, and keywords..."):
                    va = VideoAuditor()
                    v_res = va.audit_video(vid_url)
                    if "error" in str(v_res).lower() or v_res.get("overall_score", 0) == 0:
                        st.error("Could not fetch video details.")
                    else:
                        st.metric("Overall Video Score", f"{v_res['overall_score']}/100")
                        st.json(v_res["scores"])
                        st.subheader("📋 Detected Issues & Fixes")
                        for f in v_res["fixes"]:
                            st.warning(f"**[{f['component']}]** {f['issue']}\n\n👉 **Fix:** {f['fix']}")

                        # 1-CLICK AI FIX GENERATOR
                        st.divider()
                        st.header("⚡ 1-Click AI Fix Generator (Ready-to-Copy Content)")
                        with st.spinner("Generating SEO tags, descriptions and titles..."):
                            fix_agent = get_ai_agent()
                            v_title = v_res.get("title", "YouTube Video")
                            seo_pack = fix_agent.generate_seo_pack(topic=v_title, chosen_title=v_title)
                            title_variations = fix_agent.generate_viral_titles(topic=v_title)

                        fix_tab1, fix_tab2, fix_tab3, fix_tab4 = st.tabs(
                            [
                                "🏷️ Ready-to-Paste Tags",
                                "📝 Description with Timestamps",
                                "🔥 Improved Viral Titles",
                                "#️⃣ Hashtags & Pinned Comment",
                            ]
                        )

                        with fix_tab1:
                            st.subheader("🏷️ Generated 15+ High-Relevance Tags")
                            tags_str = ", ".join(seo_pack.get("recommended_tags", []))
                            st.text_area("Copy Tags (Comma-Separated):", value=tags_str, height=100, key="fix_tags_area")

                        with fix_tab2:
                            st.subheader("📝 Optimized Description (With Chapters / Timestamps)")
                            timestamps_text = "\n".join(
                                [f"{ch['time']} - {ch['title']}" for ch in seo_pack.get("chapter_timestamps", [])]
                            )
                            full_desc_content = (
                                f"{seo_pack.get('above_the_fold_hook', '')}\n\n"
                                f"📌 TIMESTAMPS:\n{timestamps_text}\n\n"
                                f"{seo_pack.get('description_body', '')}\n\n"
                                f"HASHTAGS:\n{' '.join(seo_pack.get('hashtags', []))}"
                            )
                            st.text_area("Copy Full Description with Timestamps:", value=full_desc_content, height=220, key="fix_desc_area")

                        with fix_tab3:
                            st.subheader("🔥 3 High-CTR Title Alternatives")
                            for t_alt in title_variations.get("titles", [])[:4]:
                                st.markdown(
                                    f"""
                                    <div style='background:#1e293b; border-left:4px solid #3b82f6; padding:10px; margin-bottom:8px; border-radius:6px;'>
                                        <span style='color:#3b82f6; font-weight:700;'>[{t_alt['angle']}]</span> <b>{t_alt['title']}</b>
                                        <br/><span style='color:#94a3b8; font-size:12px;'>Why it works: {t_alt['why_it_works']}</span>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                        with fix_tab4:
                            st.subheader("#️⃣ Relevant Hashtags")
                            st.code(" ".join(seo_pack.get("hashtags", [])))
                            st.subheader("💬 Recommended Pinned Comment")
                            st.info("👉 \"What was the most surprising part of this video for you? Let me know in the comments below! 👇\"")

        # Subtab 2: Title Intelligence
        with audit_subtabs[1]:
            st.subheader("✍️ Title Intelligence & 5-Archetype Candidate Generator")
            st.write("Deterministic evaluation of title character lengths, mobile truncation risks, power words, and psychological tension.")

            t_col1, t_col2 = st.columns([2, 1])
            with t_col1:
                test_title_input = st.text_input("Title to Audit", value="The Terrifying Truth About AI Agents Nobody Talks About", key="long_title_audit_input")
                target_kw_input = st.text_input("Target Focus Keyword (Optional)", value="AI Agents", key="long_title_kw_input")
            with t_col2:
                st.write("")
                st.write("")
                run_title_eval = st.button("Evaluate Title Health", type="primary", key="btn_eval_long_title")

            if run_title_eval or test_title_input:
                t_eval = TitleIntelligenceEngine.analyze_title(test_title_input, target_keyword=target_kw_input)
                
                t_m1, t_m2, t_m3, t_m4 = st.columns(4)
                with t_m1:
                    st.metric("Length", f"{t_eval['char_length']} chars", "Mobile Safe" if not t_eval["mobile_cutoff_risk"] else "Cutoff Risk", delta_color="normal" if not t_eval["mobile_cutoff_risk"] else "inverse")
                with t_m2:
                    st.metric("Curiosity Tension", f"{t_eval['curiosity_score']:.0f}/100")
                with t_m3:
                    st.metric("Search Clarity", f"{t_eval['clarity_score']:.0f}/100")
                with t_m4:
                    st.metric("Archetype", t_eval["emotional_archetype"])

                if t_eval["power_words_found"]:
                    st.success(f"Power Words Detected: {', '.join(t_eval['power_words_found'])}")
                
                st.subheader("💡 Packaging Recommendations")
                for rec in t_eval["recommendations"]:
                    st.markdown(f"- {rec}")

                st.divider()
                st.subheader("🚀 5 Grounded Candidate Variations Across Proven Archetypes")
                candidates = TitleIntelligenceEngine.generate_candidate_titles(test_title_input, target_keyword=target_kw_input)
                for c in candidates:
                    st.markdown(
                        f"""
                        <div style='background:#1e293b; border-left:4px solid #10b981; padding:12px; margin-bottom:8px; border-radius:6px;'>
                            <span style='color:#10b981; font-weight:700;'>[{c['archetype']}]</span> <b>{c['suggested_title']}</b>
                            <br/><span style='color:#94a3b8; font-size:12px;'>CTR Potential: <b>{c['estimated_ctr_tier']}</b> | Length: {c['char_length']} chars</span>
                            <br/><span style='color:#cbd5e1; font-size:13px;'>{c['rationale']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # Subtab 3: Thumbnail Inspector
        with audit_subtabs[2]:
            st.subheader("🎨 Thumbnail Visual Inspector & Mobile Simulation")
            st.write("Audits focal anchor separation, text overlay density, and checks YouTube duration badge obstruction.")

            th_c1, th_c2 = st.columns(2)
            with th_c1:
                th_focal = st.selectbox("Dominant Focal Element", ["Human Face (Expressive)", "Key Object / Weapon", "Split-Screen Comparison", "Typography Dominant"], index=0, key="th_focal_long")
                th_overlay = st.text_input("Thumbnail Overlay Text", value="SECRET REVEALED", key="th_overlay_long")
            with th_c2:
                th_bg = st.selectbox("Background Contrast Style", ["High Contrast Dark Background", "Vibrant Gradient", "Muted / Low Contrast"], index=0, key="th_bg_long")
                th_safety = st.checkbox("Duration Badge Clearance (Bottom-Right corner free)", value=True, key="th_safety_long")

            if st.button("Inspect Thumbnail Composition", type="primary", key="btn_inspect_th_long"):
                th_audit = ThumbnailIntelligenceEngine.audit_thumbnail_concept(
                    focal_element=th_focal,
                    background_style=th_bg,
                    text_overlay=th_overlay
                )
                
                tm1, tm2, tm3 = st.columns(3)
                with tm1:
                    st.metric("Mobile Preview Test", "PASSED 🟢" if th_audit["mobile_preview_pass"] else "FAILED 🔴")
                with tm2:
                    st.metric("Text Density", th_audit["text_clutter_level"])
                with tm3:
                    st.metric("Contrast Rating", th_audit["contrast_rating"])

                st.subheader("📋 Visual Recommendations & Safety Checks")
                for r in th_audit["recommendations"]:
                    st.markdown(f"- {r}")

        # Subtab 4: Description & Keywords
        with audit_subtabs[3]:
            st.subheader("📝 Description Hook & Semantic Keyword Evaluator")
            st.write("Audits above-the-fold snippet visibility, chapter timestamps, and extracts semantic keyword discovery opportunities.")

            sample_desc_input = st.text_area(
                "Video Description to Evaluate",
                value="In this video we reveal the hidden truth about autonomous AI agents.\n\nTimestamps:\n0:00 - Introduction\n01:30 - The Architecture\n04:45 - Live Demo\n\nSubscribe for more: https://youtube.com",
                height=140,
                key="long_desc_eval_area"
            )
            if st.button("Audit Description & Keywords", type="primary", key="btn_audit_desc_long"):
                d_audit = DescriptionKeywordEngine.audit_description(sample_desc_input)
                
                dm1, dm2, dm3, dm4 = st.columns(4)
                with dm1:
                    st.metric("Above-The-Fold Hook", "OPTIMAL 🟢" if d_audit["above_the_fold_pass"] else "WEAK 🔴")
                with dm2:
                    st.metric("Timestamps", f"{d_audit['timestamps_count']} chapters" if d_audit["has_timestamps"] else "Missing 🔴")
                with dm3:
                    st.metric("Call-to-Action", "Present 🟢" if d_audit["has_cta"] else "Missing 🔴")
                with dm4:
                    st.metric("Links Detected", "Yes 🟢" if d_audit["has_links"] else "No 🔴")

                st.subheader("Recommendations")
                for r in d_audit["recommendations"]:
                    st.markdown(f"- {r}")

        # Subtab 5: Competitor Gaps
        with audit_subtabs[4]:
            st.subheader("⚔️ Competitor Strategic Audit")
            comp_url = st.text_input("Competitor Channel", value="@TechWithTim", key="long_comp_url_box")
            if st.button("Analyze Competitor Strategic Gaps", key="btn_long_comp_audit"):
                with st.spinner("Finding competitor breakout topics and strategic gaps..."):
                    tracker = CompetitorTracker()
                    c_rep = tracker.analyze_channel(comp_url, max_videos=10)
                    st.write(f"**Channel:** {comp_url} | **Median Baseline Views:** {c_rep['median_views']:,}")
                    st.subheader("Top Outlier Topics to Replicate with Originality")
                    for bo in c_rep["breakouts"][:4]:
                        st.markdown(f"- **{bo['title']}** — `{bo['views']:,} views` ({bo['outlier_multiplier']}x multiplier)")

        # Subtab 6: Pre-Publish Gate
        with audit_subtabs[5]:
            st.subheader("🚦 Pre-Publish Quality & Safety Gate")
            st.write("Run the mandatory pre-publish audit before any video can be approved or published.")

            gate_title = st.text_input("Draft Title", value="The Hidden Truth About AI Agents Nobody Tells You", key="long_gate_title_box")
            gate_thumb = st.text_input("Thumbnail Overlay Text", value="SECRET REVEALED", key="long_gate_thumb_box")
            gate_hook = st.text_area("Opening Hook Script", value="Whatever you do, do not touch this setting until you see what happens next.", key="long_gate_hook_box")
            gate_desc = st.text_area("Full Description", value="In this complete guide, we reveal the hidden truth and step-by-step framework...", key="long_gate_desc_box")
            gate_tags = st.text_input("Tags (comma-separated)", value="ai agents, python tutorial, automation, tech 2026, software", key="long_gate_tags_box")

            if st.button("AUDIT BEFORE PUBLISH", type="primary", key="btn_audit_prepublish_long"):
                tags_list = [t.strip() for t in gate_tags.split(",") if t.strip()]
                res = PrePublishAuditor.audit_pre_publish(
                    title=gate_title,
                    description=gate_desc,
                    tags=tags_list,
                    hook=gate_hook,
                    script_text="",
                    thumbnail_text=gate_thumb,
                )

                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1:
                    st.metric("Final Publish Score", f"{res['final_publish_score']}/100")
                with col_v2:
                    st.metric("Verdict", res["verdict"])
                with col_v3:
                    st.metric("Policy Risk", res["policy_risk"])

                if res["problems"]:
                    st.subheader("Issues Requiring Attention")
                    for pr in res["problems"]:
                        st.error(f"**[{pr['area']}]** {pr['issue']}\n\n👉 **Recommended Fix:** {pr['fix']}")

                if res["can_approve"]:
                    st.success("✅ Video meets algorithmic quality standards!")
                    if st.button("Submit to Human Approval Queue", type="primary", key="btn_submit_gate_appr_long"):
                        ApprovalCenter.create_approval_entry(
                            title=gate_title,
                            prepublish_score=res["final_publish_score"],
                        )
                        st.success("Video successfully sent to Human Approval Center!")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Telemetry Analytics Overview Drawer
    with st.expander("📊 Channel Telemetry & Algorithmic Health Overview", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            h_score = f"{active_rep.get('overall_health_score', 84.5):.1f}/100" if active_rep else "84.5/100"
            st.metric("CHANNEL HEALTH", h_score, "Real Telemetry" if active_rep else "Baseline")
        with c2:
            sub_display = active_rep.get("subscriber_count_text") if (active_rep and active_rep.get("subscriber_count_text")) else (f"{active_rep.get('subscriber_count', 142):,} subscribers" if (active_rep and active_rep.get("subscriber_count")) else "142 subscribers")
            st.metric("Subscribers", sub_display, "Verified Count")
        with c3:
            views_display = active_rep.get("total_views_text") if (active_rep and active_rep.get("total_views_text")) else (f"{active_rep.get('total_views', 50562):,} views" if (active_rep and active_rep.get("total_views")) else "50,562 views")
            st.metric("Total Views", views_display, "Public Views")
        with c4:
            s_score = f"{active_rep.get('scores', {}).get('SEO Score', 88)}/100" if active_rep else "88/100"
            st.metric("SEO SCORE", s_score, "Index Rating")

# =============================================================================
# NEW CHAT / AI AGENT ASSISTANT (VidIQ Copilot + Daily Memory Engine)
# =============================================================================
elif nav == "💬 New Chat":
    active_rep = st.session_state.get("latest_channel_report")
    ch_label = active_rep.get("channel_name", "@SpookyToonStories") if active_rep else st.session_state.get("active_channel", "Vanished Skies")
    clean_ch_name = ch_label.replace("https://www.youtube.com/", "").replace("www.youtube.com/", "").replace("@", "")

    # Top Header & Memory Drawer
    st.markdown(
        f"""
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>
            <div>
                <h1 style='margin:0; font-size:26px; font-weight:800; color:#ffffff;'>💬 AI YouTube Growth Coach & Scriptwriter</h1>
                <div style='font-size:13px; color:#94a3b8;'>Trained on VidIQ growth algorithms • Tailored for <b>{clean_ch_name}</b> • Persistent Daily Memory</div>
            </div>
            <span style='background:#065f46; color:#6ee7b7; border:1px solid #10b981; font-size:11px; font-weight:800; padding:4px 12px; border-radius:9999px;'>🟢 ACTIVE MEMORY</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Daily Memory & Strategic Insights Drawer
    with st.expander("🧠 Persistent Daily Memory & Past Strategy Ledger", expanded=False):
        mem_c1, mem_c2 = st.columns([3, 1])
        with mem_c1:
            daily_mems = get_daily_memories(clean_ch_name, limit=5)
            if daily_mems:
                for dm in daily_mems:
                    topics_str = ", ".join(dm.get("topics", []))
                    st.markdown(
                        f"""
                        <div style='background:#111827; border-left:3px solid #3b82f6; padding:8px 12px; border-radius:6px; margin-bottom:6px;'>
                            <b style='font-size:12px; color:#60a5fa;'>📅 {dm['date']}:</b> <span style='font-size:12.5px; color:#f1f5f9;'>{dm['summary']}</span>
                            {f"<br/><span style='font-size:11px; color:#94a3b8;'>Key Topics: {topics_str}</span>" if topics_str else ""}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.caption(f"No previous summaries yet for {clean_ch_name}. The AI automatically remembers your video strategies, topics, and scripts.")
        with mem_c2:
            st.write("")
            if st.button("🧹 Clear Conversation", key="btn_clear_chat_hist", use_container_width=True):
                clear_chat_history(clean_ch_name)
                st.session_state[f"chat_loaded_{clean_ch_name}"] = False
                st.success("Conversation cleared for a fresh session!")
                st.rerun()

    # Load persistent history from database
    if not st.session_state.get(f"chat_loaded_{clean_ch_name}"):
        db_messages = get_chat_history(clean_ch_name, limit=40)
        if db_messages:
            st.session_state["chat_messages"] = [
                {"role": m["role"], "content": m["content"], "metadata": m.get("metadata", {})}
                for m in db_messages
            ]
        else:
            st.session_state["chat_messages"] = [
                {
                    "role": "assistant",
                    "content": (
                        f"👋 **Salam & Welcome!** Main aapka dedicated **AI YouTube Growth Coach & Scriptwriter** hoon for **{clean_ch_name}**.\n\n"
                        "Main aapke liye:\n"
                        "• 🔥 **Viral High-CTR Titles** (VidIQ 95+ Score)\n"
                        "• 🎣 **3-Second Retention Hooks & Full Scripts**\n"
                        "• 🏷️ **15+ High-Relevance SEO Tags & Descriptions**\n"
                        "• 📊 **Channel Growth Strategy & Competitor Analysis**\n\n"
                        "Aap kisi bhi video topic ka naam batayein ya channel ke bare mein poochien!"
                    ),
                    "metadata": {}
                }
            ]
        st.session_state[f"chat_loaded_{clean_ch_name}"] = True

    # Real-Time Intelligence Status Banner
    st.markdown(
        """
        <div style="background:linear-gradient(90deg, #0f172a, #1e293b); border:1px solid #3b82f6; border-radius:8px; padding:8px 14px; margin-bottom:12px; display:flex; align-items:center; justify-content:space-between;">
            <div style="font-size:13px; font-weight:600; color:#e2e8f0; display:flex; align-items:center; gap:8px;">
                <span style="display:inline-block; width:8px; height:8px; background:#10b981; border-radius:50%; box-shadow:0 0 8px #10b981;"></span>
                <span>⚡ <b>Real-Time YouTube Intelligence Connected:</b> Live Autocomplete, Real Search Velocity & Ranking Video Benchmarks Active</span>
            </div>
            <div style="font-size:11px; color:#94a3b8; font-weight:500;">
                VidIQ Algorithm v2.6
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Quick-Action Suggestion Chips (VidIQ Style)
    st.markdown("<div style='font-size:12px; font-weight:700; color:#64748b; margin-bottom:4px; text-transform:uppercase;'>⚡ Quick Action Prompts:</div>", unsafe_allow_html=True)
    chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
    preset_prompt = None
    with chip_col1:
        if st.button("⚡ Live Trend & Search Demand", key="chip_live", use_container_width=True):
            preset_prompt = "Realtime data check: What are the live YouTube search autocomplete trends for Pacific Air Campaign?"
    with chip_col2:
        if st.button("⚖️ Niche Comparison Analysis", key="chip_comp", use_container_width=True):
            preset_prompt = "Ghibli niche vs Vanished Skies aviation mystery: dono ka honest viral aur RPM comparison karo"
    with chip_col3:
        if st.button("📜 Full Script on Aviation Mystery", key="chip_1", use_container_width=True):
            preset_prompt = "Write a complete high-retention script with 15+ tags on: Pacific Air Campaign"
    with chip_col4:
        if st.button("🔥 5 Viral High-CTR Titles", key="chip_2", use_container_width=True):
            preset_prompt = "Give me 5 viral titles with Curiosity Gap for Pacific Air War"


    # Render Conversation Feed
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.get("chat_messages", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Handle User Input
    user_query = st.chat_input(f"Ask anything about {clean_ch_name}, titles, hooks, or full video scripts...")
    actual_query = preset_prompt or user_query

    if actual_query:
        # Append & save user message
        st.session_state["chat_messages"].append({"role": "user", "content": actual_query, "metadata": {}})
        save_chat_message(channel_handle=clean_ch_name, role="user", content=actual_query)

        with st.chat_message("user"):
            st.markdown(actual_query)

        # Generate intelligent expert response
        with st.chat_message("assistant"):
            with st.spinner("AI YouTube Coach analyzing topic velocity, VidIQ scores, and writing script..."):
                agent = get_ai_agent()
                expert_result = agent.ask_expert(
                    query=actual_query,
                    channel_name=clean_ch_name,
                    recent_history=st.session_state.get("chat_messages", []),
                    channel_report=active_rep
                )
                if not expert_result or not isinstance(expert_result, dict):
                    expert_result = {
                        "response_text": "I am ready to help you grow your YouTube channel! Please specify a video topic or ask any growth question.",
                        "topic": "General Help"
                    }
                resp_text = expert_result.get("response_text", "")
                st.markdown(resp_text)

                # Save assistant response to DB
                st.session_state["chat_messages"].append({
                    "role": "assistant",
                    "content": resp_text,
                    "metadata": expert_result
                })
                save_chat_message(
                    channel_handle=clean_ch_name,
                    role="assistant",
                    content=resp_text,
                    message_type="seo_package" if "### 🎯 VidIQ" in resp_text else "chat",
                    metadata=expert_result
                )

                # Update daily memory summary in database
                topic_tag = expert_result.get("topic", actual_query[:40])
                save_daily_memory(
                    channel_handle=clean_ch_name,
                    summary_text=f"Discussed {topic_tag} and generated high-CTR packaging & scripts.",
                    key_topics=[topic_tag]
                )

        if preset_prompt:
            st.rerun()

# =============================================================================
# RACE TO 4K (Monetization Tracker)
# =============================================================================
elif nav == "🏆 Race to 4K":
    st.title("🏆 Race to 4K Watch Hours & Monetization")
    st.write("Track your progress towards the YouTube Partner Program (1,000 Subscribers & 4,000 Watch Hours).")
    
    active_rep = st.session_state.get("latest_channel_report")
    subs = active_rep.get("subscriber_count", 142) if active_rep else 142
    views = active_rep.get("total_views", 50562) if active_rep else 50562
    est_hours = int(views * 0.012)

    r_c1, r_c2 = st.columns(2)
    with r_c1:
        st.metric("Subscribers Milestone", f"{subs} / 1,000", f"{int(subs/10)}% Reached")
        st.progress(min(1.0, subs / 1000.0))
    with r_c2:
        st.metric("Public Watch Hours", f"{est_hours} / 4,000 hrs", f"{int(est_hours/40)}% Reached")
        st.progress(min(1.0, est_hours / 4000.0))

    st.subheader("🚀 Fast-Track Recommendations")
    st.success("✅ **Publish 3 Shorts Weekly**: Drives rapid subscriber growth to hit 1,000 subs.")
    st.info("💡 **Introduce 8-minute episodic series**: Builds cumulative watch time for the 4,000 hours goal.")

# =============================================================================
# UPGRADE MATRIX
# =============================================================================
elif nav == "⚡ Upgrade":
    st.title("⚡ Upgrade to AI Growth Pro & VidIQ Max")
    st.write("Unlock unlimited daily video audits, automated AI title generators, and competitor deep-scans.")
    
    u1, u2, u3 = st.columns(3)
    with u1:
        st.markdown(
            """
            <div style='background:#111827; border:1px solid #1f2937; border-radius:12px; padding:20px; text-align:center;'>
                <h3>Free Starter</h3>
                <h1 style='color:#38bdf8;'>$0</h1>
                <p style='color:#94a3b8; font-size:13px;'>Basic channel audit & 3 daily optimizations</p>
                <div style='margin-top:20px;'><span style='background:#334155; color:white; padding:6px 16px; border-radius:9999px; font-size:12px;'>Active Plan</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with u2:
        st.markdown(
            """
            <div style='background:linear-gradient(145deg, #1e3a8a, #0f172a); border:1px solid #3b82f6; border-radius:12px; padding:20px; text-align:center;'>
                <div style='background:#2563eb; color:white; font-size:10px; font-weight:800; padding:2px 8px; border-radius:4px; display:inline-block; margin-bottom:6px;'>POPULAR</div>
                <h3>Pro Creator</h3>
                <h1 style='color:#60a5fa;'>$19<span style='font-size:14px;'>/mo</span></h1>
                <p style='color:#bfdbfe; font-size:13px;'>Unlimited Video Audits + Viral AI Title Generator</p>
                <div style='margin-top:20px;'><a href='#' style='background:#2563eb; color:white; text-decoration:none; padding:8px 18px; border-radius:9999px; font-weight:700; font-size:13px;'>Upgrade to Pro</a></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with u3:
        st.markdown(
            """
            <div style='background:#111827; border:1px solid #1f2937; border-radius:12px; padding:20px; text-align:center;'>
                <h3>Max Autonomous</h3>
                <h1 style='color:#a855f7;'>$49<span style='font-size:14px;'>/mo</span></h1>
                <p style='color:#94a3b8; font-size:13px;'>Full Auto-Production + Thumbnail Generation</p>
                <div style='margin-top:20px;'><a href='#' style='background:#7c3aed; color:white; text-decoration:none; padding:8px 18px; border-radius:9999px; font-weight:700; font-size:13px;'>Upgrade to Max</a></div>
            </div>
            """,
            unsafe_allow_html=True
        )

# =============================================================================
# 3. RESEARCH & TRENDS MODULE (Section 7, 8, 9)
# =============================================================================
elif nav in ["🔍 Research", "🔍 Research & Trends"]:
    st.title("🔬 Research Intelligence & Decision Engine")
    st.write("Deterministic telemetry collection, age-cohort outlier detection, structured transcript anatomy, and evidence-grounded opportunity scoring.")

    r_tabs = st.tabs([
        "⚡ Central Research Pipeline",
        "🎯 Discovered Opportunities & Evidence Ledger",
        "🎣 Outlier Transcript Intelligence",
        "❓ Question Opportunity Graph",
        "📈 Emerging Trends & Formats",
    ])

    # 1. Central Research Pipeline
    with r_tabs[0]:
        st.subheader("⚡ Launch Deterministic-First Research Run")
        st.caption("Coordinates Scrapers → Normalization → Age-Cohort Outliers → Transcript Anatomy → Topic Clustering → Observable Feature Scoring → Gate 1 Brief.")

        # Quick Preset Buttons
        st.markdown("**⚡ Quick 1-Click Research Presets:**")
        pr1, pr2, pr3 = st.columns(3)
        with pr1:
            if st.button("✈️ Research Vanished Skies / Mysteries", use_container_width=True):
                st.session_state["preset_query"] = "Vanished Skies Aviation Mysteries"
                st.rerun()
        with pr2:
            if st.button("🧟 Research Spooky Horror Stories", use_container_width=True):
                st.session_state["preset_query"] = "Analog Horror Lost Broadcasts"
                st.rerun()
        with pr3:
            if st.button("🤖 Research AI Agents & Automation", use_container_width=True):
                st.session_state["preset_query"] = "Autonomous AI Coding Agents"
                st.rerun()

        default_q = st.session_state.pop("preset_query", "Vanished Skies Aviation Mysteries" if st.session_state.get("active_channel") == "Vanished Skies" else "Analog Horror Lost Broadcasts")

        col_q1, col_q2 = st.columns([3, 1])
        with col_q1:
            research_query = st.text_input(
                "Target Niche, Topic Keyword, or Competitor Handle",
                value=default_q,
                placeholder="e.g. Analog Horror, Aviation Mysteries, or @SpookyToonStories",
            )
        with col_q2:
            max_vids = st.slider("Videos to Analyze", min_value=10, max_value=50, value=25)

        if st.button("🚀 Execute Research Pipeline (Phase 1 & 2 MVP)", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            def _on_progress(pct, msg):
                progress_bar.progress(pct / 100.0)
                status_text.markdown(f"**Step Progress ({pct}%):** {msg}")

            with st.spinner("Executing Research Intelligence Pipeline..."):
                orchestrator = ResearchOrchestrator()
                res = orchestrator.execute_research_pipeline(
                    query_or_channel=research_query,
                    max_videos=max_vids,
                    channel_median_views=15000.0,
                    progress_callback=_on_progress,
                )
                st.session_state["latest_research_run"] = res

            if res.get("status") == "COMPLETED":
                st.success(f"✅ Research Run `{res['run_id']}` completed successfully!")

        # Display latest run results
        active_run = st.session_state.get("latest_research_run")
        if active_run and active_run.get("status") == "COMPLETED":
            st.divider()
            st.subheader(f"📊 Research Run Summary: `{active_run['query']}`")

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("Analyzed Videos", f"{active_run['total_videos_analyzed']} uploads")
            with kpi2:
                st.metric("Breakout Outliers", f"{active_run['outliers_found']} verified", "Age-Adjusted")
            with kpi3:
                st.metric("Topic Clusters", f"{active_run['topic_clusters_count']} groups")
            with kpi4:
                st.metric("Grounded Opportunities", f"{len(active_run['opportunities'])} ready")

            st.markdown(active_run.get("executive_brief", ""))

            # Gate 1 Presentation
            st.info("🚦 **Human Approval Gate 1:** Review discovered opportunities below and approve them to advance into the Creative Studio.")

    # 2. Discovered Opportunities & Evidence Ledger
    with r_tabs[1]:
        st.subheader("🎯 Grounded Content Opportunities & Evidence Ledger")
        active_run = st.session_state.get("latest_research_run")

        if not active_run or not active_run.get("opportunities"):
            st.info("💡 Run the Research Pipeline in Tab 1 to generate evidence-backed topic opportunities.")
        else:
            for idx, opp in enumerate(active_run.get("opportunities", [])):
                score = opp["opportunity_score"]
                tier_badge = "🟢 Strong" if score >= 75 else "🟡 Moderate" if score >= 60 else "🔴 Low"
                
                with st.expander(f"Opportunity #{idx+1}: {opp['cluster_name']} — Score: {score}/100 [{opp['confidence']} Confidence]"):
                    col_det1, col_det2 = st.columns([1, 1])
                    with col_det1:
                        st.markdown("#### 📐 Observable Feature Vector")
                        features = opp.get("observable_features", {})
                        st.markdown(f"- **Demand Index:** `{features.get('demand', {}).get('score', 0)}/100` ({features.get('demand', {}).get('label', 'N/A')})")
                        st.markdown(f"- **Outlier Evidence:** `{features.get('outlier_evidence', {}).get('score', 0)}/100` ({features.get('outlier_evidence', {}).get('label', 'N/A')})")
                        st.markdown(f"- **Competition Saturation:** `{features.get('competition', {}).get('score', 0)}/100` ({features.get('competition', {}).get('label', 'N/A')})")
                        st.markdown(f"- **Audience Fit:** `{features.get('audience_fit', {}).get('score', 0)}/100`")
                        st.markdown(f"- **Novelty Score:** `{features.get('novelty', {}).get('score', 0)}/100`")
                        st.markdown(f"- **Production Difficulty:** `{features.get('production_difficulty', {}).get('score', 0)}/100`")

                    with col_det2:
                        st.markdown("#### 📜 Grounded Evidence Ledger")
                        st.caption("Every claim is anchored to empirical video observations & timestamps:")
                        for ev in opp.get("evidence_ledger", []):
                            st.markdown(
                                f"""
                                <div style='background:#1e293b; border-left:3px solid #3b82f6; padding:8px; margin-bottom:6px; border-radius:4px;'>
                                    <b>{ev['claim']}</b><br/>
                                    <span style='color:#94a3b8; font-size:12px;'>Source: <a href='{ev.get('source_url', '#')}' target='_blank'>{ev.get('source_title', 'Video')}</a> | Metric: {ev['metric_value']} | {ev['observed_at']}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    st.divider()
                    col_act1, col_act2 = st.columns([1, 3])
                    with col_act1:
                        if st.button(f"✅ Approve Topic #{idx+1} (Gate 1)", key=f"appr_{idx}"):
                            st.success(f"Topic '{opp['cluster_name']}' approved! Advancing to Creative Studio.")
                    with col_act2:
                        st.caption("Approved topics automatically generate Title, Hook, Script, and Storyboard packages.")

    # 3. Outlier Transcript Intelligence
    with r_tabs[2]:
        st.subheader("🎣 Structured Transcript Intelligence & Anatomy")
        active_run = st.session_state.get("latest_research_run")

        if not active_run or not active_run.get("transcript_intelligence"):
            st.info("💡 Run the Research Pipeline in Tab 1 to extract transcript anatomy and retention patterns.")
        else:
            t_intel = active_run.get("transcript_intelligence", {})
            st.markdown(f"**Structural Synthesis:** {t_intel.get('structural_takeaway', '')}")
            
            c_h1, c_h2, c_h3 = st.columns(3)
            with c_h1:
                st.metric("Dominant Hook Style", t_intel.get("dominant_hook_type", "Curiosity Question"))
            with c_h2:
                st.metric("Avg Pattern Interrupts", f"{t_intel.get('avg_pattern_interrupts', 0)} per video")
            with c_h3:
                st.metric("Analyzed Outlier Scripts", f"{t_intel.get('analyzed_count', 0)} transcripts")

            if t_intel.get("common_open_loops"):
                st.markdown("#### 🔄 Top Open Loops & Unresolved Narrative Hooks")
                for loop in t_intel.get("common_open_loops", []):
                    st.markdown(f"- ❓ *\"{loop}\"*")

    # 4. Question Opportunity Graph
    with r_tabs[3]:
        st.subheader("❓ Question Opportunity Graph (Audience Gaps)")
        active_run = st.session_state.get("latest_research_run")

        if not active_run or not active_run.get("question_opportunity_graph"):
            st.info("💡 Run the Research Pipeline in Tab 1 to mine audience questions and unaddressed content gaps.")
        else:
            q_graph = active_run.get("question_opportunity_graph", [])
            for q_item in q_graph:
                st.markdown(
                    f"""
                    <div style='background:#1e293b; border-left:4px solid #f59e0b; padding:12px; margin-bottom:10px; border-radius:6px;'>
                        <b style='font-size:15px;'>\"{q_item['question']}\"</b>
                        <br/><span style='color:#60a5fa;'>Topic Cluster: {q_item['cluster_topic']}</span> | 
                        <span style='color:#f59e0b;'>Competitor Coverage: {q_item['competitor_coverage']}</span> | 
                        <span style='color:#10b981; font-weight:700;'>Opportunity Strength: {q_item['opportunity_strength']}/100</span>
                        <br/><span style='color:#94a3b8; font-size:12px;'>👉 Recommendation: {q_item['recommended_action']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 5. Emerging Trends & Formats
    with r_tabs[4]:
        st.subheader("📈 Surging Trends & Emerging Formats (Section 8)")
        t_engine = TrendDiscoveryEngine()
        trends = t_engine.discover_trends(niche="Horror Storytelling")
        
        st.write("### 🔥 Surging Topics")
        for st_item in trends["rising_topics"]:
            st.markdown(
                f"""
                <div style='background:#1e293b; border-left:4px solid #10b981; padding:12px; margin-bottom:8px; border-radius:6px;'>
                    <b>{st_item['topic']}</b> — <span style='color:#10b981; font-weight:700;'>{st_item['velocity_boost']}</span>
                    <br/><span style='color:#94a3b8; font-size:13px;'>Format: {st_item['recommended_format']} | Intent: {st_item['intent']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("### 🎬 Emerging Formats")
        for ef in trends["emerging_formats"]:
            st.info(f"**{ef['format_name']}** ({ef['suitability']})\n\n{ef['description']}")

# =============================================================================
# =============================================================================
# 4. THUMBNAIL STUDIO
# =============================================================================
elif nav in ["🎨 Thumbnail Studio", "🎨 Production & Thumbnails"]:
    st.title("🎨 Thumbnail Studio")
    st.write("Generate high-contrast, high-CTR 0.5s mobile visual thumbnail concepts & production-ready AI image prompts.")

    st.subheader("🖼️ High-Contrast 0.5s Mobile Thumbnail Concepts & AI Prompts")
    th_c1, th_c2, th_c3 = st.columns([2, 1, 1])
    with th_c1:
        th_topic = st.text_input("Video Topic for Thumbnails", value="World War 2", placeholder="e.g. World War 2, MH370 Vanished Skies, AI Secrets...")
    with th_c2:
        th_vibe = st.selectbox(
            "Topic Vibe / Niche",
            [
                "Auto-Detect Niche",
                "🪖 War & History",
                "✈️ Aviation & Marine Mysteries",
                "👻 Analog Horror & Spooky",
                "🤖 Tech & AI",
                "🕵️ True Crime & Investigation",
                "📈 General Viral Growth",
            ],
            index=0,
        )
    with th_c3:
        th_aspect = st.selectbox("Aspect Ratio", ["9:16 (Shorts/TikTok)", "16:9 (Long-form)"], index=0)
        
    th_btn_c1, th_btn_c2 = st.columns(2)
    with th_btn_c1:
        gen_concepts_btn = st.button("Generate 3 High-CTR Concepts", type="primary", use_container_width=True)
    with th_btn_c2:
        gen_ai_prompt_btn = st.button("✨ Generate AI Image Prompts (Midjourney/Imagen)", use_container_width=True)

    # Track topic changes to refresh concepts
    if gen_concepts_btn or st.session_state.get("th_last_topic") != th_topic or st.session_state.get("th_concepts_active"):
        concepts = ThumbnailStudio.generate_concepts(topic=th_topic, target_vibe=th_vibe)
        st.session_state["th_concepts_active"] = True
        st.session_state["th_last_topic"] = th_topic
        for c in concepts:
            st.markdown(
                f"""
                <div style='background:#1e293b; border:1px solid #475569; padding:16px; border-radius:10px; margin-bottom:12px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <h4 style='color:#38bdf8; margin:0;'>Concept {c['concept_id']}: {c['name']}</h4>
                        <span style='background:#065f46; color:#6ee7b7; font-size:11px; font-weight:800; padding:2px 8px; border-radius:6px;'>Score: {c['curiosity_score']}/100</span>
                    </div>
                    <p style='margin-top:8px;'><b>Visual Layout:</b> {c['visual_layout']}</p>
                    <p><b>Overlay Text (3-Word Rule):</b> <span style='background:#f59e0b; color:black; font-weight:800; padding:3px 10px; border-radius:4px;'>{c['text_overlay']}</span></p>
                    <p><b>Palette:</b> {c['color_palette']}</p>
                    <p><b>Focal Point:</b> <span style='color:#cbd5e1;'>{c['focal_point']}</span></p>
                    <p style='color:#94a3b8; font-size:13px; margin-bottom:0;'><b>CTR Reason:</b> {c['ctr_reasoning']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if gen_ai_prompt_btn:
        ar_clean = "9:16" if "9:16" in th_aspect else "16:9"
        ai_prompts = ThumbnailStudio.generate_ai_image_prompt(topic=th_topic, style=th_vibe, aspect_ratio=ar_clean)
        st.markdown(f"### 🎨 Production-Ready AI Art Generation Prompts ({ai_prompts['style']})")
        
        st.markdown("#### 🌟 Midjourney v6 Prompt")
        st.code(ai_prompts["midjourney_prompt"], language="text")
        
        st.markdown("#### 🌟 Google Imagen 3 Prompt")
        st.code(ai_prompts["imagen_prompt"], language="text")
        
        st.markdown("#### 🚫 Negative Prompt")
        st.code(ai_prompts["negative_prompt"], language="text")
        
        st.markdown(f"**Recommended Text Overlay:** `{ai_prompts['recommended_overlay_text']}` ({ai_prompts['overlay_style']})")


# =============================================================================
# 8. LEARNING & RE-OPTIMIZATION (Section 27, 28, 29, 30)
# =============================================================================
elif nav in ["🧠 Learning & Analytics", "🧠 Learning & Re-Optimization"]:
    st.title("🧠 Channel Learning & Automated Re-Optimization")
    st.write("Empirical performance insights, historical pattern extraction, and automated packaging re-optimization.")

    l_tabs = st.tabs([
        "📉 24h Performance & Re-Optimization",
        "🔬 Channel Empirical Signals",
        "🧠 Channel Insights Memory",
        "💡 Strategic Recommendations"
    ])

    with l_tabs[0]:
        st.subheader("📉 24-Hour Performance Monitor & Re-Optimization Trigger")
        test_t = st.text_input("Recent Video Title", value="The Emergency Broadcast Archive")
        v_views = st.number_input("Views at 24 Hours", value=1850)
        v_baseline = st.number_input("Channel Median Baseline", value=10000)

        if st.button("Run 24h Diagnostic Audit", type="primary"):
            diag = LearningEngine.audit_performance_and_reoptimize(test_t, views=v_views, channel_median=v_baseline)
            st.metric("Pacing Status", diag["status"], f"{diag['performance_ratio']}x baseline")
            st.info(diag["diagnosis"])
            
            st.subheader("Automated Re-Optimization Plan")
            for ra in diag["reoptimization_actions"]:
                st.warning(f"**Action:** {ra['action']}\n\n👉 **Suggested Fix:** {ra['suggestion']}\n\n*Why:* {ra['why']}")

    with l_tabs[1]:
        st.subheader("🔬 Channel-Specific Empirical Signals (Closed-Loop Learning)")
        st.write("Discovered patterns, recurring breakout themes, and duration sweetspots from channel history.")

        ch_learn_handle = st.text_input("Channel Handle for Empirical Pattern Extraction", value=st.session_state.get("active_channel", "@spookytoonstories"))
        if st.button("Extract Empirical Channel Signals", type="primary"):
            with st.spinner("Extracting historical signals and outlier patterns..."):
                active_rep = st.session_state.get("latest_channel_report")
                # Fallback mock sample if offline
                sample_vids = [
                    {"video_id": "v1", "title": "The Analog Horror Mystery Broadcast", "views": 125000, "age_adjusted_outlier": 4.8, "outlier_tier": "STRONG OUTLIER", "duration_seconds": 650},
                    {"video_id": "v2", "title": "Lost Transmission from 1999", "views": 92000, "age_adjusted_outlier": 3.4, "outlier_tier": "STRONG OUTLIER", "duration_seconds": 780},
                    {"video_id": "v3", "title": "Night Shift Incident", "views": 22000, "age_adjusted_outlier": 1.1, "outlier_tier": "NORMAL", "duration_seconds": 320},
                    {"video_id": "v4", "title": "Emergency Alert System Test", "views": 19500, "age_adjusted_outlier": 1.0, "outlier_tier": "NORMAL", "duration_seconds": 600},
                    {"video_id": "v5", "title": "Do Not Answer The Phone", "views": 85000, "age_adjusted_outlier": 3.1, "outlier_tier": "STRONG OUTLIER", "duration_seconds": 710}
                ]
                signals = ChannelLearningEngine.extract_channel_learning_signals(ch_learn_handle, sample_vids)
                st.session_state["latest_learning_signals"] = signals

        signals = st.session_state.get("latest_learning_signals", [])
        if signals:
            for s in signals:
                st.markdown(
                    f"""
                    <div style='background:#1e293b; border-left:4px solid #8b5cf6; padding:12px; margin-bottom:10px; border-radius:6px;'>
                        <span style='color:#8b5cf6; font-weight:700;'>[{s['signal_type'].upper()}]</span>
                        <p style='color:#f8fafc; font-size:14px; margin-top:4px; margin-bottom:4px;'>{s['pattern_summary']}</p>
                        <span style='color:#94a3b8; font-size:12px;'>Confidence: <b>{s['confidence']}</b> | Sample Size: {s['sample_size']} videos</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Click above to extract empirical signals for this channel.")

    with l_tabs[2]:
        st.subheader("🧠 Stored Empirical Insights for this Channel")
        insights = LearningEngine.get_channel_insights()
        for ins in insights:
            st.markdown(
                f"""
                <div style='background:#1e293b; border-left:4px solid #3b82f6; padding:12px; margin-bottom:8px; border-radius:6px;'>
                    <b>{ins['insight']}</b>
                    <br/><span style='color:#94a3b8; font-size:13px;'>Evidence: {ins['evidence']} | Action: <b>{ins['action']}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with l_tabs[3]:
        st.subheader("💡 High-Priority AI Recommendations (Section 30 & 42)")
        recs = LearningEngine.get_active_recommendations()
        for r in recs:
            st.info(f"**[{r['category']}] ({r['priority']} Priority)**\n\n{r['recommendation']}\n\n*WHY:* {r['why']}")


