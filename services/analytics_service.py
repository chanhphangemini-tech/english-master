"""
Analytics Service - Progress Analytics Dashboard
Cung cấp analytics chi tiết về tiến độ học tập cho Premium users
"""
import streamlit as st
from core.database import supabase
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from core.timezone_utils import (
    get_vn_now_utc, get_vn_start_of_day_utc, 
    get_vn_start_of_week_utc, get_vn_start_of_month_utc
)

logger = logging.getLogger(__name__)


def get_user_progress_analytics(user_id: int, days: int = 30) -> Dict:
    """
    Get comprehensive progress analytics for a user.
    
    Args:
        user_id: User ID
        days: Number of days to analyze (default: 30)
    
    Returns:
        Dict with analytics data including:
        - overview: Basic stats (total words, streak, days active, avg study time)
        - vocabulary_progress: Timeline data for vocabulary growth
        - skills_progress: Progress for each skill (listening, speaking, reading, writing)
        - activity_heatmap: Daily activity data
        - topics_progress: Progress by vocabulary topics
        - level_progress: Progress by level
        - ai_usage: AI usage breakdown by feature
    """
    if not supabase or not user_id:
        return {}
    
    try:
        # Calculate date range
        from datetime import timezone
        now_utc = datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00'))
        start_date_utc = (now_utc - timedelta(days=days)).isoformat()
        
        analytics = {
            "overview": get_overview_stats(user_id, days),
            "vocabulary_progress": get_vocabulary_progress_timeline(user_id, days),
            "skills_progress": get_skills_progress(user_id),
            "activity_heatmap": get_activity_heatmap(user_id, days),
            "topics_progress": get_topics_progress(user_id),
            "level_progress": get_level_progress(user_id),
            "ai_usage": get_ai_usage_breakdown(user_id, days)
        }
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting progress analytics: {e}")
        return {}


def get_overview_stats(user_id: int, days: int = 30) -> Dict:
    """
    Get overview statistics:
    - Total words learned
    - Current streak
    - Days active
    - Average daily study time (estimated)
    """
    if not supabase or not user_id:
        return {
            "total_words": 0,
            "current_streak": 0,
            "days_active": 0,
            "avg_study_time_minutes": 0
        }
    
    try:
        # Total words learned
        vocab_res = supabase.table("UserVocabulary")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        total_words = vocab_res.count or 0
        
        # Current streak (from Users table)
        user_res = supabase.table("Users")\
            .select("current_streak")\
            .eq("id", user_id)\
            .single()\
            .execute()
        current_streak = user_res.data.get('current_streak', 0) or 0 if user_res.data else 0
        
        # Days active (unique days with activity in ActivityLog)
        start_date = (datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00')) - timedelta(days=days)).isoformat()
        activity_res = supabase.table("ActivityLog")\
            .select("created_at")\
            .eq("user_id", user_id)\
            .gte("created_at", start_date)\
            .execute()
        
        # Count unique days
        unique_dates = set()
        if activity_res.data:
            for entry in activity_res.data:
                date_str = entry.get('created_at', '')[:10]  # Extract YYYY-MM-DD
                if date_str:
                    unique_dates.add(date_str)
        days_active = len(unique_dates)
        
        # Average study time (estimated based on activity count)
        # Rough estimate: 5 minutes per activity
        activity_count = len(activity_res.data) if activity_res.data else 0
        avg_study_time_minutes = int((activity_count * 5) / max(days_active, 1))
        
        return {
            "total_words": total_words,
            "current_streak": current_streak,
            "days_active": days_active,
            "avg_study_time_minutes": avg_study_time_minutes
        }
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        return {
            "total_words": 0,
            "current_streak": 0,
            "days_active": 0,
            "avg_study_time_minutes": 0
        }


def get_vocabulary_progress_timeline(user_id: int, days: int = 30) -> List[Dict]:
    """
    Get vocabulary learning timeline (words learned per day).
    
    Returns:
        List of dicts with keys: date (YYYY-MM-DD), count (words learned that day)
    """
    if not supabase or not user_id:
        return []
    
    try:
        # Get all UserVocabulary entries with created_at
        start_date = (datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00')) - timedelta(days=days)).isoformat()
        
        vocab_res = supabase.table("UserVocabulary")\
            .select("created_at")\
            .eq("user_id", user_id)\
            .gte("created_at", start_date)\
            .order("created_at", desc=False)\
            .execute()
        
        # Group by date
        timeline = {}
        if vocab_res.data:
            for entry in vocab_res.data:
                date_str = entry.get('created_at', '')[:10]  # Extract YYYY-MM-DD
                if date_str:
                    timeline[date_str] = timeline.get(date_str, 0) + 1
        
        # Convert to list format
        result = [{"date": date, "count": count} for date, count in sorted(timeline.items())]
        
        return result
    except Exception as e:
        logger.error(f"Error getting vocabulary timeline: {e}")
        return []


def get_skills_progress(user_id: int) -> Dict:
    """
    Get skills progress (listening, speaking, reading, writing).
    
    Returns:
        Dict with keys: listening, speaking, reading, writing
        Each contains: exercises_completed, accuracy, level
    """
    if not supabase or not user_id:
        return {
            "listening": {"exercises_completed": 0, "accuracy": 0, "level": "A1"},
            "speaking": {"exercises_completed": 0, "accuracy": 0, "level": "A1"},
            "reading": {"exercises_completed": 0, "accuracy": 0, "level": "A1"},
            "writing": {"exercises_completed": 0, "accuracy": 0, "level": "A1"}
        }
    
    try:
        # Try to get from SkillProgress table
        skills_res = supabase.table("SkillProgress")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        skills_data = {}
        if skills_res.data:
            for skill in skills_res.data:
                skill_type = skill.get('skill_type', '').lower()
                skills_data[skill_type] = {
                    "exercises_completed": skill.get('progress_percent', 0),  # Use progress as proxy
                    "accuracy": skill.get('progress_percent', 0),
                    "level": skill.get('level', 'A1')
                }
        
        # Default values for missing skills
        default_skill = {"exercises_completed": 0, "accuracy": 0, "level": "A1"}
        result = {
            "listening": skills_data.get('listening', default_skill),
            "speaking": skills_data.get('speaking', default_skill),
            "reading": skills_data.get('reading', default_skill),
            "writing": skills_data.get('writing', default_skill)
        }
        
        # If no SkillProgress data, estimate from ActivityLog
        if not skills_res.data:
            # Count activities by skill type from ActivityLog
            activity_res = supabase.table("ActivityLog")\
                .select("action_type")\
                .eq("user_id", user_id)\
                .execute()
            
            if activity_res.data:
                skill_counts = {
                    "listening": 0,
                    "speaking": 0,
                    "reading": 0,
                    "writing": 0
                }
                
                for entry in activity_res.data:
                    action_type = entry.get('action_type', '').lower()
                    if 'listening' in action_type or 'luyen_nghe' in action_type:
                        skill_counts['listening'] += 1
                    elif 'speaking' in action_type or 'luyen_noi' in action_type:
                        skill_counts['speaking'] += 1
                    elif 'reading' in action_type or 'luyen_doc' in action_type:
                        skill_counts['reading'] += 1
                    elif 'writing' in action_type or 'luyen_viet' in action_type:
                        skill_counts['writing'] += 1
                
                # Update result with counts
                for skill_type in result:
                    result[skill_type]["exercises_completed"] = skill_counts.get(skill_type, 0)
        
        return result
    except Exception as e:
        logger.error(f"Error getting skills progress: {e}")
        return {
            "listening": {"exercises_completed": 0, "accuracy": 0, "level": "A1"},
            "speaking": {"exercises_completed": 0, "accuracy": 0, "level": "A1"},
            "reading": {"exercises_completed": 0, "accuracy": 0, "level": "A1"},
            "writing": {"exercises_completed": 0, "accuracy": 0, "level": "A1"}
        }


def get_activity_heatmap(user_id: int, days: int = 30) -> List[Dict]:
    """
    Get daily activity heatmap data.
    
    Returns:
        List of dicts with keys: date (YYYY-MM-DD), count (activity count for that day)
    """
    if not supabase or not user_id:
        return []
    
    try:
        start_date = (datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00')) - timedelta(days=days)).isoformat()
        
        activity_res = supabase.table("ActivityLog")\
            .select("created_at")\
            .eq("user_id", user_id)\
            .gte("created_at", start_date)\
            .execute()
        
        # Group by date
        heatmap = {}
        if activity_res.data:
            for entry in activity_res.data:
                date_str = entry.get('created_at', '')[:10]  # Extract YYYY-MM-DD
                if date_str:
                    heatmap[date_str] = heatmap.get(date_str, 0) + 1
        
        # Convert to list format
        result = [{"date": date, "count": count} for date, count in sorted(heatmap.items())]
        
        return result
    except Exception as e:
        logger.error(f"Error getting activity heatmap: {e}")
        return []


def get_topics_progress(user_id: int) -> Dict[str, int]:
    """
    Get vocabulary progress by topic.
    
    Returns:
        Dict with topic names as keys and word counts as values
    """
    if not supabase or not user_id:
        return {}
    
    try:
        # Get UserVocabulary with Vocabulary join to get topics
        vocab_res = supabase.table("UserVocabulary")\
            .select("vocab_id, Vocabulary(topic)")\
            .eq("user_id", user_id)\
            .execute()
        
        topics = {}
        if vocab_res.data:
            for entry in vocab_res.data:
                vocab_data = entry.get('Vocabulary', {})
                if isinstance(vocab_data, dict):
                    topic = vocab_data.get('topic', 'Other') or 'Other'
                elif isinstance(vocab_data, list) and len(vocab_data) > 0:
                    topic = vocab_data[0].get('topic', 'Other') or 'Other'
                else:
                    topic = 'Other'
                
                topics[topic] = topics.get(topic, 0) + 1
        
        return topics
    except Exception as e:
        logger.error(f"Error getting topics progress: {e}")
        return {}


def get_level_progress(user_id: int) -> Dict[str, int]:
    """
    Get vocabulary progress by level (A1, A2, B1, B2, C1, C2).
    
    Returns:
        Dict with level names as keys and word counts as values
    """
    if not supabase or not user_id:
        return {}
    
    try:
        # Get UserVocabulary with Vocabulary join to get levels
        vocab_res = supabase.table("UserVocabulary")\
            .select("vocab_id, Vocabulary(level)")\
            .eq("user_id", user_id)\
            .execute()
        
        levels = {}
        if vocab_res.data:
            for entry in vocab_res.data:
                vocab_data = entry.get('Vocabulary', {})
                if isinstance(vocab_data, dict):
                    level = vocab_data.get('level', 'A1') or 'A1'
                elif isinstance(vocab_data, list) and len(vocab_data) > 0:
                    level = vocab_data[0].get('level', 'A1') or 'A1'
                else:
                    level = 'A1'
                
                levels[level] = levels.get(level, 0) + 1
        
        return levels
    except Exception as e:
        logger.error(f"Error getting level progress: {e}")
        return {}


def get_ai_usage_breakdown(user_id: int, days: int = 30) -> Dict[str, int]:
    """
    Get AI usage breakdown by feature type.
    
    Returns:
        Dict with feature types as keys and usage counts as values
    """
    if not supabase or not user_id:
        return {}
    
    try:
        start_date = (datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00')) - timedelta(days=days)).isoformat()
        
        # Get AI-related activities from ActivityLog
        activity_res = supabase.table("ActivityLog")\
            .select("action_type")\
            .eq("user_id", user_id)\
            .gte("created_at", start_date)\
            .like("action_type", "ai_%")\
            .execute()
        
        usage = {
            "listening": 0,
            "speaking": 0,
            "reading": 0,
            "writing": 0,
            "other": 0
        }
        
        if activity_res.data:
            for entry in activity_res.data:
                action_type = entry.get('action_type', '').lower()
                if 'listening' in action_type or 'ai_listening' in action_type:
                    usage['listening'] += 1
                elif 'speaking' in action_type or 'ai_speaking' in action_type:
                    usage['speaking'] += 1
                elif 'reading' in action_type or 'ai_reading' in action_type:
                    usage['reading'] += 1
                elif 'writing' in action_type or 'ai_writing' in action_type:
                    usage['writing'] += 1
                else:
                    usage['other'] += 1
        
        return usage
    except Exception as e:
        logger.error(f"Error getting AI usage breakdown: {e}")
        return {}


def export_analytics_to_csv(user_id: int, days: int = 30) -> Optional[bytes]:
    """
    Export analytics data to CSV format.
    
    Returns:
        bytes: CSV file content, or None on error
    """
    try:
        import csv
        import io
        
        analytics = get_user_progress_analytics(user_id, days)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write overview
        writer.writerow(["Metric", "Value"])
        overview = analytics.get('overview', {})
        writer.writerow(["Total Words Learned", overview.get('total_words', 0)])
        writer.writerow(["Current Streak", overview.get('current_streak', 0)])
        writer.writerow(["Days Active", overview.get('days_active', 0)])
        writer.writerow(["Average Study Time (minutes)", overview.get('avg_study_time_minutes', 0)])
        writer.writerow([])
        
        # Write vocabulary timeline
        writer.writerow(["Date", "Words Learned"])
        timeline = analytics.get('vocabulary_progress', [])
        for entry in timeline:
            writer.writerow([entry.get('date', ''), entry.get('count', 0)])
        writer.writerow([])
        
        # Write topics
        writer.writerow(["Topic", "Word Count"])
        topics = analytics.get('topics_progress', {})
        for topic, count in topics.items():
            writer.writerow([topic, count])
        writer.writerow([])
        
        # Write levels
        writer.writerow(["Level", "Word Count"])
        levels = analytics.get('level_progress', {})
        for level, count in levels.items():
            writer.writerow([level, count])
        
        # Convert to bytes
        csv_bytes = output.getvalue().encode('utf-8-sig')  # UTF-8 with BOM for Excel compatibility
        output.close()
        
        return csv_bytes
    except Exception as e:
        logger.error(f"Error exporting analytics to CSV: {e}")
        return None


def export_analytics_to_pdf(user_id: int, days: int = 30) -> Optional[bytes]:
    """
    Export analytics data to PDF format (Premium only).
    
    Returns:
        bytes: PDF file content, or None on error
    """
    try:
        # PDF export requires reportlab library
        # For now, return None - can be implemented later if needed
        logger.info("PDF export not yet implemented")
        return None
    except Exception as e:
        logger.error(f"Error exporting analytics to PDF: {e}")
        return None
