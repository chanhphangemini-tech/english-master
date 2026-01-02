import streamlit as st
from datetime import datetime

AI_USAGE_LIMIT = 5 # Daily limit for free users per feature (increased to demonstrate value - freemium model)

def initialize_ai_usage_tracker():
    """Initializes or resets the daily AI usage tracker in session state."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    if st.session_state.get('ai_usage_date') != today_str:
        st.session_state.ai_usage_date = today_str
        st.session_state.ai_usage_counts = {
            "listening": 0,
            "speaking": 0,
            "reading": 0,
            "writing": 0,
        }

def can_use_ai_feature(feature_type: str) -> bool:
    """
    Checks if the user can use an AI feature based on their plan and usage limits.
    - Free users: 5 requests/day per feature (tracked in session state) + top-up credits
    - Premium users: Tier-based limits/month (tracked in database, includes top-up)
    - Admin: Unlimited (no tracking)
    """
    user_info = st.session_state.get("user_info", {})
    user_plan = user_info.get("plan", "free")
    user_role = user_info.get("role", "user")
    user_id = user_info.get("id")

    # Admin: Unlimited
    if user_role == 'admin':
        return True
    
    # Premium users: Check monthly limit from database (basic/premium/pro)
    from services.premium_usage_service import has_premium_subscription
    if has_premium_subscription(user_plan=user_plan) and user_id:
        try:
            from services.premium_usage_service import can_premium_use_ai
            allowed, message = can_premium_use_ai(user_id)
            if not allowed:
                # Store message for display
                st.session_state['premium_ai_limit_message'] = message
            return allowed
        except Exception as e:
            import logging
            logging.error(f"Error checking premium AI limit: {e}")
            # Fail open - allow usage if check fails
            return True

    # Free users: Check daily limit + top-up credits
    initialize_ai_usage_tracker()

    if feature_type not in st.session_state.ai_usage_counts:
        st.session_state.ai_usage_counts[feature_type] = 0

    current_usage = st.session_state.ai_usage_counts[feature_type]
    
    # Check if within daily limit
    if current_usage < AI_USAGE_LIMIT:
        return True
    
    # Daily limit exceeded - check if user has top-up credits
    if user_id:
        try:
            from services.premium_usage_service import get_topup_balance
            topup_balance = get_topup_balance(user_id)
            if topup_balance > 0:
                return True  # User can use top-up credits
        except Exception as e:
            import logging
            logging.error(f"Error checking free user top-up balance: {e}")
            # Fail closed - don't allow if check fails
            pass
    
    return False

def log_ai_usage(feature_type: str):
    """
    Logs AI usage for a given feature.
    - Free users: Tracked in session state (daily limit) + top-up credits (if available)
    - Premium users: Already tracked in generate_response_with_fallback() (DO NOT track here to avoid double tracking)
    - Admin: Not tracked (unlimited)
    
    NOTE: Premium users are tracked in core/llm.py:generate_response_with_fallback() after successful AI call.
    This function only tracks FREE users to avoid double tracking for premium users.
    
    For free users: If daily limit is exceeded, attempt to use top-up credits first.
    """
    user_info = st.session_state.get("user_info", {})
    user_plan = user_info.get("plan", "free")
    user_role = user_info.get("role", "user")
    user_id = user_info.get("id")

    # Admin: Don't track
    if user_role == 'admin':
        return
    
    # Premium users: Already tracked in generate_response_with_fallback() - DO NOT track here
    from services.premium_usage_service import has_premium_subscription
    if has_premium_subscription(user_plan=user_plan):
        return

    # Free users: Track in session state
    initialize_ai_usage_tracker()
    
    if feature_type not in st.session_state.ai_usage_counts:
        st.session_state.ai_usage_counts[feature_type] = 0
    
    current_usage = st.session_state.ai_usage_counts[feature_type]
    
    # If within daily limit, just increment
    if current_usage < AI_USAGE_LIMIT:
        st.session_state.ai_usage_counts[feature_type] += 1
        return
    
    # Daily limit exceeded - try to use top-up credit
    if user_id:
        try:
            from services.premium_usage_service import get_topup_balance, use_topup_credit
            topup_balance = get_topup_balance(user_id)
            if topup_balance > 0:
                # Use top-up credit instead of incrementing daily count
                if use_topup_credit(user_id, 1):
                    # Successfully used top-up - don't increment daily count
                    return
        except Exception as e:
            import logging
            logging.error(f"Error using top-up credit for free user: {e}")
            # Fall through to increment daily count (will exceed limit, but that's handled in can_use_ai_feature)
    
    # No top-up available or error - increment daily count (will exceed limit)
    st.session_state.ai_usage_counts[feature_type] += 1

def show_premium_upsell(feature_name: str, feature_type: str):
    """Displays a standardized message for locked features."""
    user_info = st.session_state.get("user_info", {})
    user_plan = user_info.get("plan", "free")
    
    # Premium users: Show monthly limit message if exceeded
    from services.premium_usage_service import has_premium_subscription
    if has_premium_subscription(user_plan=user_plan) and 'premium_ai_limit_message' in st.session_state:
        st.error(f"🔒 {st.session_state['premium_ai_limit_message']}")
        st.info("💡 Limit sẽ reset vào đầu tháng tới. Hoặc liên hệ admin để được hỗ trợ.")
        del st.session_state['premium_ai_limit_message']  # Clear after showing
        return
    
    # Free users: Show daily limit message
    initialize_ai_usage_tracker()
    limit = AI_USAGE_LIMIT
    count = st.session_state.ai_usage_counts.get(feature_type, 0)
    
    st.warning(f"🔒 Bạn đã hết {count}/{limit} lượt sử dụng tính năng '{feature_name}' hôm nay.")
    
    # Check if user has top-up credits
    user_id = st.session_state.get("user_info", {}).get("id")
    topup_balance = 0
    if user_id:
        try:
            from services.premium_usage_service import get_topup_balance
            topup_balance = get_topup_balance(user_id)
        except:
            pass
    
    if topup_balance > 0:
        st.info(f"💡 Bạn có {topup_balance} lượt Top-up còn lại. Các lượt tiếp theo sẽ tự động dùng Top-up.")
    else:
        st.info("💡 Bạn có thể mua thêm lượt AI (Top-up) hoặc nâng cấp lên Premium để nhận 600 lượt/tháng và mở khóa toàn bộ tiềm năng học tập!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ Mua Top-up", width='stretch'):
                st.switch_page("pages/15_Premium.py")
        with col2:
            if st.button("✨ Tìm hiểu gói Premium", width='stretch'):
                st.switch_page("pages/15_Premium.py")