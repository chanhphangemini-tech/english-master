"""
Error Messages & User Feedback - Centralized error message definitions

This module provides user-friendly error messages and feedback strings
to ensure consistent communication across the app.

Author: AI Assistant
Date: 2025-12-30
"""

import streamlit as st
from typing import Optional


# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_MESSAGES = {
    # Authentication errors
    "auth_failed": "❌ Đăng nhập thất bại. Vui lòng kiểm tra lại tên đăng nhập và mật khẩu.",
    "auth_invalid_username": "❌ Tên đăng nhập không hợp lệ. Vui lòng chỉ sử dụng chữ cái, số và dấu gạch dưới.",
    "auth_invalid_email": "❌ Địa chỉ email không hợp lệ.",
    "auth_weak_password": "❌ Mật khẩu quá yếu. Vui lòng sử dụng ít nhất 8 ký tự với chữ hoa, chữ thường và số.",
    "auth_password_mismatch": "❌ Mật khẩu xác nhận không khớp.",
    "account_locked": "🔒 Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Admin để được hỗ trợ.",
    "account_not_found": "❌ Không tìm thấy tài khoản. Vui lòng kiểm tra lại thông tin.",
    "username_exists": "❌ Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.",
    "email_exists": "❌ Email đã được sử dụng. Vui lòng dùng email khác hoặc đăng nhập.",
    
    # Network & Connection errors
    "network_error": "🌐 Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng và thử lại.",
    "network_timeout": "⏱️ Kết nối quá chậm hoặc bị gián đoạn. Vui lòng thử lại.",
    "server_error": "🔧 Server đang gặp sự cố. Chúng tôi đang khắc phục, vui lòng thử lại sau.",
    
    # Data loading errors
    "data_load_failed": "📂 Không thể tải dữ liệu. Vui lòng thử lại sau.",
    "data_empty": "📭 Không có dữ liệu để hiển thị.",
    "data_corrupted": "⚠️ Dữ liệu bị lỗi. Vui lòng báo Admin.",
    
    # Feature access errors
    "premium_required": "⭐ Tính năng này dành cho tài khoản Premium. Nâng cấp ngay để trải nghiệm!",
    "feature_locked": "🔒 Tính năng này đang được phát triển và sẽ sớm ra mắt.",
    "daily_limit_reached": "⏰ Bạn đã sử dụng hết lượt miễn phí hôm nay. Quay lại vào ngày mai hoặc nâng cấp Premium!",
    "ai_limit_reached": "🤖 Bạn đã hết lượt sử dụng AI cho hôm nay. Nâng cấp Premium để không giới hạn!",
    
    # Form validation errors
    "form_incomplete": "📝 Vui lòng điền đầy đủ tất cả thông tin bắt buộc.",
    "form_invalid_input": "⚠️ Thông tin nhập vào không hợp lệ. Vui lòng kiểm tra lại.",
    
    # Quiz & Test errors
    "quiz_not_started": "❌ Bài quiz chưa được bắt đầu. Vui lòng tạo bài mới.",
    "quiz_already_submitted": "✅ Bạn đã nộp bài này rồi. Không thể sửa đổi.",
    "test_time_expired": "⏰ Hết giờ làm bài! Kết quả sẽ được tự động nộp.",
    
    # File & Upload errors
    "upload_failed": "📤 Upload file thất bại. Vui lòng thử lại.",
    "file_too_large": "📦 File quá lớn. Kích thước tối đa: 5MB.",
    "file_invalid_format": "📄 Định dạng file không được hỗ trợ.",
    
    # Generic errors
    "unknown_error": "❓ Đã có lỗi không xác định xảy ra. Vui lòng thử lại hoặc liên hệ hỗ trợ.",
    "permission_denied": "🚫 Bạn không có quyền thực hiện thao tác này.",
}


# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

SUCCESS_MESSAGES = {
    # Authentication
    "login_success": "✅ Đăng nhập thành công! Chào mừng bạn quay lại.",
    "logout_success": "👋 Đăng xuất thành công. Hẹn gặp lại!",
    "register_success": "🎉 Đăng ký thành công! Hãy đăng nhập để bắt đầu học.",
    "password_changed": "✅ Đổi mật khẩu thành công!",
    "profile_updated": "✅ Cập nhật hồ sơ thành công!",
    
    # Learning & Progress
    "word_learned": "🎓 Tuyệt vời! Bạn đã học xong từ này.",
    "quiz_completed": "✅ Hoàn thành bài quiz! Kết quả đã được lưu.",
    "test_submitted": "📝 Nộp bài thành công! Đang chấm điểm...",
    "level_up": "🎉 Chúc mừng! Bạn đã lên cấp độ mới!",
    "streak_milestone": "🔥 Wow! Bạn đã giữ streak {days} ngày liên tiếp!",
    "achievement_unlocked": "🏆 Mở khóa thành tựu mới: {achievement_name}!",
    
    # Shop & Premium
    "item_purchased": "🛒 Mua thành công! Item đã được thêm vào kho đồ.",
    "premium_activated": "👑 Chào mừng đến với Premium! Tận hưởng toàn bộ tính năng.",
    "item_equipped": "✨ Đã trang bị {item_name}!",
    
    # Data operations
    "data_saved": "💾 Dữ liệu đã được lưu thành công.",
    "data_deleted": "🗑️ Đã xóa thành công.",
    
    # Generic success
    "action_completed": "✅ Thao tác hoàn tất thành công!",
}


# ============================================================================
# INFO MESSAGES
# ============================================================================

INFO_MESSAGES = {
    "loading": "⏳ Đang tải dữ liệu...",
    "processing": "⚙️ Đang xử lý...",
    "generating_ai": "🤖 AI đang tạo nội dung cho bạn...",
    "checking": "🔍 Đang kiểm tra...",
    "saving": "💾 Đang lưu...",
    
    "welcome_new_user": "👋 Chào mừng bạn mới! Hãy bắt đầu với bài kiểm tra trình độ để chúng tôi tùy chỉnh lộ trình học cho bạn.",
    "first_lesson": "📚 Đây là bài học đầu tiên của bạn. Chúc bạn học tốt!",
    "streak_reminder": "🔥 Đừng quên học hôm nay để giữ streak nhé!",
    "premium_trial": "⭐ Bạn đang dùng thử Premium. Hãy trải nghiệm toàn bộ tính năng!",
}


# ============================================================================
# WARNING MESSAGES
# ============================================================================

WARNING_MESSAGES = {
    "unsaved_changes": "⚠️ Bạn có thay đổi chưa lưu. Rời đi sẽ mất dữ liệu!",
    "streak_risk": "⚠️ Streak của bạn sắp bị mất! Hãy học ít nhất 1 từ hôm nay.",
    "low_coins": "⚠️ Số Coin của bạn đang thấp. Hoàn thành nhiệm vụ để kiếm thêm!",
    "daily_goal_unmet": "⚠️ Bạn chưa hoàn thành mục tiêu hôm nay (0/{target} từ).",
    "premium_expiring": "⚠️ Premium của bạn sẽ hết hạn trong {days} ngày. Gia hạn ngay!",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def show_error(
    error_key: str, 
    details: Optional[str] = None,
    show_details_expander: bool = True
) -> None:
    """
    Display user-friendly error message with optional technical details.
    
    Args:
        error_key: Key from ERROR_MESSAGES dict
        details: Optional technical details (for developers/debugging)
        show_details_expander: Whether to show details in expander
        
    Example:
        try:
            load_data()
        except Exception as e:
            show_error("data_load_failed", str(e))
    """
    message = ERROR_MESSAGES.get(error_key, ERROR_MESSAGES["unknown_error"])
    st.error(message)
    
    if details and show_details_expander:
        with st.expander("🔍 Chi tiết lỗi (cho developer)"):
            st.code(details, language="text")


def show_success(success_key: str, **kwargs) -> None:
    """
    Display success message with optional formatting.
    
    Args:
        success_key: Key from SUCCESS_MESSAGES dict
        **kwargs: Format arguments (e.g., days=7, achievement_name="Master")
        
    Example:
        show_success("streak_milestone", days=7)
    """
    message = SUCCESS_MESSAGES.get(success_key, SUCCESS_MESSAGES["action_completed"])
    formatted_message = message.format(**kwargs) if kwargs else message
    st.success(formatted_message)


def show_info(info_key: str, **kwargs) -> None:
    """Display info message with optional formatting."""
    message = INFO_MESSAGES.get(info_key, "")
    formatted_message = message.format(**kwargs) if kwargs else message
    st.info(formatted_message)


def show_warning(warning_key: str, **kwargs) -> None:
    """Display warning message with optional formatting."""
    message = WARNING_MESSAGES.get(warning_key, "")
    formatted_message = message.format(**kwargs) if kwargs else message
    st.warning(formatted_message)


def validate_form_field(
    field_value: str,
    field_name: str,
    validation_rules: dict
) -> tuple[bool, str]:
    """
    Validate form field with rules.
    
    Args:
        field_value: Value to validate
        field_name: Name of field (for error message)
        validation_rules: Dict with rules (e.g., {'min_length': 3, 'required': True})
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
        
    Example:
        is_valid, error = validate_form_field(
            username,
            "Tên đăng nhập",
            {'required': True, 'min_length': 3, 'max_length': 20}
        )
        if not is_valid:
            st.error(error)
    """
    # Required check
    if validation_rules.get('required') and not field_value:
        return False, f"❌ {field_name} là bắt buộc."
    
    # Min length check
    min_len = validation_rules.get('min_length')
    if min_len and len(field_value) < min_len:
        return False, f"❌ {field_name} phải có ít nhất {min_len} ký tự."
    
    # Max length check
    max_len = validation_rules.get('max_length')
    if max_len and len(field_value) > max_len:
        return False, f"❌ {field_name} không được vượt quá {max_len} ký tự."
    
    # Email check
    if validation_rules.get('is_email'):
        if '@' not in field_value or '.' not in field_value.split('@')[1]:
            return False, f"❌ {field_name} không hợp lệ."
    
    # Custom pattern check
    pattern = validation_rules.get('pattern')
    if pattern:
        import re
        if not re.match(pattern, field_value):
            return False, f"❌ {field_name} không đúng định dạng."
    
    return True, ""


def calculate_password_strength(password: str) -> int:
    """
    Calculate password strength (0-5 scale).
    
    Args:
        password: Password string
        
    Returns:
        Strength score (0: very weak, 5: very strong)
        
    Example:
        strength = calculate_password_strength("MyP@ss123")
        if strength < 3:
            st.warning("Mật khẩu yếu")
    """
    score = 0
    
    # Length
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    
    # Complexity
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        score += 1
    
    return min(score, 5)


def get_password_strength_message(password: str) -> tuple[str, str]:
    """
    Get password strength message and color.
    
    Returns:
        Tuple of (message, color)
        
    Example:
        message, color = get_password_strength_message("weak123")
        st.markdown(f"<span style='color:{color}'>{message}</span>", unsafe_allow_html=True)
    """
    strength = calculate_password_strength(password)
    
    if strength <= 1:
        return "❌ Rất yếu", "#ff0000"
    elif strength == 2:
        return "⚠️ Yếu", "#ff6b00"
    elif strength == 3:
        return "🟡 Trung bình", "#ffc107"
    elif strength == 4:
        return "✅ Mạnh", "#4caf50"
    else:
        return "✅ Rất mạnh", "#00c853"

