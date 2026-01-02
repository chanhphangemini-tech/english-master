# Re-export everything to maintain compatibility
from core.database import supabase
from services.user_service import get_user_stats, log_activity, process_daily_streak
from services.vocab_service import (
    load_progress, load_vocab_data, get_due_vocabulary, update_srs_stats,
    add_word_to_srs, mark_learned, remove_word_from_srs, get_daily_learning_batch,
    bulk_master_levels, get_irregular_verbs_list, add_word_to_srs_and_prioritize,
    get_user_level_progress, load_all_vocabulary, get_vocabulary_topics, get_vocabulary_levels,
    get_total_vocabulary_count
)
from services.shop_service import (
    get_shop_items, get_user_inventory, buy_shop_item, activate_user_theme,
    check_and_use_freeze_streak, use_item
)
from services.game_service import (
    save_mock_test_result, create_pvp_challenge, get_open_challenges,
    join_pvp_challenge, submit_pvp_score, get_all_pvp_challenges,
    get_leaderboard_english
)
from services.admin_service import get_all_users, get_system_analytics
from services.grammar_service import *
from services.quest_service import generate_daily_quests
from services.chat_service import (
    get_chat_sessions, get_chat_messages, create_chat_session, add_chat_message
)
