"""
Script để kiểm tra Vocabulary database xem có duplicate không.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_duplicates():
    """Kiểm tra từ vựng trùng lặp."""
    if not supabase:
        logger.error("Supabase client not initialized")
        return
    
    print("=" * 60)
    print("Vocabulary Duplicate Check")
    print("=" * 60)
    
    try:
        # Get all vocabulary
        result = supabase.table("Vocabulary").select("id, word, level").execute()
        all_words = result.data if result.data else []
        
        print(f"\nTotal words in database: {len(all_words)}")
        
        # Find duplicates (case-insensitive)
        word_counts = {}
        duplicates = []
        
        for item in all_words:
            word_lower = item['word'].lower().strip()
            if word_lower not in word_counts:
                word_counts[word_lower] = []
            word_counts[word_lower].append(item)
        
        # Find words that appear multiple times
        for word_lower, items in word_counts.items():
            if len(items) > 1:
                duplicates.append({
                    'word': word_lower,
                    'count': len(items),
                    'items': items
                })
        
        print(f"\nDuplicate words found: {len(duplicates)}")
        
        if duplicates:
            print("\nTop 20 duplicates:")
            # Sort by count descending
            duplicates.sort(key=lambda x: x['count'], reverse=True)
            for i, dup in enumerate(duplicates[:20], 1):
                print(f"\n{i}. '{dup['word']}' appears {dup['count']} times:")
                for item in dup['items']:
                    print(f"   - ID: {item['id']}, Level: {item.get('level', 'N/A')}, Word: {item['word']}")
        else:
            print("\nNo duplicates found! OK")
        
        return duplicates
        
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        return []

def check_level_distribution():
    """Kiểm tra phân bổ từ vựng theo level."""
    if not supabase:
        return
    
    print("\n" + "=" * 60)
    print("Vocabulary Level Distribution")
    print("=" * 60)
    
    try:
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        distribution = {}
        
        for level in levels:
            result = supabase.table("Vocabulary").select("id", count="exact").eq("level", level).execute()
            count = result.count if hasattr(result, 'count') else len(result.data or [])
            distribution[level] = count
        
        print("\nWords by level:")
        total = 0
        for level in levels:
            count = distribution.get(level, 0)
            total += count
            # Visual bar
            bar_length = int(count / 100)  # 1 char = 100 words
            bar = "|" * min(bar_length, 50)  # Limit bar length
            print(f"{level}: {count:5d} words {bar}")
        
        print(f"\nTotal: {total} words")
        
        # Recommend which levels need more words
        print("\nRecommendations:")
        avg_count = total / len(levels)
        for level in levels:
            count = distribution.get(level, 0)
            if count < avg_count * 0.8:  # Less than 80% of average
                needed = int(avg_count - count)
                print(f"  {level}: Consider adding ~{needed} more words (current: {count})")
        
        return distribution
        
    except Exception as e:
        logger.error(f"Error checking level distribution: {e}")
        return {}

if __name__ == "__main__":
    duplicates = check_duplicates()
    distribution = check_level_distribution()
    
    print("\n" + "=" * 60)
    print("Check Complete!")
    print("=" * 60)
