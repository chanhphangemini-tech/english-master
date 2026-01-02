from datetime import datetime, timedelta, timezone
from core.timezone_utils import get_vn_now_utc

def calculate_review_schedule(quality: int, last_interval: int, last_ease: float, last_streak: int):
    """
    Tính toán lịch ôn tập tiếp theo dựa trên thuật toán SuperMemo-2 (SM-2).
    
    Args:
        quality (int): Đánh giá của người dùng (0-5).
                       0-2: Quên/Sai (Học lại).
                       3: Nhớ khó khăn.
                       4: Nhớ được.
                       5: Nhớ hoàn hảo.
        last_interval (int): Khoảng cách ngày của lần trước (days).
        last_ease (float): Hệ số dễ (Ease Factor) của lần trước (mặc định 2.5).
        last_streak (int): Chuỗi nhớ liên tục hiện tại.

    Returns:
        dict: {
            'next_review': datetime (UTC),
            'interval': int (days),
            'ease_factor': float,
            'streak': int,
            'status': str ('learning', 'review', 'mastered')
        }
    """
    
    new_interval = 0
    new_ease = last_ease
    new_streak = last_streak

    # Nếu đánh giá < 3 (Quên), reset lại từ đầu
    if quality < 3:
        new_streak = 0
        new_interval = 1
    else:
        # Nếu nhớ (>= 3), tăng streak và tính interval mới
        new_streak += 1
        
        if new_streak == 1:
            new_interval = 1
        elif new_streak == 2:
            new_interval = 6
        else:
            new_interval = int(round(last_interval * last_ease))

        # Cập nhật Ease Factor (Công thức chuẩn SM-2)
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ease = last_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Ease Factor không được nhỏ hơn 1.3
        if new_ease < 1.3:
            new_ease = 1.3

    # Tính ngày review tiếp theo (dùng VN timezone, convert sang UTC)
    now_vn_utc = datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00'))
    next_review_date = now_vn_utc + timedelta(days=new_interval)

    return {
        "next_review": next_review_date,
        "interval": new_interval,
        "ease_factor": round(new_ease, 2),
        "streak": new_streak,
        "status": "review" if new_streak < 5 else "mastered" # Giả định nhớ 5 lần liên tiếp là Mastered
    }