"""
Skill Tracking Service
Helper service to track skill exercise completions and check achievements
"""
import logging
from core.database import supabase
from services.achievement_service import check_skill_achievements
from core.timezone_utils import get_vn_now_utc

logger = logging.getLogger(__name__)

def track_skill_progress(user_id: int, skill_type: str, exercises: int = 1, correct: float = 0) -> None:
    """
    Track skill exercise progress and update SkillProgress table.
    
    Args:
        user_id: User ID
        skill_type: Skill type ('listening', 'speaking', 'reading', 'writing')
        exercises: Number of exercises completed (default: 1)
        correct: Number of correct exercises or accuracy (0.0-1.0) (default: 0)
    """
    if not supabase or not user_id or not skill_type:
        return
    
    try:
        # Calculate accuracy (0-100)
        if exercises > 0:
            if correct <= 1.0:
                # correct is accuracy (0.0-1.0)
                accuracy_percent = int(correct * 100)
            else:
                # correct is number of correct exercises
                accuracy_percent = int((correct / exercises) * 100)
        else:
            accuracy_percent = 0
        
        # Clamp accuracy_percent to 0-100
        accuracy_percent = max(0, min(100, accuracy_percent))
        
        # Get current user level (default to A1)
        try:
            user_res = supabase.table("Users").select("current_level").eq("id", user_id).single().execute()
            user_level = user_res.data.get('current_level', 'A1') if user_res.data else 'A1'
        except:
            user_level = 'A1'
        
        # Check if SkillProgress record exists for this user and skill
        try:
            existing = supabase.table("SkillProgress").select("id").eq("user_id", user_id).eq("skill_type", skill_type.lower()).execute()
            if existing.data and len(existing.data) > 0:
                # Update existing record
                supabase.table("SkillProgress").update({
                    "level": user_level,
                    "progress_percent": accuracy_percent,
                    "last_updated": get_vn_now_utc()
                }).eq("id", existing.data[0]['id']).execute()
            else:
                # Insert new record
                supabase.table("SkillProgress").insert({
                    "user_id": user_id,
                    "skill_type": skill_type.lower(),
                    "level": user_level,
                    "progress_percent": accuracy_percent,
                    "last_updated": get_vn_now_utc()
                }).execute()
        except Exception as upsert_error:
            logger.warning(f"Error upserting SkillProgress for {skill_type}: {upsert_error}")
        
        # Count total exercises for achievements
        try:
            activity_res = supabase.table("ActivityLog").select("id", count="exact").eq(
                "user_id", user_id
            ).eq("action_type", f"skill_{skill_type}").execute()
            
            total_count = activity_res.count if hasattr(activity_res, 'count') and activity_res.count else 0
            
            # Check achievements
            check_skill_achievements(user_id, skill_type, total_count)
        except Exception as ach_error:
            logger.warning(f"Error checking achievements for {skill_type}: {ach_error}")
            
    except Exception as e:
        logger.error(f"Error tracking skill progress for {skill_type}: {e}")

def track_skill_completion(user_id: int, skill_type: str) -> None:
    """
    Track skill exercise completion and check achievements.
    
    Args:
        user_id: User ID
        skill_type: Skill type ('listening', 'speaking', 'reading', 'writing')
    """
    if not supabase or not user_id or not skill_type:
        return
    
    try:
        # Count total completed exercises for this skill
        res = supabase.table("ActivityLog").select("id", count="exact").eq(
            "user_id", user_id
        ).eq("action_type", f"skill_{skill_type}").execute()
        
        current_count = res.count if hasattr(res, 'count') and res.count else 0
        
        # Check achievements
        check_skill_achievements(user_id, skill_type, current_count)
    except Exception as e:
        logger.warning(f"Error tracking skill completion for {skill_type}: {e}")

def log_skill_exercise(user_id: int, skill_type: str, metadata: dict = None) -> bool:
    """
    Log skill exercise completion to ActivityLog and check achievements.
    
    Args:
        user_id: User ID
        skill_type: Skill type ('listening', 'speaking', 'reading', 'writing')
        metadata: Additional metadata
    
    Returns:
        bool: True if logged successfully
    """
    if not supabase or not user_id or not skill_type:
        return False
    
    try:
        # Log to ActivityLog
        supabase.table("ActivityLog").insert({
            "user_id": user_id,
            "action_type": f"skill_{skill_type}",
            "value": 1,
            "metadata": metadata or {}
        }).execute()
        
        # Count total completed exercises for this skill
        res = supabase.table("ActivityLog").select("id", count="exact").eq(
            "user_id", user_id
        ).eq("action_type", f"skill_{skill_type}").execute()
        
        current_count = res.count if hasattr(res, 'count') and res.count else 0
        
        # Check achievements
        check_skill_achievements(user_id, skill_type, current_count)
        
        return True
    except Exception as e:
        logger.error(f"Error logging skill exercise for {skill_type}: {e}")
        return False
