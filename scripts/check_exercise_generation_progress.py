"""
Script để check progress của exercise generation.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import supabase
from services.exercise_cache_service import VALID_TOPICS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXERCISE_TYPES = ["dictation", "comprehension", "reading_question"]
TARGET_COUNT = 5  # 5 exercises per topic

def check_progress():
    """Check generation progress."""
    if not supabase:
        logger.error("Supabase client not initialized")
        return
    
    print("=" * 60)
    print("Exercise Generation Progress Report")
    print("=" * 60)
    
    total_topics = len(VALID_TOPICS)
    
    # Count by exercise type
    stats = {}
    for ex_type in EXERCISE_TYPES:
        stats[ex_type] = {
            'complete': 0,
            'partial': 0,
            'missing': 0,
            'total_exercises': 0
        }
        
        for topic in VALID_TOPICS:
            try:
                result = supabase.table("AIExercises").select("id", count="exact").eq("exercise_type", ex_type).eq("topic", topic).execute()
                count = result.count if hasattr(result, 'count') else len(result.data or [])
                
                stats[ex_type]['total_exercises'] += count
                
                if count >= TARGET_COUNT:
                    stats[ex_type]['complete'] += 1
                elif count > 0:
                    stats[ex_type]['partial'] += 1
                else:
                    stats[ex_type]['missing'] += 1
            except Exception as e:
                logger.error(f"Error checking {ex_type} - {topic}: {e}")
    
    # Print summary
    print(f"\nTotal topics: {total_topics}")
    print(f"Target: {TARGET_COUNT} exercises per topic per type")
    print(f"Total exercises needed: {total_topics * len(EXERCISE_TYPES) * TARGET_COUNT}")
    print()
    
    total_complete = 0
    total_exercises = 0
    
    for ex_type in EXERCISE_TYPES:
        s = stats[ex_type]
        total_complete += s['complete']
        total_exercises += s['total_exercises']
        
        print(f"{ex_type.upper()}:")
        print(f"  Complete topics: {s['complete']}/{total_topics} ({s['complete']*100/total_topics:.1f}%)")
        print(f"  Partial topics: {s['partial']}/{total_topics}")
        print(f"  Missing topics: {s['missing']}/{total_topics}")
        print(f"  Total exercises: {s['total_exercises']}/{total_topics * TARGET_COUNT}")
        print()
    
    print("=" * 60)
    print("OVERALL PROGRESS")
    print("=" * 60)
    total_possible = total_topics * len(EXERCISE_TYPES)
    total_complete_types = total_complete
    print(f"Complete topic-types: {total_complete_types}/{total_possible} ({total_complete_types*100/total_possible:.1f}%)")
    print(f"Total exercises generated: {total_exercises}/{total_topics * len(EXERCISE_TYPES) * TARGET_COUNT}")
    print("=" * 60)

if __name__ == "__main__":
    check_progress()
