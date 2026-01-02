"""
Streak Service - Streak Milestones and Rewards
Hệ thống milestone và rewards cho streak để tăng động lực học tập
"""
import streamlit as st
from core.database import supabase
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from core.timezone_utils import get_vn_now_utc

logger = logging.getLogger(__name__)

# Streak Milestones Configuration
STREAK_MILESTONES = {
    7: {
        "coins": 50,
        "badge": "week_warrior",
        "title": None,
        "frame": None,
        "name": "Week Warrior"
    },
    14: {
        "coins": 100,
        "badge": "two_weeks_strong",
        "title": None,
        "frame": None,
        "name": "Two Weeks Strong"
    },
    30: {
        "coins": 200,
        "badge": "monthly_master",
        "title": "monthly_master",
        "frame": None,
        "name": "Monthly Master"
    },
    60: {
        "coins": 500,
        "badge": "two_month_champion",
        "title": None,
        "frame": None,
        "name": "Two Month Champion"
    },
    100: {
        "coins": 1000,
        "badge": "century_streak",
        "title": None,
        "frame": "century_frame",
        "name": "Century Streak"
    },
    180: {
        "coins": 2000,
        "badge": "half_year_hero",
        "title": None,
        "frame": None,
        "name": "Half Year Hero"
    },
    365: {
        "coins": 5000,
        "badge": "year_legend",
        "title": "year_legend",
        "frame": None,
        "name": "Year Legend"
    }
}


def check_streak_milestones(user_id: int, current_streak: int) -> List[Dict]:
    """
    Check if user reached any streak milestones and award rewards.
    
    Args:
        user_id: User ID
        current_streak: Current streak value
    
    Returns:
        List of achieved milestones (newly achieved)
    """
    if not supabase or not user_id:
        return []
    
    try:
        # Get already achieved milestones
        achieved_res = supabase.table("StreakMilestones")\
            .select("milestone_days")\
            .eq("user_id", user_id)\
            .execute()
        
        achieved_days = set()
        if achieved_res.data:
            achieved_days = {m['milestone_days'] for m in achieved_res.data}
        
        # Check which milestones should be achieved
        new_milestones = []
        for milestone_days, reward_config in STREAK_MILESTONES.items():
            if milestone_days <= current_streak and milestone_days not in achieved_days:
                # New milestone achieved!
                new_milestones.append(milestone_days)
        
        # Award rewards for new milestones
        awarded_milestones = []
        for milestone_days in new_milestones:
            reward_config = STREAK_MILESTONES[milestone_days]
            
            # Award milestone
            success, milestone_data = award_streak_milestone(
                user_id=user_id,
                milestone_days=milestone_days,
                reward_config=reward_config
            )
            
            if success:
                awarded_milestones.append(milestone_data)
        
        return awarded_milestones
    
    except Exception as e:
        logger.error(f"Error checking streak milestones: {e}")
        return []


def award_streak_milestone(user_id: int, milestone_days: int, reward_config: Dict) -> Tuple[bool, Dict]:
    """
    Award a streak milestone to a user.
    
    Args:
        user_id: User ID
        milestone_days: Number of days for this milestone
        reward_config: Reward configuration from STREAK_MILESTONES
    
    Returns:
        Tuple (success, milestone_data)
    """
    if not supabase or not user_id:
        return False, {}
    
    try:
        # Get current user coins
        user_res = supabase.table("Users")\
            .select("coins")\
            .eq("id", user_id)\
            .single()\
            .execute()
        
        current_coins = user_res.data.get('coins', 0) or 0 if user_res.data else 0
        
        # Calculate new coins
        reward_coins = reward_config.get('coins', 0)
        new_coins = current_coins + reward_coins
        
        # Update user coins
        supabase.table("Users")\
            .update({"coins": new_coins})\
            .eq("id", user_id)\
            .execute()
        
        # Award badge if specified
        reward_badge = reward_config.get('badge')
        if reward_badge:
            try:
                award_badge_to_user(user_id, reward_badge)
            except Exception as e:
                logger.warning(f"Error awarding badge {reward_badge}: {e}")
        
        # Award title if specified
        reward_title = reward_config.get('title')
        if reward_title:
            try:
                award_title_to_user(user_id, reward_title)
            except Exception as e:
                logger.warning(f"Error awarding title {reward_title}: {e}")
        
        # Award frame if specified
        reward_frame = reward_config.get('frame')
        if reward_frame:
            try:
                award_frame_to_user(user_id, reward_frame)
            except Exception as e:
                logger.warning(f"Error awarding frame {reward_frame}: {e}")
        
        # Record milestone achievement
        milestone_data = {
            "user_id": user_id,
            "milestone_days": milestone_days,
            "reward_coins": reward_coins,
            "reward_badge": reward_badge,
            "reward_title": reward_title,
            "reward_frame": reward_frame,
            "achieved_at": get_vn_now_utc()
        }
        
        supabase.table("StreakMilestones")\
            .insert(milestone_data)\
            .execute()
        
        return True, {
            "milestone_days": milestone_days,
            "name": reward_config.get('name', f"{milestone_days} Days"),
            "coins": reward_coins,
            "badge": reward_badge,
            "title": reward_title,
            "frame": reward_frame
        }
    
    except Exception as e:
        logger.error(f"Error awarding streak milestone: {e}")
        return False, {}


def award_badge_to_user(user_id: int, badge_key: str) -> bool:
    """
    Award a badge to user (add to UserBadges table).
    
    Args:
        user_id: User ID
        badge_key: Badge key/name
    
    Returns:
        bool: Success
    """
    if not supabase or not user_id:
        return False
    
    try:
        # First, try to find badge by name/key
        badge_res = supabase.table("Badges")\
            .select("id")\
            .eq("name", badge_key)\
            .single()\
            .execute()
        
        badge_id = None
        if badge_res.data:
            badge_id = badge_res.data.get('id')
        else:
            # Badge doesn't exist in Badges table - skip for now
            logger.warning(f"Badge {badge_key} not found in Badges table")
            return False
        
        # Check if user already has this badge
        existing_res = supabase.table("UserBadges")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("badge_id", badge_id)\
            .execute()
        
        if existing_res.data:
            # User already has this badge
            return True
        
        # Add badge to user
        supabase.table("UserBadges")\
            .insert({
                "user_id": user_id,
                "badge_id": badge_id
            })\
            .execute()
        
        return True
    except Exception as e:
        logger.error(f"Error awarding badge: {e}")
        return False


def award_title_to_user(user_id: int, title_key: str) -> bool:
    """
    Award a title to user (add to UserInventory if title item exists).
    
    Args:
        user_id: User ID
        title_key: Title key/name (should match ShopItems.value)
    
    Returns:
        bool: Success
    """
    if not supabase or not user_id:
        return False
    
    try:
        # Find title item in ShopItems
        item_res = supabase.table("ShopItems")\
            .select("id")\
            .eq("type", "title")\
            .eq("value", title_key)\
            .single()\
            .execute()
        
        item_id = None
        if item_res.data:
            item_id = item_res.data.get('id')
        else:
            # Title item doesn't exist - skip for now
            logger.warning(f"Title {title_key} not found in ShopItems")
            return False
        
        # Check if user already has this title
        existing_res = supabase.table("UserInventory")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("item_id", item_id)\
            .execute()
        
        if existing_res.data:
            # User already has this title
            return True
        
        # Add title to user inventory
        supabase.table("UserInventory")\
            .insert({
                "user_id": user_id,
                "item_id": item_id,
                "quantity": 1,
                "is_active": False
            })\
            .execute()
        
        return True
    except Exception as e:
        logger.error(f"Error awarding title: {e}")
        return False


def award_frame_to_user(user_id: int, frame_key: str) -> bool:
    """
    Award a frame to user (add to UserInventory if frame item exists).
    
    Args:
        user_id: User ID
        frame_key: Frame key/name (should match ShopItems.value)
    
    Returns:
        bool: Success
    """
    if not supabase or not user_id:
        return False
    
    try:
        # Find frame item in ShopItems
        item_res = supabase.table("ShopItems")\
            .select("id")\
            .eq("type", "avatar_frame")\
            .eq("value", frame_key)\
            .single()\
            .execute()
        
        item_id = None
        if item_res.data:
            item_id = item_res.data.get('id')
        else:
            # Frame item doesn't exist - skip for now
            logger.warning(f"Frame {frame_key} not found in ShopItems")
            return False
        
        # Check if user already has this frame
        existing_res = supabase.table("UserInventory")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("item_id", item_id)\
            .execute()
        
        if existing_res.data:
            # User already has this frame
            return True
        
        # Add frame to user inventory
        supabase.table("UserInventory")\
            .insert({
                "user_id": user_id,
                "item_id": item_id,
                "quantity": 1,
                "is_active": False
            })\
            .execute()
        
        return True
    except Exception as e:
        logger.error(f"Error awarding frame: {e}")
        return False


def get_streak_milestones(user_id: int) -> List[Dict]:
    """
    Get all achieved milestones for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        List of milestone data
    """
    if not supabase or not user_id:
        return []
    
    try:
        res = supabase.table("StreakMilestones")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("milestone_days", desc=False)\
            .execute()
        
        milestones = []
        if res.data:
            for milestone in res.data:
                milestone_days = milestone.get('milestone_days')
                reward_config = STREAK_MILESTONES.get(milestone_days, {})
                milestones.append({
                    "milestone_days": milestone_days,
                    "name": reward_config.get('name', f"{milestone_days} Days"),
                    "achieved_at": milestone.get('achieved_at'),
                    "reward_coins": milestone.get('reward_coins', 0),
                    "reward_badge": milestone.get('reward_badge'),
                    "reward_title": milestone.get('reward_title'),
                    "reward_frame": milestone.get('reward_frame')
                })
        
        return milestones
    except Exception as e:
        logger.error(f"Error getting streak milestones: {e}")
        return []


def get_next_milestone(user_id: int, current_streak: int) -> Optional[Dict]:
    """
    Get next milestone info for a user.
    
    Args:
        user_id: User ID
        current_streak: Current streak value
    
    Returns:
        Dict with next milestone info, or None if all milestones achieved
    """
    try:
        # Get achieved milestones
        achieved_res = supabase.table("StreakMilestones")\
            .select("milestone_days")\
            .eq("user_id", user_id)\
            .execute()
        
        achieved_days = set()
        if achieved_res.data:
            achieved_days = {m['milestone_days'] for m in achieved_res.data}
        
        # Find next milestone
        sorted_milestones = sorted(STREAK_MILESTONES.keys())
        for milestone_days in sorted_milestones:
            if milestone_days > current_streak and milestone_days not in achieved_days:
                reward_config = STREAK_MILESTONES[milestone_days]
                return {
                    "milestone_days": milestone_days,
                    "name": reward_config.get('name', f"{milestone_days} Days"),
                    "days_remaining": milestone_days - current_streak,
                    "reward_coins": reward_config.get('coins', 0),
                    "reward_badge": reward_config.get('badge'),
                    "reward_title": reward_config.get('title'),
                    "reward_frame": reward_config.get('frame')
                }
        
        return None
    except Exception as e:
        logger.error(f"Error getting next milestone: {e}")
        return None


def get_milestone_progress(user_id: int, current_streak: int) -> Dict:
    """
    Get milestone progress information.
    
    Args:
        user_id: User ID
        current_streak: Current streak value
    
    Returns:
        Dict with progress info
    """
    try:
        milestones = get_streak_milestones(user_id)
        next_milestone = get_next_milestone(user_id, current_streak)
        
        return {
            "achieved_milestones": milestones,
            "next_milestone": next_milestone,
            "total_achieved": len(milestones),
            "total_milestones": len(STREAK_MILESTONES)
        }
    except Exception as e:
        logger.error(f"Error getting milestone progress: {e}")
        return {
            "achieved_milestones": [],
            "next_milestone": None,
            "total_achieved": 0,
            "total_milestones": len(STREAK_MILESTONES)
        }
