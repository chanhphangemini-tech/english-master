"""
UI Components Library - Standardized UI elements for English Master App

This module provides reusable, consistent UI components to ensure
uniform design across all pages.

Author: AI Assistant
Date: 2025-12-30
"""

import streamlit as st
from typing import Callable, Optional, List, Dict, Any


# ============================================================================
# BUTTONS - Standardized button components
# ============================================================================

def render_primary_button(
    label: str, 
    key: str, 
    icon: str = "", 
    full_width: bool = True,
    disabled: bool = False
) -> bool:
    """
    Primary CTA button - for main actions (submit, start, generate).
    
    Args:
        label: Button text
        key: Unique button key
        icon: Optional emoji icon
        full_width: Whether button spans full width
        disabled: Whether button is disabled
        
    Returns:
        True if button was clicked
        
    Example:
        if render_primary_button("Bắt đầu học", "start_learn", "🚀"):
            start_learning()
    """
    display_label = f"{icon} {label}".strip() if icon else label
    width_param = 'stretch' if full_width else 'content'
    return st.button(
        display_label, 
        key=key, 
        type="primary", 
        width=width_param,
        disabled=disabled
    )


def render_secondary_button(
    label: str, 
    key: str, 
    icon: str = "", 
    full_width: bool = False,
    disabled: bool = False
) -> bool:
    """
    Secondary button - for alternative actions (upgrade, options).
    
    Args:
        label: Button text
        key: Unique button key
        icon: Optional emoji icon
        full_width: Whether button spans full width
        disabled: Whether button is disabled
        
    Returns:
        True if button was clicked
    """
    display_label = f"{icon} {label}".strip() if icon else label
    width_param = 'stretch' if full_width else 'content'
    return st.button(
        display_label, 
        key=key, 
        type="secondary", 
        width=width_param,
        disabled=disabled
    )


def render_tertiary_button(
    label: str, 
    key: str, 
    icon: str = "",
    disabled: bool = False
) -> bool:
    """
    Tertiary button - for low priority actions (cancel, back, links).
    
    Args:
        label: Button text
        key: Unique button key
        icon: Optional emoji icon
        disabled: Whether button is disabled
        
    Returns:
        True if button was clicked
    """
    display_label = f"{icon} {label}".strip() if icon else label
    return st.button(
        display_label, 
        key=key, 
        type="tertiary",
        disabled=disabled
    )


def render_premium_upsell_button(
    context: str = "feature",
    full_width: bool = True
) -> None:
    """
    Standardized Premium upsell button that navigates to Premium tab in shop.
    
    Args:
        context: Context identifier for tracking (e.g., "vocab", "grammar")
        full_width: Whether button spans full width
        
    Example:
        render_premium_upsell_button("grammar_lessons")
    """
    width_param = 'stretch' if full_width else 'content'
    if st.button(
        "⭐ Nâng cấp Premium để mở khóa", 
        key=f"premium_upsell_{context}", 
        type="secondary", 
        width=width_param
    ):
        st.switch_page("pages/15_Premium.py")


# ============================================================================
# LAYOUT - Standardized layout components
# ============================================================================

def render_section(
    title: str, 
    caption: str = "", 
    use_divider: bool = True,
    icon: str = ""
) -> None:
    """
    Standardized section header with optional divider.
    
    Args:
        title: Section title
        caption: Optional caption/description
        use_divider: Whether to show divider before section
        icon: Optional emoji icon before title
        
    Example:
        render_section("Thống kê học tập", "Xem tiến độ của bạn", icon="📊")
    """
    if use_divider:
        st.divider()
    
    display_title = f"{icon} {title}" if icon else title
    st.markdown(f"### {display_title}")
    
    if caption:
        st.caption(caption)


def render_card_container(content_callback: Callable) -> None:
    """
    Standardized card container with consistent styling.
    
    Args:
        content_callback: Function that renders card content
        
    Example:
        def my_card_content():
            st.write("Hello from card")
        
        render_card_container(my_card_content)
    """
    with st.container(border=True):
        content_callback()


def render_stats_card(
    label: str, 
    value: str, 
    icon: str = "",
    delta: Optional[str] = None
) -> None:
    """
    Standardized stats card (metric card).
    
    Args:
        label: Metric label
        value: Metric value
        icon: Optional emoji icon
        delta: Optional delta value (e.g., "+5")
        
    Example:
        render_stats_card("Từ vựng", "150 từ", icon="📚", delta="+10")
    """
    display_label = f"{icon} {label}" if icon else label
    st.metric(display_label, value, delta=delta)


# ============================================================================
# MESSAGES - Standardized message components
# ============================================================================

def show_success_message(message: str, icon: str = "✅") -> None:
    """Show success message with icon."""
    st.success(f"{icon} {message}")


def show_error_message(message: str, icon: str = "❌") -> None:
    """Show error message with icon."""
    st.error(f"{icon} {message}")


def show_warning_message(message: str, icon: str = "⚠️") -> None:
    """Show warning message with icon."""
    st.warning(f"{icon} {message}")


def show_info_message(message: str, icon: str = "ℹ️") -> None:
    """Show info message with icon."""
    st.info(f"{icon} {message}")


# ============================================================================
# PROGRESS - Progress indicators
# ============================================================================

def render_progress_bar(
    current: int, 
    total: int, 
    label: str = "",
    show_percentage: bool = True
) -> None:
    """
    Render a progress bar with optional label and percentage.
    
    Args:
        current: Current progress value
        total: Total/max value
        label: Optional label above progress bar
        show_percentage: Whether to show percentage text
        
    Example:
        render_progress_bar(7, 10, "Nhiệm vụ hoàn thành")
    """
    if label:
        st.caption(label)
    
    progress = current / total if total > 0 else 0
    st.progress(progress)
    
    if show_percentage:
        st.caption(f"{current}/{total} ({int(progress*100)}%)")


def render_quiz_progress(
    current_question: int, 
    total_questions: int
) -> None:
    """
    Render quiz progress indicator with question number.
    
    Args:
        current_question: Current question number (1-indexed)
        total_questions: Total number of questions
        
    Example:
        render_quiz_progress(3, 10)  # Shows "Câu 3/10 (30%)"
    """
    progress = (current_question / total_questions) * 100
    
    st.markdown(f"""
    <div style="background: #e3f2fd; padding: 12px; border-radius: 8px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #1565c0;">Câu {current_question}/{total_questions}</span>
            <div style="flex-grow: 1; margin: 0 20px; background: #fff; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #4CAF50, #8BC34A); height: 100%; width: {progress}%; border-radius: 4px; transition: width 0.3s;"></div>
            </div>
            <span style="font-weight: 600; color: #1565c0;">{int(progress)}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# LOADING STATES
# ============================================================================

def render_loading_with_progress(
    data_loader: Callable,
    message: str = "Đang tải...",
    estimated_batches: int = 5
) -> Any:
    """
    Render a loading state with progress bar for batch data loading.
    
    Args:
        data_loader: Generator function that yields batches of data
        message: Loading message
        estimated_batches: Estimated number of batches
        
    Returns:
        All loaded data
        
    Example:
        def load_vocab_batches():
            for batch in fetch_batches():
                yield batch
        
        data = render_loading_with_progress(load_vocab_batches, "Đang tải từ vựng...", 5)
    """
    with st.spinner(""):
        progress_bar = st.progress(0)
        progress_text = st.empty()
        
        all_data = []
        
        for i, batch in enumerate(data_loader()):
            all_data.extend(batch)
            progress = min((i + 1) / estimated_batches, 1.0)
            progress_bar.progress(progress)
            progress_text.text(f"{message} {len(all_data)} items...")
        
        progress_bar.empty()
        progress_text.empty()
        
    return all_data


# ============================================================================
# EMPTY STATES
# ============================================================================

def render_empty_state(
    message: str = "Chưa có dữ liệu", 
    icon: str = "📭",
    action_label: Optional[str] = None,
    action_callback: Optional[Callable] = None
) -> None:
    """
    Render an empty state with optional action button.
    
    Args:
        message: Empty state message
        icon: Emoji icon
        action_label: Optional action button label
        action_callback: Optional callback when action button is clicked
        
    Example:
        def start_learning():
            st.switch_page("pages/06_On_Tap.py")
        
        render_empty_state(
            "Bạn chưa học từ nào", 
            "📚", 
            "Bắt đầu học ngay",
            start_learning
        )
    """
    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px; color: #6c757d;">
        <div style="font-size: 64px; margin-bottom: 20px; opacity: 0.5;">{icon}</div>
        <p style="font-size: 1.2em; margin-bottom: 10px;">{message}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if render_primary_button(action_label, "empty_state_action", full_width=True):
                action_callback()


# ============================================================================
# CONFIRMATION DIALOGS
# ============================================================================

def render_confirmation_dialog(
    title: str,
    message: str,
    confirm_label: str = "Xác nhận",
    cancel_label: str = "Hủy",
    key_prefix: str = "confirm"
) -> Optional[bool]:
    """
    Render a confirmation dialog.
    
    Args:
        title: Dialog title
        message: Dialog message
        confirm_label: Confirm button label
        cancel_label: Cancel button label
        key_prefix: Unique key prefix
        
    Returns:
        True if confirmed, False if cancelled, None if not interacted
        
    Example:
        result = render_confirmation_dialog(
            "Xác nhận xóa",
            "Bạn có chắc muốn xóa từ này?",
            "Xóa",
            "Hủy",
            "delete_word"
        )
        if result == True:
            delete_word()
        elif result == False:
            st.info("Đã hủy")
    """
    st.warning(f"**{title}**")
    st.write(message)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"✅ {confirm_label}", key=f"{key_prefix}_confirm"):
            return True
    
    with col2:
        if st.button(f"❌ {cancel_label}", key=f"{key_prefix}_cancel"):
            return False
    
    return None


# ============================================================================
# PREMIUM UPSELL - Smart Strategy
# ============================================================================

def show_smart_premium_upsell(
    feature_name: str,
    feature_context: str,
    benefits: List[str],
    user_stats: Optional[Dict[str, Any]] = None
) -> None:
    """
    Show smart premium upsell with value-focused messaging.
    Only shows if user meets certain criteria to avoid annoyance.
    
    Args:
        feature_name: Name of the feature (e.g., "Luyện AI")
        feature_context: Context for tracking
        benefits: List of Premium benefits
        user_stats: Optional user statistics for smart display logic
        
    Example:
        show_smart_premium_upsell(
            "Luyện AI không giới hạn",
            "ai_practice",
            [
                "Không giới hạn số lượt luyện AI",
                "Phản hồi chi tiết từ AI",
                "Lưu lịch sử luyện tập"
            ],
            get_user_stats(user_id)
        )
    """
    # Smart display logic (can be enhanced)
    if user_stats:
        # Don't show if user just dismissed recently
        last_dismissed = st.session_state.get(f'premium_dismissed_{feature_context}', 0)
        import time
        if time.time() - last_dismissed < 86400:  # 24 hours
            return
    
    # Value-focused message
    st.info(f"""
    ✨ **Mở khóa {feature_name} với Premium**
    
    Bạn đang học tốt đấy! Nâng cấp Premium để tận dụng tối đa:
    
    {chr(10).join([f'- ✅ {benefit}' for benefit in benefits])}
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if render_secondary_button("Tìm hiểu Premium", f"upsell_{feature_context}", "⭐", full_width=True):
            st.session_state.shop_active_tab = "premium"
            st.switch_page("pages/11_Cua_Hang.py")
    
    with col2:
        if render_tertiary_button("Để sau", f"dismiss_{feature_context}"):
            import time
            st.session_state[f'premium_dismissed_{feature_context}'] = time.time()
            st.rerun()


# ============================================================================
# RESPONSIVE HELPERS
# ============================================================================

def is_mobile() -> bool:
    """
    Detect if user is on mobile device (basic detection).
    For production, use JavaScript-based detection.
    
    Returns:
        True if likely on mobile
    """
    # This is a placeholder - Streamlit doesn't have built-in mobile detection
    # In production, use JavaScript to set session state
    return st.session_state.get('is_mobile', False)


def render_responsive_columns(
    desktop_layout: List[int],
    mobile_stack: bool = True
) -> List:
    """
    Render columns that adapt to mobile.
    
    Args:
        desktop_layout: Column layout for desktop (e.g., [1, 2, 1])
        mobile_stack: Whether to stack vertically on mobile
        
    Returns:
        List of column objects
        
    Example:
        cols = render_responsive_columns([1, 1, 1])
        cols[0].metric("Metric 1", "100")
        cols[1].metric("Metric 2", "200")
        cols[2].metric("Metric 3", "300")
    """
    if is_mobile() and mobile_stack:
        # On mobile, return single column repeated
        return [st.container() for _ in desktop_layout]
    else:
        # On desktop, return columns as specified
        return st.columns(desktop_layout)

