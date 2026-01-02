"""
Script để thêm từ vựng mới cho các level A1, A2, C1 (những level còn thiếu).
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import supabase
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Từ vựng A1 phổ biến (bổ sung thêm)
A1_WORDS = [
    {"word": "book", "pronunciation": "/bʊk/", "meaning": "sách", "type": "noun", "level": "A1", "topic": "Education", "example": "I read a book every day.", "example_translation": "Tôi đọc một cuốn sách mỗi ngày."},
    {"word": "pen", "pronunciation": "/pen/", "meaning": "bút", "type": "noun", "level": "A1", "topic": "Daily Life", "example": "Can I borrow your pen?", "example_translation": "Tôi có thể mượn bút của bạn không?"},
    {"word": "chair", "pronunciation": "/tʃeər/", "meaning": "ghế", "type": "noun", "level": "A1", "topic": "Daily Life", "example": "Please sit on the chair.", "example_translation": "Vui lòng ngồi trên ghế."},
    {"word": "table", "pronunciation": "/ˈteɪbəl/", "meaning": "bàn", "type": "noun", "level": "A1", "topic": "Daily Life", "example": "The table is round.", "example_translation": "Cái bàn tròn."},
    {"word": "door", "pronunciation": "/dɔːr/", "meaning": "cửa", "type": "noun", "level": "A1", "topic": "Daily Life", "example": "Close the door, please.", "example_translation": "Vui lòng đóng cửa."},
    {"word": "window", "pronunciation": "/ˈwɪndəʊ/", "meaning": "cửa sổ", "type": "noun", "level": "A1", "topic": "Daily Life", "example": "Open the window.", "example_translation": "Mở cửa sổ."},
    {"word": "wall", "pronunciation": "/wɔːl/", "meaning": "tường", "type": "noun", "level": "A1", "topic": "Housing", "example": "The wall is white.", "example_translation": "Bức tường màu trắng."},
    {"word": "floor", "pronunciation": "/flɔːr/", "meaning": "sàn nhà", "type": "noun", "level": "A1", "topic": "Housing", "example": "The floor is clean.", "example_translation": "Sàn nhà sạch."},
    {"word": "ceiling", "pronunciation": "/ˈsiːlɪŋ/", "meaning": "trần nhà", "type": "noun", "level": "A1", "topic": "Housing", "example": "The ceiling is high.", "example_translation": "Trần nhà cao."},
    {"word": "room", "pronunciation": "/ruːm/", "meaning": "phòng", "type": "noun", "level": "A1", "topic": "Housing", "example": "This room is big.", "example_translation": "Căn phòng này lớn."},
]

# Từ vựng A2 phổ biến (bổ sung thêm)
A2_WORDS = [
    {"word": "comfortable", "pronunciation": "/ˈkʌmftəbəl/", "meaning": "thoải mái", "type": "adjective", "level": "A2", "topic": "Daily Life", "example": "This sofa is very comfortable.", "example_translation": "Chiếc ghế sofa này rất thoải mái."},
    {"word": "expensive", "pronunciation": "/ɪkˈspensɪv/", "meaning": "đắt", "type": "adjective", "level": "A2", "topic": "Shopping", "example": "This car is too expensive.", "example_translation": "Chiếc xe này quá đắt."},
    {"word": "cheap", "pronunciation": "/tʃiːp/", "meaning": "rẻ", "type": "adjective", "level": "A2", "topic": "Shopping", "example": "This shirt is cheap.", "example_translation": "Chiếc áo này rẻ."},
    {"word": "difficult", "pronunciation": "/ˈdɪfɪkəlt/", "meaning": "khó", "type": "adjective", "level": "A2", "topic": "Education", "example": "Math is difficult for me.", "example_translation": "Toán khó đối với tôi."},
    {"word": "easy", "pronunciation": "/ˈiːzi/", "meaning": "dễ", "type": "adjective", "level": "A2", "topic": "Education", "example": "This exercise is easy.", "example_translation": "Bài tập này dễ."},
    {"word": "important", "pronunciation": "/ɪmˈpɔːtənt/", "meaning": "quan trọng", "type": "adjective", "level": "A2", "topic": "Daily Life", "example": "Health is important.", "example_translation": "Sức khỏe quan trọng."},
    {"word": "interesting", "pronunciation": "/ˈɪntrəstɪŋ/", "meaning": "thú vị", "type": "adjective", "level": "A2", "topic": "Entertainment", "example": "This movie is interesting.", "example_translation": "Bộ phim này thú vị."},
    {"word": "boring", "pronunciation": "/ˈbɔːrɪŋ/", "meaning": "nhàm chán", "type": "adjective", "level": "A2", "topic": "Entertainment", "example": "The lecture was boring.", "example_translation": "Bài giảng nhàm chán."},
    {"word": "beautiful", "pronunciation": "/ˈbjuːtɪfəl/", "meaning": "đẹp", "type": "adjective", "level": "A2", "topic": "Daily Life", "example": "She is beautiful.", "example_translation": "Cô ấy đẹp."},
    {"word": "useful", "pronunciation": "/ˈjuːsfʊl/", "meaning": "hữu ích", "type": "adjective", "level": "A2", "topic": "Daily Life", "example": "This tool is useful.", "example_translation": "Công cụ này hữu ích."},
]

# Từ vựng C1 phổ biến (bổ sung thêm)
C1_WORDS = [
    {"word": "ambiguous", "pronunciation": "/æmˈbɪɡjuəs/", "meaning": "mơ hồ, không rõ ràng", "type": "adjective", "level": "C1", "topic": "Education", "example": "The instructions were ambiguous.", "example_translation": "Hướng dẫn mơ hồ."},
    {"word": "comprehensive", "pronunciation": "/ˌkɒmprɪˈhensɪv/", "meaning": "toàn diện", "type": "adjective", "level": "C1", "topic": "Education", "example": "We need a comprehensive plan.", "example_translation": "Chúng ta cần một kế hoạch toàn diện."},
    {"word": "controversial", "pronunciation": "/ˌkɒntrəˈvɜːʃəl/", "meaning": "gây tranh cãi", "type": "adjective", "level": "C1", "topic": "News", "example": "This is a controversial topic.", "example_translation": "Đây là chủ đề gây tranh cãi."},
    {"word": "substantial", "pronunciation": "/səbˈstænʃəl/", "meaning": "đáng kể", "type": "adjective", "level": "C1", "topic": "Business", "example": "There was a substantial increase.", "example_translation": "Có sự gia tăng đáng kể."},
    {"word": "sophisticated", "pronunciation": "/səˈfɪstɪkeɪtɪd/", "meaning": "tinh vi, phức tạp", "type": "adjective", "level": "C1", "topic": "Technology", "example": "This is a sophisticated system.", "example_translation": "Đây là hệ thống tinh vi."},
    {"word": "inevitable", "pronunciation": "/ɪˈnevɪtəbəl/", "meaning": "không thể tránh khỏi", "type": "adjective", "level": "C1", "topic": "Daily Life", "example": "Change is inevitable.", "example_translation": "Thay đổi là không thể tránh khỏi."},
    {"word": "profound", "pronunciation": "/prəˈfaʊnd/", "meaning": "sâu sắc", "type": "adjective", "level": "C1", "topic": "Education", "example": "He made a profound impact.", "example_translation": "Anh ấy tạo ra tác động sâu sắc."},
    {"word": "explicit", "pronunciation": "/ɪkˈsplɪsɪt/", "meaning": "rõ ràng, minh bạch", "type": "adjective", "level": "C1", "topic": "Education", "example": "Please give explicit instructions.", "example_translation": "Vui lòng đưa ra hướng dẫn rõ ràng."},
    {"word": "implicit", "pronunciation": "/ɪmˈplɪsɪt/", "meaning": "ngầm, ẩn ý", "type": "adjective", "level": "C1", "topic": "Education", "example": "There is an implicit understanding.", "example_translation": "Có một sự hiểu biết ngầm."},
    {"word": "elaborate", "pronunciation": "/ɪˈlæbərət/", "meaning": "chi tiết, phức tạp", "type": "adjective", "level": "C1", "topic": "Education", "example": "He gave an elaborate explanation.", "example_translation": "Anh ấy đưa ra lời giải thích chi tiết."},
]

def check_word_exists(word: str, level: str) -> bool:
    """Kiểm tra từ đã tồn tại chưa (case-insensitive)."""
    try:
        result = supabase.table("Vocabulary").select("id").eq("level", level).ilike("word", word).execute()
        return len(result.data or []) > 0
    except Exception as e:
        logger.error(f"Error checking word {word}: {e}")
        return False

def add_vocabulary_words(level: str, words: list):
    """Thêm từ vựng vào database."""
    if not supabase:
        logger.error("Supabase client not initialized")
        return
    
    logger.info(f"Processing {len(words)} words for level {level}...")
    
    added = 0
    skipped = 0
    errors = 0
    
    for word_data in words:
        word = word_data.get('word', '').strip().lower()
        
        if not word:
            continue
        
        # Check if word already exists
        if check_word_exists(word, level):
            skipped += 1
            logger.debug(f"  Skipped: {word} (already exists)")
            continue
        
        try:
            # Prepare data
            insert_data = {
                "word": word_data['word'],
                "pronunciation": word_data.get('pronunciation', ''),
                "meaning": word_data.get('meaning', ''),
                "type": word_data.get('type', 'noun'),
                "level": level,
                "topic": word_data.get('topic'),
                "example": word_data.get('example', ''),
                "example_translation": word_data.get('example_translation', '')
            }
            
            # Insert
            result = supabase.table("Vocabulary").insert(insert_data).execute()
            
            if result.data:
                added += 1
                logger.info(f"  Added: {word}")
            else:
                errors += 1
                logger.warning(f"  Failed to add: {word}")
                
        except Exception as e:
            errors += 1
            logger.error(f"  Error adding {word}: {e}")
    
    logger.info(f"\nLevel {level} Summary:")
    logger.info(f"  Added: {added}")
    logger.info(f"  Skipped: {skipped}")
    logger.info(f"  Errors: {errors}")

def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Vocabulary Addition Script")
    logger.info("=" * 60)
    
    # Note: This script only adds a small sample (10 words per level)
    # For production, you would need a much larger vocabulary list
    # or use an API/dataset to get comprehensive vocabulary lists
    
    logger.info("\nNote: This script adds sample words only.")
    logger.info("For full vocabulary expansion, use a comprehensive vocabulary dataset.")
    logger.info("")
    
    # Add A1 words
    add_vocabulary_words("A1", A1_WORDS)
    
    # Add A2 words
    add_vocabulary_words("A2", A2_WORDS)
    
    # Add C1 words
    add_vocabulary_words("C1", C1_WORDS)
    
    logger.info("\n" + "=" * 60)
    logger.info("Vocabulary Addition Complete!")
    logger.info("=" * 60)
    logger.info("\nNote: Only sample words added.")
    logger.info("To add more words, expand the word lists in this script")
    logger.info("or use an external vocabulary database/API.")

if __name__ == "__main__":
    main()
