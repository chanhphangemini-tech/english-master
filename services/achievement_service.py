"""
Achievement Service - Long-term Achievements System
Hệ thống achievements dài hạn để tạo mục tiêu lớn cho người dùng
"""
import streamlit as st
from core.database import supabase
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from core.timezone_utils import get_vn_now_utc

logger = logging.getLogger(__name__)

# Achievement Definitions
ACHIEVEMENT_DEFINITIONS = {
    # Vocabulary Achievements
    'vocab_100': {'type': 'vocab', 'target': 100, 'name': 'Bước đầu tiên', 'description': 'Học 100 từ vựng', 'reward_coins': 100, 'icon': '🌱'},
    'vocab_500': {'type': 'vocab', 'target': 500, 'name': 'Mọt sách', 'description': 'Học 500 từ vựng', 'reward_coins': 500, 'icon': '🐛'},
    'vocab_1000': {'type': 'vocab', 'target': 1000, 'name': 'Thông thái', 'description': 'Học 1000 từ vựng', 'reward_coins': 1000, 'icon': '🦉'},
    'vocab_2000': {'type': 'vocab', 'target': 2000, 'name': 'Từ điển sống', 'description': 'Học 2000 từ vựng', 'reward_coins': 2000, 'icon': '📘'},
    'vocab_5000': {'type': 'vocab', 'target': 5000, 'name': 'Vua tiếng Anh', 'description': 'Học 5000 từ vựng', 'reward_coins': 5000, 'icon': '👑'},
    
    # Skill Achievements (per skill type)
    'skill_listening_50': {'type': 'skill', 'target': 50, 'name': 'Nghe giỏi', 'description': 'Hoàn thành 50 bài nghe', 'reward_coins': 200, 'icon': '👂', 'skill': 'listening'},
    'skill_listening_100': {'type': 'skill', 'target': 100, 'name': 'Thính giác siêu phàm', 'description': 'Hoàn thành 100 bài nghe', 'reward_coins': 500, 'icon': '👂', 'skill': 'listening'},
    'skill_speaking_50': {'type': 'skill', 'target': 50, 'name': 'Nói giỏi', 'description': 'Hoàn thành 50 bài nói', 'reward_coins': 200, 'icon': '💬', 'skill': 'speaking'},
    'skill_speaking_100': {'type': 'skill', 'target': 100, 'name': 'Hùng biện', 'description': 'Hoàn thành 100 bài nói', 'reward_coins': 500, 'icon': '💬', 'skill': 'speaking'},
    'skill_reading_50': {'type': 'skill', 'target': 50, 'name': 'Đọc giỏi', 'description': 'Hoàn thành 50 bài đọc', 'reward_coins': 200, 'icon': '📄', 'skill': 'reading'},
    'skill_reading_100': {'type': 'skill', 'target': 100, 'name': 'Đọc thông thạo', 'description': 'Hoàn thành 100 bài đọc', 'reward_coins': 500, 'icon': '📄', 'skill': 'reading'},
    'skill_writing_50': {'type': 'skill', 'target': 50, 'name': 'Viết giỏi', 'description': 'Hoàn thành 50 bài viết', 'reward_coins': 200, 'icon': '✏️', 'skill': 'writing'},
    'skill_writing_100': {'type': 'skill', 'target': 100, 'name': 'Nhà văn', 'description': 'Hoàn thành 100 bài viết', 'reward_coins': 500, 'icon': '✏️', 'skill': 'writing'},
    
    # Grammar Achievements (per level)
    'grammar_A1_complete': {'type': 'grammar', 'target': 1, 'name': 'Ngữ pháp A1', 'description': 'Hoàn thành tất cả bài ngữ pháp A1', 'reward_coins': 300, 'icon': '📝', 'level': 'A1'},
    'grammar_A2_complete': {'type': 'grammar', 'target': 1, 'name': 'Ngữ pháp A2', 'description': 'Hoàn thành tất cả bài ngữ pháp A2', 'reward_coins': 400, 'icon': '📝', 'level': 'A2'},
    'grammar_B1_complete': {'type': 'grammar', 'target': 1, 'name': 'Ngữ pháp B1', 'description': 'Hoàn thành tất cả bài ngữ pháp B1', 'reward_coins': 500, 'icon': '📝', 'level': 'B1'},
    'grammar_B2_complete': {'type': 'grammar', 'target': 1, 'name': 'Ngữ pháp B2', 'description': 'Hoàn thành tất cả bài ngữ pháp B2', 'reward_coins': 600, 'icon': '📝', 'level': 'B2'},
    'grammar_C1_complete': {'type': 'grammar', 'target': 1, 'name': 'Ngữ pháp C1', 'description': 'Hoàn thành tất cả bài ngữ pháp C1', 'reward_coins': 800, 'icon': '📝', 'level': 'C1'},
    'grammar_C2_complete': {'type': 'grammar', 'target': 1, 'name': 'Ngữ pháp C2', 'description': 'Hoàn thành tất cả bài ngữ pháp C2', 'reward_coins': 1000, 'icon': '📝', 'level': 'C2'},
    
    # PvP Achievements
    'pvp_10': {'type': 'pvp', 'target': 10, 'name': 'Chiến tướng', 'description': 'Thắng 10 trận PvP', 'reward_coins': 500, 'icon': '⚔️'},
    'pvp_50': {'type': 'pvp', 'target': 50, 'name': 'Thần chiến tranh', 'description': 'Thắng 50 trận PvP', 'reward_coins': 2000, 'icon': '👹'},
    'pvp_100': {'type': 'pvp', 'target': 100, 'name': 'Độc cô cầu bại', 'description': 'Thắng 100 trận PvP', 'reward_coins': 5000, 'icon': '☠️'},
    
    # Quest Achievements
    'quest_100': {'type': 'quest', 'target': 100, 'name': 'Nhiệm vụ chăm chỉ', 'description': 'Hoàn thành 100 quests', 'reward_coins': 1000, 'icon': '📜'},
    'quest_500': {'type': 'quest', 'target': 500, 'name': 'Nhiệm vụ kiên trì', 'description': 'Hoàn thành 500 quests', 'reward_coins': 3000, 'icon': '📚'},
    'quest_1000': {'type': 'quest', 'target': 1000, 'name': 'Nhiệm vụ huyền thoại', 'description': 'Hoàn thành 1000 quests', 'reward_coins': 8000, 'icon': '🏆'},
}


def check_achievements(user_id: int, achievement_type: str, current_value: int) -> List[Dict]:
    """
    Check and award achievements for a specific type.
    
    Args:
        user_id: User ID
        achievement_type: Type of achievement ('vocab', 'streak', 'skill', 'grammar', 'pvp', 'quest')
        current_value: Current value (e.g., vocab count, streak days, pvp wins)
    
    Returns:
        List of newly achieved achievements
    """
    if not supabase or not user_id:
        return []
    
    try:
        # Get all achievements for this type
        type_achievements = {k: v for k, v in ACHIEVEMENT_DEFINITIONS.items() if v['type'] == achievement_type}
        
        # Get already achieved/started achievements for this user and type
        existing_res = supabase.table("Achievements")\
            .select("achievement_key, achieved_at, progress")\
            .eq("user_id", user_id)\
            .eq("achievement_type", achievement_type)\
            .execute()
        
        existing_keys = {}
        if existing_res.data:
            for ach in existing_res.data:
                existing_keys[ach['achievement_key']] = {
                    'achieved': ach.get('achieved_at') is not None,
                    'progress': ach.get('progress', 0)
                }
        
        # Check which achievements should be achieved/updated
        new_achievements = []
        for key, definition in type_achievements.items():
            target = definition['target']
            
            # Check if already achieved
            if existing_keys.get(key, {}).get('achieved', False):
                continue
            
            # Check if current value meets target
            if current_value >= target:
                # Award achievement
                success, achievement_data = award_achievement(
                    user_id=user_id,
                    achievement_key=key,
                    achievement_type=achievement_type,
                    definition=definition,
                    current_value=current_value
                )
                
                if success:
                    new_achievements.append(achievement_data)
            else:
                # Update progress (if not achieved yet)
                update_achievement_progress(
                    user_id=user_id,
                    achievement_key=key,
                    achievement_type=achievement_type,
                    current_value=current_value,
                    target=target
                )
        
        return new_achievements
    
    except Exception as e:
        logger.error(f"Error checking achievements: {e}")
        return []


def check_skill_achievements(user_id: int, skill_type: str, current_count: int) -> List[Dict]:
    """
    Check achievements for a specific skill type.
    
    Args:
        user_id: User ID
        skill_type: Skill type ('listening', 'speaking', 'reading', 'writing')
        current_count: Current exercise count for this skill
    
    Returns:
        List of newly achieved achievements
    """
    # Filter achievements for this skill
    skill_achievements = {
        k: v for k, v in ACHIEVEMENT_DEFINITIONS.items()
        if v.get('type') == 'skill' and v.get('skill') == skill_type
    }
    
    if not skill_achievements:
        return []
    
    try:
        # Get existing achievements
        existing_res = supabase.table("Achievements")\
            .select("achievement_key, achieved_at")\
            .eq("user_id", user_id)\
            .eq("achievement_type", "skill")\
            .like("achievement_key", f"skill_{skill_type}_%")\
            .execute()
        
        existing_keys = {ach['achievement_key']: ach.get('achieved_at') is not None for ach in (existing_res.data or [])}
        
        new_achievements = []
        for key, definition in skill_achievements.items():
            if existing_keys.get(key, False):
                continue
            
            target = definition['target']
            if current_count >= target:
                success, achievement_data = award_achievement(
                    user_id=user_id,
                    achievement_key=key,
                    achievement_type='skill',
                    definition=definition,
                    current_value=current_count
                )
                
                if success:
                    new_achievements.append(achievement_data)
            else:
                update_achievement_progress(
                    user_id=user_id,
                    achievement_key=key,
                    achievement_type='skill',
                    current_value=current_count,
                    target=target
                )
        
        return new_achievements
    except Exception as e:
        logger.error(f"Error checking skill achievements: {e}")
        return []


def check_grammar_level_achievements(user_id: int, level: str, is_complete: bool) -> List[Dict]:
    """
    Check grammar level completion achievements.
    
    Args:
        user_id: User ID
        level: Grammar level ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')
        is_complete: Whether the level is fully completed
    
    Returns:
        List of newly achieved achievements
    """
    achievement_key = f"grammar_{level}_complete"
    definition = ACHIEVEMENT_DEFINITIONS.get(achievement_key)
    
    if not definition or not is_complete:
        return []
    
    try:
        # Check if already achieved
        existing_res = supabase.table("Achievements")\
            .select("achieved_at")\
            .eq("user_id", user_id)\
            .eq("achievement_key", achievement_key)\
            .execute()
        
        if existing_res.data and existing_res.data[0].get('achieved_at'):
            return []  # Already achieved
        
        # Award achievement
        success, achievement_data = award_achievement(
            user_id=user_id,
            achievement_key=achievement_key,
            achievement_type='grammar',
            definition=definition,
            current_value=1
        )
        
        return [achievement_data] if success else []
    
    except Exception as e:
        logger.error(f"Error checking grammar level achievements: {e}")
        return []


def award_achievement(user_id: int, achievement_key: str, achievement_type: str, definition: Dict, current_value: int) -> Tuple[bool, Dict]:
    """
    Award an achievement to a user.
    
    Args:
        user_id: User ID
        achievement_key: Achievement key
        achievement_type: Achievement type
        definition: Achievement definition from ACHIEVEMENT_DEFINITIONS
        current_value: Current value that triggered the achievement
    
    Returns:
        Tuple (success, achievement_data)
    """
    if not supabase or not user_id:
        return False, {}
    
    try:
        # Award coins if specified
        reward_coins = definition.get('reward_coins', 0)
        if reward_coins > 0:
            try:
                from services.user_service import add_coins
                add_coins(user_id, reward_coins)
            except Exception as e:
                logger.warning(f"Error adding coins for achievement: {e}")
        
        # Record achievement
        achievement_data = {
            "user_id": user_id,
            "achievement_type": achievement_type,
            "achievement_key": achievement_key,
            "progress": current_value,
            "target": definition['target'],
            "achieved_at": get_vn_now_utc()
        }
        
        # Upsert achievement
        supabase.table("Achievements")\
            .upsert(achievement_data, on_conflict="user_id, achievement_type, achievement_key")\
            .execute()
        
        return True, {
            "achievement_key": achievement_key,
            "name": definition.get('name', achievement_key),
            "description": definition.get('description', ''),
            "icon": definition.get('icon', '🏆'),
            "coins": reward_coins
        }
    
    except Exception as e:
        logger.error(f"Error awarding achievement: {e}")
        return False, {}


def update_achievement_progress(user_id: int, achievement_key: str, achievement_type: str, current_value: int, target: int):
    """
    Update progress for an achievement (without awarding if not yet reached).
    
    Args:
        user_id: User ID
        achievement_key: Achievement key
        achievement_type: Achievement type
        current_value: Current progress value
        target: Target value
    """
    if not supabase or not user_id:
        return
    
    try:
        # Check if achievement record exists
        existing_res = supabase.table("Achievements")\
            .select("id, achieved_at")\
            .eq("user_id", user_id)\
            .eq("achievement_key", achievement_key)\
            .execute()
        
        if existing_res.data:
            # Update progress only if not already achieved
            if not existing_res.data[0].get('achieved_at'):
                supabase.table("Achievements")\
                    .update({
                        "progress": min(current_value, target),
                        "target": target
                    })\
                    .eq("id", existing_res.data[0]['id'])\
                    .execute()
        else:
            # Create new progress record
            supabase.table("Achievements")\
                .insert({
                    "user_id": user_id,
                    "achievement_type": achievement_type,
                    "achievement_key": achievement_key,
                    "progress": min(current_value, target),
                    "target": target,
                    "achieved_at": None
                })\
                .execute()
    
    except Exception as e:
        logger.error(f"Error updating achievement progress: {e}")


def get_user_achievements(user_id: int) -> Dict[str, List[Dict]]:
    """
    Get all achievements for a user, grouped by type.
    
    Args:
        user_id: User ID
    
    Returns:
        Dict với keys: achieved (completed achievements), progress (in-progress achievements)
    """
    if not supabase or not user_id:
        return {"achieved": [], "progress": []}
    
    try:
        res = supabase.table("Achievements")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        achieved = []
        progress = []
        
        if res.data:
            for ach in res.data:
                achievement_key = ach.get('achievement_key')
                definition = ACHIEVEMENT_DEFINITIONS.get(achievement_key, {})
                
                achievement_info = {
                    "achievement_key": achievement_key,
                    "type": ach.get('achievement_type'),
                    "name": definition.get('name', achievement_key),
                    "description": definition.get('description', ''),
                    "icon": definition.get('icon', '🏆'),
                    "progress": ach.get('progress', 0),
                    "target": ach.get('target', 0),
                    "achieved_at": ach.get('achieved_at'),
                    "reward_coins": definition.get('reward_coins', 0)
                }
                
                if ach.get('achieved_at'):
                    achieved.append(achievement_info)
                else:
                    progress.append(achievement_info)
        
        # Sort achieved by achieved_at (newest first)
        achieved.sort(key=lambda x: x.get('achieved_at', ''), reverse=True)
        
        # Sort progress by progress percentage (highest first)
        progress.sort(key=lambda x: (x.get('progress', 0) / max(x.get('target', 1), 1)), reverse=True)
        
        return {
            "achieved": achieved,
            "progress": progress
        }
    except Exception as e:
        logger.error(f"Error getting user achievements: {e}")
        return {"achieved": [], "progress": []}


def get_achievement_progress(user_id: int) -> Dict:
    """
    Get progress summary for all achievement types.
    
    Args:
        user_id: User ID
    
    Returns:
        Dict với progress summary cho mỗi achievement type
    """
    achievements = get_user_achievements(user_id)
    
    # Count achievements by type
    type_counts = {}
    for ach in achievements['achieved']:
        ach_type = ach.get('type', 'other')
        type_counts[ach_type] = type_counts.get(ach_type, 0) + 1
    
    # Get total available achievements by type
    total_by_type = {}
    for key, definition in ACHIEVEMENT_DEFINITIONS.items():
        ach_type = definition.get('type', 'other')
        total_by_type[ach_type] = total_by_type.get(ach_type, 0) + 1
    
    return {
        "achieved_count": len(achievements['achieved']),
        "total_count": len(ACHIEVEMENT_DEFINITIONS),
        "type_counts": type_counts,
        "total_by_type": total_by_type,
        "achievements": achievements
    }
