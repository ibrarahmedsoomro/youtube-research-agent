"""
Unit tests for Multi-Account YouTube OAuth and Channel Management.
"""

import os
import pytest
from database.db import (
    init_db,
    save_or_update_connected_account,
    get_connected_accounts,
    get_active_account,
    set_active_account,
    delete_connected_account,
)
from operations.youtube_auth import YouTubeAuthManager

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

class TestMultiAccountAuth:
    def test_save_and_switch_accounts(self):
        # Save Account 1
        acc1 = save_or_update_connected_account(
            channel_id="UC_TEST_01",
            channel_handle="@ChannelOne",
            channel_name="Channel One",
            email="one@example.com",
            subscriber_count=5000,
            video_count=10,
            set_active=True,
        )
        assert acc1 is not None

        # Save Account 2
        acc2 = save_or_update_connected_account(
            channel_id="UC_TEST_02",
            channel_handle="@ChannelTwo",
            channel_name="Channel Two",
            email="two@example.com",
            subscriber_count=15000,
            video_count=25,
            set_active=True,
        )
        assert acc2 is not None

        # Active should now be Account 2
        active = get_active_account()
        assert active["channel_handle"] == "@ChannelTwo"

        # Switch back to Account 1
        switched = set_active_account("@ChannelOne")
        assert switched is True
        active = get_active_account()
        assert active["channel_handle"] == "@ChannelOne"

        # List accounts
        all_accs = get_connected_accounts()
        handles = [a["channel_handle"] for a in all_accs]
        assert "@ChannelOne" in handles
        assert "@ChannelTwo" in handles

    def test_auth_manager_instance(self):
        auth_mgr = YouTubeAuthManager()
        accounts = auth_mgr.list_accounts()
        assert len(accounts) > 0
        active = auth_mgr.get_current_active()
        assert active is not None
