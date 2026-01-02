"""
Script to check vocabulary details generation progress.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import supabase
import pandas as pd

def check_progress():
    """Check vocabulary details generation progress."""
    
    # Get overall stats
    query_overall = """
    SELECT 
        COUNT(*) as total_words,
        COUNT(*) FILTER (WHERE collocations IS NOT NULL OR word_forms IS NOT NULL OR synonyms IS NOT NULL OR usage_notes IS NOT NULL OR phrasal_verbs IS NOT NULL) as words_with_details,
        COUNT(*) FILTER (WHERE collocations IS NULL AND word_forms IS NULL AND synonyms IS NULL AND usage_notes IS NULL AND phrasal_verbs IS NULL) as words_without_details,
        ROUND(COUNT(*) FILTER (WHERE collocations IS NOT NULL OR word_forms IS NOT NULL OR synonyms IS NOT NULL OR usage_notes IS NOT NULL OR phrasal_verbs IS NOT NULL)::numeric / COUNT(*) * 100, 2) as overall_completion_percent
    FROM "Vocabulary"
    """
    
    # Get stats by level
    query_by_level = """
    WITH vocab_stats AS (
        SELECT 
            level,
            COUNT(*) as total_words,
            COUNT(*) FILTER (WHERE collocations IS NOT NULL OR word_forms IS NOT NULL OR synonyms IS NOT NULL OR usage_notes IS NOT NULL OR phrasal_verbs IS NOT NULL) as words_with_details,
            COUNT(*) FILTER (WHERE collocations IS NOT NULL) as with_collocations,
            COUNT(*) FILTER (WHERE word_forms IS NOT NULL) as with_word_forms,
            COUNT(*) FILTER (WHERE synonyms IS NOT NULL) as with_synonyms,
            COUNT(*) FILTER (WHERE usage_notes IS NOT NULL) as with_usage_notes,
            COUNT(*) FILTER (WHERE phrasal_verbs IS NOT NULL) as with_phrasal_verbs
        FROM "Vocabulary"
        GROUP BY level
    )
    SELECT 
        level,
        total_words,
        words_with_details,
        total_words - words_with_details as words_missing_details,
        ROUND(words_with_details::numeric / total_words * 100, 2) as completion_percent,
        with_collocations,
        with_word_forms,
        with_synonyms,
        with_usage_notes,
        with_phrasal_verbs
    FROM vocab_stats
    ORDER BY 
        CASE level 
            WHEN 'A1' THEN 1 
            WHEN 'A2' THEN 2 
            WHEN 'B1' THEN 3 
            WHEN 'B2' THEN 4 
            WHEN 'C1' THEN 5 
            WHEN 'C2' THEN 6 
        END
    """
    
    try:
        # Overall stats
        result_overall = supabase.rpc('exec_sql', {'query': query_overall}).execute()
        if result_overall.data:
            overall = result_overall.data[0]
            print("="*70)
            print("📊 TỔNG KẾT TIẾN TRÌNH GENERATE VOCABULARY DETAILS")
            print("="*70)
            print(f"Tổng số từ vựng: {overall['total_words']}")
            print(f"Đã có chi tiết: {overall['words_with_details']}")
            print(f"Chưa có chi tiết: {overall['words_without_details']}")
            print(f"Hoàn thành: {overall['overall_completion_percent']}%")
            print("="*70)
        
        # Stats by level
        result_levels = supabase.rpc('exec_sql', {'query': query_by_level}).execute()
        if result_levels.data:
            print("\n📈 TIẾN TRÌNH THEO TỪNG LEVEL:\n")
            df = pd.DataFrame(result_levels.data)
            print(df.to_string(index=False))
            print("\n")
            
            # Summary
            total_missing = df['words_missing_details'].sum()
            print(f"📝 Tổng số từ còn thiếu chi tiết: {total_missing}")
            
    except Exception as e:
        # Fallback: use direct query
        try:
            # Get all vocab
            all_vocab = supabase.table("Vocabulary").select("level, collocations, word_forms, synonyms, usage_notes, phrasal_verbs").execute()
            
            if all_vocab.data:
                df = pd.DataFrame(all_vocab.data)
                
                # Calculate stats
                total = len(df)
                has_details = df.apply(lambda row: any([
                    row.get('collocations'),
                    row.get('word_forms'),
                    row.get('synonyms'),
                    row.get('usage_notes'),
                    row.get('phrasal_verbs')
                ]), axis=1).sum()
                
                print("="*70)
                print("📊 TỔNG KẾT TIẾN TRÌNH GENERATE VOCABULARY DETAILS")
                print("="*70)
                print(f"Tổng số từ vựng: {total}")
                print(f"Đã có chi tiết: {has_details}")
                print(f"Chưa có chi tiết: {total - has_details}")
                print(f"Hoàn thành: {has_details/total*100:.2f}%")
                print("="*70)
                
                # By level
                print("\n📈 TIẾN TRÌNH THEO TỪNG LEVEL:\n")
                level_stats = []
                for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
                    level_df = df[df['level'] == level]
                    if len(level_df) > 0:
                        level_total = len(level_df)
                        level_has_details = level_df.apply(lambda row: any([
                            row.get('collocations'),
                            row.get('word_forms'),
                            row.get('synonyms'),
                            row.get('usage_notes'),
                            row.get('phrasal_verbs')
                        ]), axis=1).sum()
                        level_stats.append({
                            'level': level,
                            'total_words': level_total,
                            'words_with_details': level_has_details,
                            'words_missing_details': level_total - level_has_details,
                            'completion_percent': round(level_has_details/level_total*100, 2)
                        })
                
                stats_df = pd.DataFrame(level_stats)
                print(stats_df.to_string(index=False))
                print("\n")
                
        except Exception as e2:
            print(f"❌ Error: {e2}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_progress()
