"""
Timezone Utilities
Helper functions để làm việc với múi giờ Việt Nam (UTC+7)
"""
from datetime import datetime, timezone, timedelta

# Vietnam timezone: UTC+7
VN_TIMEZONE = timezone(timedelta(hours=7))

def get_vn_now():
    """
    Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)
    
    Returns:
        datetime: Current time in Vietnam timezone
    """
    return datetime.now(VN_TIMEZONE)

def get_vn_now_utc():
    """
    Lấy thời gian hiện tại theo múi giờ Việt Nam, nhưng convert sang UTC để lưu vào database
    
    Returns:
        str: ISO format string in UTC timezone (for database storage)
    """
    return datetime.now(VN_TIMEZONE).astimezone(timezone.utc).isoformat()

def get_vn_start_of_day_utc():
    """
    Lấy thời gian bắt đầu ngày hôm nay (00:00:00) theo múi giờ Việt Nam, convert sang UTC
    
    Returns:
        str: ISO format string in UTC timezone
    """
    now_vn = datetime.now(VN_TIMEZONE)
    start_of_day_vn = now_vn.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_of_day_vn.astimezone(timezone.utc).isoformat()

def get_vn_start_of_week_utc():
    """
    Lấy thời gian bắt đầu tuần (Monday 00:00:00) theo múi giờ Việt Nam, convert sang UTC
    
    Returns:
        str: ISO format string in UTC timezone
    """
    now_vn = datetime.now(VN_TIMEZONE)
    days_since_monday = now_vn.weekday()
    start_of_week_vn = (now_vn - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start_of_week_vn.astimezone(timezone.utc).isoformat()

def get_vn_today_str():
    """
    Lấy ngày hôm nay theo định dạng YYYY-MM-DD (múi giờ Việt Nam)
    
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    return datetime.now(VN_TIMEZONE).strftime('%Y-%m-%d')

def get_vn_start_of_month_utc():
    """
    Lấy thời gian bắt đầu tháng hiện tại (ngày 1, 00:00:00) theo múi giờ Việt Nam, convert sang UTC
    
    Returns:
        str: ISO format string in UTC timezone (for database storage)
    """
    now_vn = datetime.now(VN_TIMEZONE)
    start_of_month_vn = now_vn.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start_of_month_vn.astimezone(timezone.utc).isoformat()

