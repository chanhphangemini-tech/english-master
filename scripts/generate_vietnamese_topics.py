"""
Script để tạo danh sách 50+ chủ đề bằng tiếng Việt cho exercises.
Mỗi chủ đề sẽ có 5 mẫu exercises.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import supabase
from services.exercise_cache_service import save_exercise
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Danh sách 50+ chủ đề bằng tiếng Việt (dễ hiểu cho học viên)
VIETNAMESE_TOPICS = [
    # Cuộc sống hàng ngày (10)
    "Cuộc sống hàng ngày", "Gia đình", "Bạn bè", "Nhà ở", "Đồ ăn và nấu ăn",
    "Mua sắm", "Thời trang", "Sức khỏe", "Thể thao và tập luyện", "Sở thích",
    
    # Học tập & Công việc (10)
    "Học tập", "Trường học", "Công việc", "Nghề nghiệp", "Kinh doanh",
    "Kỹ năng", "Du học", "Thi cử", "Dự án", "Thành tựu",
    
    # Du lịch & Văn hóa (10)
    "Du lịch", "Điểm đến", "Phương tiện đi lại", "Khách sạn", "Văn hóa",
    "Lễ hội", "Truyền thống", "Lịch sử", "Nghệ thuật", "Âm nhạc",
    
    # Công nghệ & Khoa học (10)
    "Công nghệ", "Internet", "Điện thoại", "Máy tính", "Khoa học",
    "Thiên nhiên", "Môi trường", "Khí hậu", "Y học", "Nghiên cứu",
    
    # Giải trí & Truyền thông (10)
    "Phim ảnh", "Sách", "Trò chơi", "Truyền hình", "Tin tức",
    "Mạng xã hội", "Blog", "Podcast", "Radio", "Báo chí",
    
    # Xã hội & Quan hệ (10)
    "Tình yêu", "Hẹn hò", "Hôn nhân", "Trẻ em", "Người cao tuổi",
    "Cộng đồng", "Tình nguyện", "Giúp đỡ", "Tình bạn", "Mối quan hệ",
    
    # Tài chính & Kinh tế (5)
    "Tiền bạc", "Ngân hàng", "Đầu tư", "Tiết kiệm", "Mua bán",
    
    # Các chủ đề khác (5)
    "Thời tiết", "Động vật", "Thực vật", "Thiên nhiên", "Khám phá",
]

# Mapping từ tiếng Việt sang English (để lưu trong DB - dùng English)
TOPIC_MAPPING = {
    # Cuộc sống hàng ngày
    "Cuộc sống hàng ngày": "Daily Life",
    "Gia đình": "Family",
    "Bạn bè": "Friends",
    "Nhà ở": "Housing",
    "Đồ ăn và nấu ăn": "Food & Cooking",
    "Mua sắm": "Shopping",
    "Thời trang": "Fashion",
    "Sức khỏe": "Health",
    "Thể thao và tập luyện": "Sports & Fitness",
    "Sở thích": "Hobbies",
    
    # Học tập & Công việc
    "Học tập": "Education",
    "Trường học": "School",
    "Công việc": "Work",
    "Nghề nghiệp": "Career",
    "Kinh doanh": "Business",
    "Kỹ năng": "Skills",
    "Du học": "Study Abroad",
    "Thi cử": "Exams",
    "Dự án": "Projects",
    "Thành tựu": "Achievements",
    
    # Du lịch & Văn hóa
    "Du lịch": "Travel",
    "Điểm đến": "Destinations",
    "Phương tiện đi lại": "Transportation",
    "Khách sạn": "Hotels",
    "Văn hóa": "Culture",
    "Lễ hội": "Festivals",
    "Truyền thống": "Traditions",
    "Lịch sử": "History",
    "Nghệ thuật": "Art",
    "Âm nhạc": "Music",
    
    # Công nghệ & Khoa học
    "Công nghệ": "Technology",
    "Internet": "Internet",
    "Điện thoại": "Mobile Phones",
    "Máy tính": "Computers",
    "Khoa học": "Science",
    "Thiên nhiên": "Nature",
    "Môi trường": "Environment",
    "Khí hậu": "Climate",
    "Y học": "Medicine",
    "Nghiên cứu": "Research",
    
    # Giải trí & Truyền thông
    "Phim ảnh": "Movies",
    "Sách": "Books",
    "Trò chơi": "Games",
    "Truyền hình": "TV",
    "Tin tức": "News",
    "Mạng xã hội": "Social Media",
    "Blog": "Blogs",
    "Podcast": "Podcasts",
    "Radio": "Radio",
    "Báo chí": "Journalism",
    
    # Xã hội & Quan hệ
    "Tình yêu": "Love",
    "Hẹn hò": "Dating",
    "Hôn nhân": "Marriage",
    "Trẻ em": "Children",
    "Người cao tuổi": "Elderly",
    "Cộng đồng": "Community",
    "Tình nguyện": "Volunteering",
    "Giúp đỡ": "Helping",
    "Tình bạn": "Friendship",
    "Mối quan hệ": "Relationships",
    
    # Tài chính & Kinh tế
    "Tiền bạc": "Money",
    "Ngân hàng": "Banking",
    "Đầu tư": "Investment",
    "Tiết kiệm": "Savings",
    "Mua bán": "Trade",
    
    # Các chủ đề khác
    "Thời tiết": "Weather",
    "Động vật": "Animals",
    "Thực vật": "Plants",
    "Khám phá": "Exploration",
}

def get_topic_english(vietnamese_topic):
    """Lấy English topic name từ Vietnamese."""
    return TOPIC_MAPPING.get(vietnamese_topic, vietnamese_topic)

# Update VALID_TOPICS trong exercise_cache_service
def update_valid_topics():
    """Update VALID_TOPICS list trong exercise_cache_service.py"""
    # This will be done manually in the file
    pass

print(f"Total Vietnamese topics: {len(VIETNAMESE_TOPICS)}")
print(f"Topics by category:")
categories = {
    "Cuộc sống hàng ngày": VIETNAMESE_TOPICS[0:10],
    "Học tập & Công việc": VIETNAMESE_TOPICS[10:20],
    "Du lịch & Văn hóa": VIETNAMESE_TOPICS[20:30],
    "Công nghệ & Khoa học": VIETNAMESE_TOPICS[30:40],
    "Giải trí & Truyền thông": VIETNAMESE_TOPICS[40:50],
    "Xã hội & Quan hệ": VIETNAMESE_TOPICS[50:60],
    "Tài chính & Kinh tế": VIETNAMESE_TOPICS[60:65],
    "Các chủ đề khác": VIETNAMESE_TOPICS[65:70],
}

for category, topics in categories.items():
    print(f"\n{category}: {len(topics)} topics")
