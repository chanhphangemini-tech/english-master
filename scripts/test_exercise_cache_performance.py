"""
Script để test tốc độ load exercises từ cache và so sánh với generate mới.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from core.database import supabase
from services.exercise_cache_service import get_unseen_exercise
from core.llm import generate_response_with_fallback, parse_json_response
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test user ID (use admin or test user)
TEST_USER_ID = 1  # Adjust if needed

def test_cache_performance():
    """Test tốc độ load từ cache vs generate mới."""
    if not supabase:
        logger.error("Supabase client not initialized")
        return
    
    print("=" * 60)
    print("Exercise Cache Performance Test")
    print("=" * 60)
    
    test_cases = [
        {"exercise_type": "dictation", "level": "A1", "topic": "Daily Life"},
        {"exercise_type": "dictation", "level": "A2", "topic": "Travel"},
        {"exercise_type": "comprehension", "level": "B1", "topic": "Business"},
        {"exercise_type": "reading_question", "level": "B2", "topic": "Technology"},
        {"exercise_type": "grammar_question", "level": "C1", "topic": None},
        {"exercise_type": "podcast_script", "level": "B1", "topic": None},
    ]
    
    print(f"\nTest User ID: {TEST_USER_ID}")
    print(f"Total test cases: {len(test_cases)}\n")
    
    cache_times = []
    generate_times = []
    
    for i, test_case in enumerate(test_cases, 1):
        exercise_type = test_case["exercise_type"]
        level = test_case["level"]
        topic = test_case["topic"]
        
        print(f"[{i}/{len(test_cases)}] Testing {exercise_type} (Level: {level}, Topic: {topic or 'N/A'})")
        
        # Test 1: Load from cache
        print("  -> Testing cache load...")
        start_time = time.time()
        cached_exercise = get_unseen_exercise(TEST_USER_ID, exercise_type, level, topic)
        cache_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if cached_exercise:
            cache_times.append(cache_time)
            print(f"    OK Cache load: {cache_time:.2f} ms")
            print(f"    OK Exercise ID: {cached_exercise.get('id')}")
        else:
            print(f"    X No cached exercise found")
        
        # Test 2: Generate new (simulate - chỉ đo prompt, không thực sự generate)
        print("  -> Testing generate new (simulated)...")
        start_time = time.time()
        # Simulate prompt creation (không gọi AI thật để tránh tốn API)
        prompt = f"Generate {exercise_type} exercise for level {level}"
        _ = len(prompt)  # Simulate some work
        generate_time = (time.time() - start_time) * 1000
        generate_times.append(generate_time)
        print(f"    ! Simulated generate: {generate_time:.2f} ms (Note: Real AI generation takes 2-5 seconds)")
        
        print()
    
    # Statistics
    print("=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    
    if cache_times:
        avg_cache = sum(cache_times) / len(cache_times)
        min_cache = min(cache_times)
        max_cache = max(cache_times)
        
        print(f"\nCache Load Performance:")
        print(f"  Average: {avg_cache:.2f} ms")
        print(f"  Min:     {min_cache:.2f} ms")
        print(f"  Max:     {max_cache:.2f} ms")
        print(f"  Count:   {len(cache_times)} successful loads")
    
    if generate_times:
        avg_generate = sum(generate_times) / len(generate_times)
        print(f"\nGenerate New (Simulated):")
        print(f"  Average: {avg_generate:.2f} ms")
        print(f"  Note: Real AI generation typically takes 2000-5000 ms")
    
    if cache_times:
        print(f"\nSpeed Improvement:")
        print(f"  Cache is ~{2000/avg_cache:.0f}x - ~{5000/avg_cache:.0f}x faster than AI generation")
        print(f"  (Assuming AI generation takes 2-5 seconds)")
    
    print("\n" + "=" * 60)

def test_cache_statistics():
    """Kiểm tra thống kê cache."""
    if not supabase:
        logger.error("Supabase client not initialized")
        return
    
    print("\n" + "=" * 60)
    print("CACHE STATISTICS")
    print("=" * 60)
    
    try:
        # Count exercises by type
        exercise_types = ["dictation", "comprehension", "reading_question", "grammar_question", "podcast_script"]
        
        for ex_type in exercise_types:
            result = supabase.table("AIExercises").select("id", count="exact").eq("exercise_type", ex_type).execute()
            count = result.count if hasattr(result, 'count') else len(result.data or [])
            print(f"\n{ex_type}:")
            print(f"  Total exercises: {count}")
            
            # Count by level
            levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
            for level in levels:
                level_result = supabase.table("AIExercises").select("id", count="exact").eq("exercise_type", ex_type).eq("level", level).execute()
                level_count = level_result.count if hasattr(level_result, 'count') else len(level_result.data or [])
                if level_count > 0:
                    print(f"    {level}: {level_count}")
        
        # Total count
        total_result = supabase.table("AIExercises").select("id", count="exact").execute()
        total_count = total_result.count if hasattr(total_result, 'count') else len(total_result.data or [])
        print(f"\nTotal exercises in cache: {total_count}")
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")

if __name__ == "__main__":
    test_cache_statistics()
    test_cache_performance()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nTips:")
    print("- Cache load should be < 200ms (typically 50-150ms)")
    print("- AI generation takes 2-5 seconds")
    print("- Cache provides 20-100x speed improvement")
    print("- More exercises in cache = better user experience")
