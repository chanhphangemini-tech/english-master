"""
Script để generate 5 mẫu exercises cho mỗi chủ đề.
Chạy theo batch để tránh quá tải API.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import supabase
from services.exercise_cache_service import VALID_TOPICS, save_exercise
from core.llm import generate_response_with_fallback, parse_json_response
import logging
import time
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Số mẫu cần generate cho mỗi chủ đề
SAMPLES_PER_TOPIC = 5

# Các exercise types cần generate
EXERCISE_TYPES = [
    "dictation",
    "comprehension", 
    "reading_question",
    "podcast_script"
]

# Level distribution (A1, A2 nhiều hơn để phù hợp với user mới)
LEVEL_DISTRIBUTION = {
    "A1": 1,  # 1 bài A1
    "A2": 1,  # 1 bài A2
    "B1": 1,  # 1 bài B1
    "B2": 1,  # 1 bài B2
    "C1": 1,  # 1 bài C1
}

# Level distribution cho podcast (không có A1, vì podcast thường A2+)
PODCAST_LEVEL_DISTRIBUTION = {
    "A2": 1,
    "B1": 1,
    "B2": 1,
    "C1": 1,
}

def count_existing_exercises(exercise_type: str, topic: str) -> int:
    """Đếm số exercises hiện có cho topic này."""
    try:
        result = supabase.table("AIExercises").select("id", count="exact").eq("exercise_type", exercise_type).eq("topic", topic).execute()
        return result.count if hasattr(result, 'count') else len(result.data or [])
    except Exception as e:
        logger.error(f"Error counting exercises: {e}")
        return 0

def generate_dictation_exercise(topic: str, level: str) -> Dict[str, Any]:
    """Generate dictation exercise."""
    prompt = f"""
    Generate 1 English sentence for dictation practice.
    Level: {level} (CEFR).
    Topic: {topic}.
    
    Return strictly JSON format:
    {{
        "text": "The sentence in English",
        "translation": "Vietnamese translation"
    }}
    """
    
    try:
        res = generate_response_with_fallback(prompt, ["ERROR"])
        data = parse_json_response(res)
        if data and "text" in data:
            return data
    except Exception as e:
        logger.error(f"Error generating dictation: {e}")
    
    return None

def generate_comprehension_exercise(topic: str, level: str) -> Dict[str, Any]:
    """Generate comprehension exercise."""
    prompt = f"""
    Create a short reading comprehension exercise about '{topic}' for level {level}.
    Length: 50-80 words.
    
    Return strictly JSON format:
    {{
        "text": "Short passage text",
        "question": "Comprehension question",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Correct Option Text",
        "explanation": "Explanation in Vietnamese"
    }}
    """
    
    try:
        res = generate_response_with_fallback(prompt, ["ERROR"])
        data = parse_json_response(res)
        if data and "text" in data:
            return data
    except Exception as e:
        logger.error(f"Error generating comprehension: {e}")
    
    return None

def generate_reading_exercise(topic: str, level: str) -> Dict[str, Any]:
    """Generate reading comprehension exercise."""
    prompt = f"""
    Act as an English teacher. Create a comprehensive reading lesson about '{topic}' (CEFR Level {level}).
    Length: 200-250 words.
    
    Return strictly JSON format:
    {{
        "title": "Title in English",
        "english_content": "Full English text...",
        "vietnamese_content": "Full Vietnamese translation...",
        "summary": "A brief summary of the text (1-2 sentences) in English.",
        "vocabulary": [
            {{"word": "word1", "type": "noun/verb...", "meaning": "Vietnamese meaning", "context": "Example sentence from text"}}
        ],
        "grammar": [
            {{"structure": "Name of structure", "explanation": "Brief explanation in Vietnamese", "example": "Example from text"}}
        ],
        "quiz": [
            {{"question": "Question 1?", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "explanation": "Why?"}},
            {{"question": "Question 2?", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "explanation": "Why?"}},
            {{"question": "Question 3?", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "explanation": "Why?"}}
        ]
    }}
    """
    
    try:
        res = generate_response_with_fallback(prompt, ["ERROR"])
        data = parse_json_response(res)
        if data and "english_content" in data:
            return data
    except Exception as e:
        logger.error(f"Error generating reading: {e}")
    
    return None

def generate_podcast_exercise(topic: str, level: str) -> Dict[str, Any]:
    """Generate podcast script exercise."""
    # Use "Trung bình (3-5 phút)" = "500-700 words" as default
    target_words = "500-700 words"
    pod_duration = "Trung bình (3-5 phút)"
    
    prompt = f"""
    Create a professional, engaging podcast episode about: {topic}.
    
    Requirements:
    - Length: {target_words} (approximately {pod_duration})
    - Level: {level} (CEFR) - use appropriate vocabulary and sentence complexity
    - Format: Structured podcast with clear segments
    - Characters: Host (Alice - Female, professional and engaging) and Guest (Bob - Male, knowledgeable expert)
    
    Structure:
    1. Introduction (Host welcomes listeners, introduces topic and guest)
    2. Main Discussion (3-4 key points about the topic, with Host asking questions and Guest providing insights)
    3. Examples/Case Studies (real-world applications or interesting facts)
    4. Conclusion (Host summarizes key takeaways, thanks guest, closing remarks)
    
    Content Guidelines:
    - Make it informative, engaging, and educational
    - Include natural conversation flow with questions and answers
    - Add interesting facts, examples, or anecdotes
    - Use appropriate transitions between segments
    - End with a memorable closing statement
    
    Format: JSON list of objects, each representing a speaking turn with BOTH English and Vietnamese:
    [
        {{"speaker": "Host", "text": "Welcome message and introduction in English...", "translation": "Bản dịch tiếng Việt tương ứng ở đây"}},
        {{"speaker": "Guest", "text": "Response and insights in English...", "translation": "Bản dịch tiếng Việt tương ứng ở đây"}},
        ...
    ]
    
    CRITICAL REQUIREMENTS:
    - Each object MUST include both "text" (English) and "translation" (Vietnamese) fields
    - Vietnamese translation should be natural, accurate, and help Vietnamese learners understand
    - Do not skip the translation field - it is required for all speaking turns
    
    Ensure the total dialogue is approximately {target_words} and covers the topic comprehensively.
    """
    
    try:
        res = generate_response_with_fallback(prompt, ["ERROR"])
        data = parse_json_response(res)
        if data and isinstance(data, list) and len(data) > 0:
            return data
    except Exception as e:
        logger.error(f"Error generating podcast: {e}")
    
    return None

def generate_exercises_for_topic(topic: str, exercise_type: str, max_exercises: int = SAMPLES_PER_TOPIC):
    """Generate exercises cho một topic và exercise type."""
    if not supabase:
        logger.error("Supabase client not initialized")
        return 0
    
    # Check how many already exist
    existing_count = count_existing_exercises(exercise_type, topic)
    if existing_count >= max_exercises:
        logger.info(f"  {exercise_type} - {topic}: Already has {existing_count} exercises, skipping")
        return 0
    
    needed = max_exercises - existing_count
    logger.info(f"  {exercise_type} - {topic}: Need {needed} more exercises (has {existing_count})")
    
    generated = 0
    failed = 0
    
    # Choose level distribution based on exercise type
    level_dist = PODCAST_LEVEL_DISTRIBUTION if exercise_type == "podcast_script" else LEVEL_DISTRIBUTION
    
    # Generate for each level
    for level, count in level_dist.items():
        for _ in range(count):
            if generated >= needed:
                break
            
            # Generate exercise based on type
            if exercise_type == "dictation":
                exercise_data = generate_dictation_exercise(topic, level)
            elif exercise_type == "comprehension":
                exercise_data = generate_comprehension_exercise(topic, level)
            elif exercise_type == "reading_question":
                exercise_data = generate_reading_exercise(topic, level)
            elif exercise_type == "podcast_script":
                exercise_data = generate_podcast_exercise(topic, level)
            else:
                logger.warning(f"Unknown exercise type: {exercise_type}")
                continue
            
            if exercise_data:
                # Save to database
                try:
                    exercise_id = save_exercise(
                        exercise_type=exercise_type,
                        level=level,
                        topic=topic,
                        exercise_data=exercise_data,
                        user_id=None  # System-generated
                    )
                    if exercise_id:
                        generated += 1
                        logger.info(f"    Generated {exercise_type} - {topic} - {level} (ID: {exercise_id})")
                    else:
                        failed += 1
                        logger.warning(f"    Failed to save {exercise_type} - {topic} - {level}")
                except Exception as e:
                    failed += 1
                    logger.error(f"    Error saving exercise: {e}")
            else:
                failed += 1
                logger.warning(f"    Failed to generate {exercise_type} - {topic} - {level}")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
    
    return generated

def generate_all_exercises(topics: List[str] = None, exercise_types: List[str] = None, start_from: int = 0):
    """
    Generate exercises cho tất cả topics.
    
    Args:
        topics: List topics to generate (None = all)
        exercise_types: List exercise types to generate (None = all)
        start_from: Start from this topic index (for resuming)
    """
    if not supabase:
        logger.error("Supabase client not initialized")
        return
    
    if topics is None:
        topics = VALID_TOPICS
    
    if exercise_types is None:
        exercise_types = EXERCISE_TYPES
    
    logger.info("=" * 60)
    logger.info("Exercise Generation Script")
    logger.info("=" * 60)
    logger.info(f"Total topics: {len(topics)}")
    logger.info(f"Exercise types: {exercise_types}")
    logger.info(f"Starting from topic index: {start_from}")
    logger.info(f"Samples per topic: {SAMPLES_PER_TOPIC}")
    logger.info("")
    
    total_generated = 0
    total_failed = 0
    
    # Process topics from start_from
    for topic_idx, topic in enumerate(topics[start_from:], start=start_from):
        logger.info(f"[{topic_idx + 1}/{len(topics)}] Processing topic: {topic}")
        
        for exercise_type in exercise_types:
            try:
                generated = generate_exercises_for_topic(topic, exercise_type)
                total_generated += generated
            except Exception as e:
                logger.error(f"Error processing {exercise_type} - {topic}: {e}")
                total_failed += 1
        
        # Delay between topics
        time.sleep(1)
        
        # Progress update every 10 topics
        if (topic_idx + 1) % 10 == 0:
            logger.info("")
            logger.info(f"Progress: {topic_idx + 1}/{len(topics)} topics")
            logger.info(f"Generated so far: {total_generated} exercises")
            logger.info("")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("GENERATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total generated: {total_generated}")
    logger.info(f"Total failed: {total_failed}")
    logger.info("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample exercises for topics")
    parser.add_argument("--topics", type=int, help="Number of topics to process (default: all)")
    parser.add_argument("--start", type=int, default=0, help="Start from topic index (default: 0)")
    parser.add_argument("--type", choices=EXERCISE_TYPES, help="Generate only this exercise type")
    parser.add_argument("--check", action="store_true", help="Only check existing counts, don't generate")
    
    args = parser.parse_args()
    
    if args.check:
        # Just check counts
        logger.info("Checking existing exercises...")
        for topic in VALID_TOPICS[:10]:  # Check first 10
            for ex_type in EXERCISE_TYPES:
                count = count_existing_exercises(ex_type, topic)
                logger.info(f"{ex_type} - {topic}: {count} exercises")
    else:
        # Generate
        topics_to_process = VALID_TOPICS[:args.topics] if args.topics else VALID_TOPICS
        exercise_types_to_process = [args.type] if args.type else EXERCISE_TYPES
        
        generate_all_exercises(
            topics=topics_to_process,
            exercise_types=exercise_types_to_process,
            start_from=args.start
        )
