import streamlit as st
# from core.theme import apply_custom_theme  # Disabled to use Streamlit default
from services.user_service import get_user_stats
from services.feature_flag_service import is_feature_enabled, get_feature_maintenance_message
from services.title_service import get_title_display_name
from services.frame_service import get_frame_style, get_frame_border_style

def render_sidebar():
    """Sidebar điều hướng cho English App."""
    # apply_custom_theme()  # Disabled to use Streamlit default

    if st.session_state.get('logged_in', False):
        user_info = st.session_state.get('user_info', {})
        user_name = user_info.get('name', 'Learner')
        user_id = user_info.get('id')
        role = str(user_info.get('role', 'user')).lower()
        level = user_info.get('current_level', 'A1')
        avatar_url = user_info.get('avatar_url') or "https://cdn-icons-png.flaticon.com/512/197/197374.png"
        
        # Lấy thông tin tùy chỉnh từ user_info
        active_frame = user_info.get('active_avatar_frame')
        active_title = user_info.get('active_title')
        
        # Get frame style from frame_service
        frame_container_style, frame_extra_css, frame_class = get_frame_style(active_frame)
        frame_border_style = get_frame_border_style(active_frame)
        
        # Fetch stats with caching (sử dụng cached data để tránh reload mỗi lần chuyển page)
        # Only fetch if not already cached in session_state to avoid unnecessary calls
        from core.data_cache import get_cached_user_stats
        
        # Cache stats in session_state for this render cycle
        stats_cache_key = f'sidebar_stats_{user_id}'
        if stats_cache_key not in st.session_state:
            stats = get_cached_user_stats(user_id)
            st.session_state[stats_cache_key] = stats
        else:
            stats = st.session_state[stats_cache_key]
        
        coins = stats.get('coins', 0)
        streak = stats.get('streak', 0)

        with st.sidebar:
            # Add frame extra CSS if any (replace & with proper selector)
            frame_css = ""
            if frame_extra_css:
                if frame_class:
                    # Replace & with .sidebar-avatar-container.frame-XXX
                    frame_css = frame_extra_css.replace('&', f'.sidebar-avatar-container.{frame_class}')
                else:
                    frame_css = frame_extra_css
            
            # Custom CSS for beautiful sidebar (use string concatenation to avoid f-string issues with % in CSS)
            css_content = """<style>
                """ + frame_css + """
                /* Sidebar background - professional light gray */
                section[data-testid="stSidebar"] {
                    background-color: #ffffff !important;
                    border-right: 1px solid #e2e8f0 !important;
                    padding: 0 !important;
                    min-width: 256px !important;
                    max-width: 256px !important;
                    width: 256px !important;
                }
                section[data-testid="stSidebar"] > div {
                    background-color: #ffffff !important;
                    padding: 0 !important;
                    width: 100% !important;
                }
                /* Disable sidebar resize - Hide resize handle and disable resize functionality */
                [data-testid="stSidebar"] [data-testid="stSidebarResizeHandle"],
                [data-testid="stSidebar"] [data-testid*="resize"],
                [data-testid="stSidebar"] .resize-handle,
                [data-testid="stSidebar"] .sidebar-resize-handle,
                [data-testid="stSidebar"] > div > div[style*="cursor"],
                [data-testid="stSidebar"] [role="separator"],
                section[data-testid="stSidebar"]::after,
                section[data-testid="stSidebar"]::before {
                    display: none !important;
                    visibility: hidden !important;
                    pointer-events: none !important;
                    width: 0 !important;
                    height: 0 !important;
                    opacity: 0 !important;
                }
                /* Disable resize cursor on sidebar border and all child elements */
                section[data-testid="stSidebar"],
                section[data-testid="stSidebar"] * {
                    resize: none !important;
                    cursor: default !important;
                }
                /* Disable any drag/resize functionality */
                [data-testid="stSidebar"] {
                    touch-action: none !important;
                    -webkit-user-select: none !important;
                    -moz-user-select: none !important;
                    -ms-user-select: none !important;
                    user-select: none !important;
                }
                /* Prevent any element with resize cursor from being visible */
                [data-testid="stSidebar"] [style*="cursor: ew-resize"],
                [data-testid="stSidebar"] [style*="cursor: col-resize"],
                [data-testid="stSidebar"] [style*="cursor: w-resize"],
                [data-testid="stSidebar"] [style*="cursor: e-resize"] {
                    display: none !important;
                    pointer-events: none !important;
                }
                /* Target specific Streamlit resize elements by class */
                [data-testid="stSidebar"] .st-emotion-cache-m0hag0,
                [data-testid="stSidebar"] .e6f82ta3,
                [data-testid="stSidebar"] [class*="e6f82ta3"] {
                    cursor: default !important;
                    pointer-events: none !important;
                    user-select: none !important;
                }
                /* Disable mouse events on sidebar border area */
                section[data-testid="stSidebar"] {
                    border-right: 1px solid #e2e8f0 !important;
                }
                /* Override any inline styles that enable resize */
                [data-testid="stSidebar"] > div > div[style*="cursor: col-resize"],
                [data-testid="stSidebar"] > div > div[style*="cursor: ew-resize"] {
                    cursor: default !important;
                    pointer-events: none !important;
                }
                /* Ensure sidebar content container uses full width */
                section[data-testid="stSidebar"] > div > div {
                    width: 100% !important;
                    padding: 0 8px !important;
                    box-sizing: border-box !important;
                }
                
                /* Profile section styling */
                .sidebar-profile {
                    text-align: center;
                    padding: 15px 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }
                .sidebar-avatar-container {
                    width: 140px;
                    height: 140px;
                    margin: 0 auto 15px auto;
                    border-radius: 50%;
                    padding: 4px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .sidebar-avatar-container img {
                    width: 100% !important;
                    height: 100% !important;
                    object-fit: cover;
                    border-radius: 50%;
                }
                .sidebar-name {
                    font-size: 1.3rem;
                    font-weight: bold;
                    color: #262730;
                    margin: 0 0 6px 0;
                    text-align: center;
                }
                .sidebar-level {
                    color: #808495;
                    font-size: 0.95rem;
                    margin: 0 0 8px 0;
                    text-align: center;
                }
                .sidebar-title {
                    color: #d63031;
                    font-weight: 700;
                    font-size: 0.95rem;
                    margin: 8px 0 4px 0;
                    text-align: center;
                    padding: 8px 16px;
                    background: linear-gradient(135deg, #ff7675 0%, #fd79a8 50%, #fdcb6e 100%);
                    border-radius: 25px;
                    display: block;
                    width: 100%;
                    box-shadow: 0 4px 8px rgba(255, 118, 117, 0.3);
                    border: 2px solid #d63031;
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    animation: title-glow 2s ease-in-out infinite;
                    box-sizing: border-box;
                }
                @keyframes title-glow {
                    0%, 100% {
                        box-shadow: 0 4px 8px rgba(255, 118, 117, 0.3);
                    }
                    50% {
                        box-shadow: 0 4px 12px rgba(255, 118, 117, 0.5), 0 0 20px rgba(255, 118, 117, 0.3);
                    }
                }
                .sidebar-powerup-active {
                    color: #ffffff;
                    font-weight: 600;
                    font-size: 0.85rem;
                    margin: 8px 0 4px 0;
                    text-align: center;
                    padding: 6px 12px;
                    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                    border-radius: 20px;
                    display: block;
                    width: 100%;
                    box-shadow: 0 2px 4px rgba(116, 185, 255, 0.3);
                    border: 1px solid #0984e3;
                    box-sizing: border-box;
                }
                .sidebar-powerup-active small {
                    font-size: 0.75rem;
                    opacity: 0.95;
                }
                .sidebar-premium-badge {
                    color: #d4af37;
                    font-weight: 700;
                    font-size: 0.95rem;
                    margin: 8px 0 4px 0;
                    text-align: center;
                    padding: 8px 16px;
                    background: linear-gradient(135deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%);
                    border-radius: 25px;
                    display: block;
                    width: 100%;
                    box-shadow: 0 4px 8px rgba(212, 175, 55, 0.4);
                    border: 2px solid #d4af37;
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    animation: premium-glow 2s ease-in-out infinite;
                    box-sizing: border-box;
                }
                .sidebar-basic-badge {
                    color: #3b82f6;
                    font-weight: 700;
                    font-size: 0.95rem;
                    margin: 8px 0 4px 0;
                    text-align: center;
                    padding: 8px 16px;
                    background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 50%, #60a5fa 100%);
                    border-radius: 25px;
                    display: block;
                    width: 100%;
                    box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
                    border: 2px solid #3b82f6;
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    animation: basic-glow 2s ease-in-out infinite;
                    box-sizing: border-box;
                }
                .sidebar-pro-badge {
                    color: #a855f7;
                    font-weight: 700;
                    font-size: 0.95rem;
                    margin: 8px 0 4px 0;
                    text-align: center;
                    padding: 8px 16px;
                    background: linear-gradient(135deg, #c084fc 0%, #e9d5ff 50%, #c084fc 100%);
                    border-radius: 25px;
                    display: block;
                    width: 100%;
                    box-shadow: 0 4px 8px rgba(168, 85, 247, 0.4);
                    border: 2px solid #a855f7;
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    animation: pro-glow 2s ease-in-out infinite;
                    box-sizing: border-box;
                }
                .sidebar-free-badge {
                    color: #6b7280;
                    font-weight: 700;
                    font-size: 0.95rem;
                    margin: 8px 0 4px 0;
                    text-align: center;
                    padding: 8px 16px;
                    background: linear-gradient(135deg, #e5e7eb 0%, #f3f4f6 50%, #e5e7eb 100%);
                    border-radius: 25px;
                    display: block;
                    width: 100%;
                    box-shadow: 0 2px 4px rgba(107, 114, 128, 0.2);
                    border: 2px solid #9ca3af;
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
                    box-sizing: border-box;
                }
                @keyframes basic-glow {
                    0%, 100% {
                        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
                    }
                    50% {
                        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.6), 0 0 20px rgba(96, 165, 250, 0.3);
                    }
                }
                @keyframes pro-glow {
                    0%, 100% {
                        box-shadow: 0 4px 8px rgba(168, 85, 247, 0.4);
                    }
                    50% {
                        box-shadow: 0 4px 12px rgba(168, 85, 247, 0.6), 0 0 20px rgba(192, 132, 252, 0.3);
                    }
                }
                @keyframes premium-glow {
                    0%, 100% {
                        box-shadow: 0 4px 8px rgba(212, 175, 55, 0.4);
                    }
                    50% {
                        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.6), 0 0 20px rgba(255, 215, 0, 0.3);
                    }
                }
                /* Stats section */
                .stats-container {
                    padding: 8px 0;
                    margin: 5px 0;
                }
                .stat-item {
                    text-align: center;
                    color: #000000;
                }
                .stat-icon {
                    font-size: 1.8rem;
                    margin-bottom: 5px;
                }
                .stat-value {
                    font-size: 1.2rem;
                    font-weight: bold;
                    color: #000000;
                    margin: 0;
                }
                .stat-label {
                    font-size: 0.85rem;
                    font-weight: bold;
                    color: #000000;
                    margin: 0;
                }
                /* Navigation buttons with hover effect */
                .sidebar-button {
                    margin: 4px 0;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                }
                .sidebar-button:hover {
                    transform: translateY(-2px);
                }
                
                /* Ensure all sidebar buttons have consistent width - Target all button containers */
                [data-testid="stSidebar"] > div > div > div {
                    width: 100% !important;
                    max-width: 100% !important;
                    padding: 0 8px !important;
                    box-sizing: border-box !important;
                }
                [data-testid="stSidebar"] > div > div > div > div {
                    width: 100% !important;
                    max-width: 100% !important;
                    padding: 0 !important;
                    box-sizing: border-box !important;
                }
                /* Target button wrapper containers more specifically */
                [data-testid="stSidebar"] [class*="stButton"],
                [data-testid="stSidebar"] [class*="e6f82ta8"],
                [data-testid="stSidebar"] > div > div > div > div > div {
                    width: 100% !important;
                    max-width: 100% !important;
                    min-width: 100% !important;
                    display: block !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    box-sizing: border-box !important;
                }
                /* Target all buttons in sidebar - ensure full width */
                [data-testid="stSidebar"] button {
                    width: 100% !important;
                    max-width: 100% !important;
                    min-width: 100% !important;
                    display: block !important;
                    box-sizing: border-box !important;
                    margin: 4px 0 !important;
                    padding-left: 12px !important;
                    padding-right: 12px !important;
                    transition: all 0.3s ease !important;
                }
                [data-testid="stSidebar"] button:hover {
                    transform: translateY(-2px) !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                }
                /* Ensure button parent containers are full width */
                [data-testid="stSidebar"] button[class*="e1q4kxr415"],
                [data-testid="stSidebar"] button[class*="st-emotion"] {
                    width: calc(100% - 16px) !important;
                    max-width: calc(100% - 16px) !important;
                    min-width: calc(100% - 16px) !important;
                }
                /* Section headers */
                .sidebar-section {
                    font-weight: 600;
                    font-size: 0.95rem;
                    color: #262730;
                    margin: 15px 0 8px 0;
                    padding: 8px 0;
                    border-bottom: 2px solid #f0f2f6;
                }
            </style>
            """
            st.markdown(css_content, unsafe_allow_html=True)
            
            # Profile Section
            # Check user plan and tier
            user_plan = user_info.get('plan', 'free')
            user_tier = user_info.get('premium_tier')
            user_plan_lower = str(user_plan).lower()
            is_premium = user_plan_lower in ('basic', 'premium', 'pro')
            
            st.markdown('<div class="sidebar-profile">', unsafe_allow_html=True)
            # Apply frame style from frame_service
            frame_class_attr = f'class="{frame_class}"' if frame_class else ''
            st.markdown(f'''
                <div class="sidebar-avatar-container {frame_class}" style="{frame_container_style}">
                    <img src="{avatar_url}" alt="Avatar" style="{frame_border_style}">
                </div>
                <p class="sidebar-name">{user_name}</p>
                <p class="sidebar-level">Level {level}</p>
            ''', unsafe_allow_html=True)
            
            # Plan/Tier badge
            if user_plan_lower == 'pro':
                st.markdown('''
                <p class="sidebar-pro-badge">
                    💎 <strong>Pro Member</strong>
                </p>
                ''', unsafe_allow_html=True)
            elif user_plan_lower == 'premium':
                st.markdown('''
                <p class="sidebar-premium-badge">
                    👑 <strong>Premium Member</strong>
                </p>
                ''', unsafe_allow_html=True)
            elif user_plan_lower == 'basic':
                st.markdown('''
                <p class="sidebar-basic-badge">
                    ⭐ <strong>Basic Member</strong>
                </p>
                ''', unsafe_allow_html=True)
            else:
                st.markdown('''
                <p class="sidebar-free-badge">
                    🆓 <strong>Free Member</strong>
                </p>
                ''', unsafe_allow_html=True)
            
            if active_title:
                title_display = get_title_display_name(active_title)
                if title_display:
                    st.markdown(f'<p class="sidebar-title">{title_display}</p>', unsafe_allow_html=True)
            
            # Display active consumable items
            active_powerup_type = user_info.get('active_powerup_type')
            active_powerup_expires_at = user_info.get('active_powerup_expires_at')
            if active_powerup_type and active_powerup_expires_at:
                try:
                    from core.timezone_utils import get_vn_now_utc
                    from datetime import datetime, timezone
                    expires_at = datetime.fromisoformat(active_powerup_expires_at.replace('Z', '+00:00'))
                    now = datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00'))
                    
                    if expires_at > now:
                        remaining = expires_at - now
                        hours_left = int(remaining.total_seconds() / 3600)
                        minutes_left = int((remaining.total_seconds() % 3600) / 60)
                        
                        # Powerup icon mapping
                        powerup_icons = {
                            'streak_freeze': '❄️',
                            'powerup': '⚡'
                        }
                        icon = powerup_icons.get(active_powerup_type, '⚡')
                        
                        time_str = f"{hours_left}h {minutes_left}m" if hours_left > 0 else f"{minutes_left}m"
                        st.markdown(f'''
                        <p class="sidebar-powerup-active">
                            {icon} <strong>Đang sử dụng</strong><br>
                            <small>Còn lại: {time_str}</small>
                        </p>
                        ''', unsafe_allow_html=True)
                except Exception as e:
                    # Silently fail if error parsing
                    pass
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.divider()
            
            # Stats Section with gradient background
            st.markdown('<div class="stats-container">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("""
                <div class="stat-item">
                    <div class="stat-icon">💰</div>
                    <div class="stat-value">{coins:,}</div>
                    <div class="stat-label">Coins</div>
                </div>
                """.format(coins=coins), unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="stat-item">
                    <div class="stat-icon">🔥</div>
                    <div class="stat-value">{streak}</div>
                    <div class="stat-label">Streak</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                daily_progress = st.session_state.get('daily_progress', '0/10')
                st.markdown(f"""
                <div class="stat-item">
                    <div class="stat-icon">🎯</div>
                    <div class="stat-value">{daily_progress}</div>
                    <div class="stat-label">Today</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.divider()

            # --- NAVIGATION MENUS ---
            
            # Helper function to render navigation button with feature flag check
            def render_nav_button(label, page, key, feature_key=None):
                """Render navigation button with feature flag check"""
                if feature_key and not is_feature_enabled(feature_key):
                    # Feature disabled - show disabled button with lock icon
                    maintenance_msg = get_feature_maintenance_message(feature_key)
                    disabled_label = f"🔒 {label}"
                    st.markdown(f"""
                    <div style="opacity: 0.5; margin-bottom: 0.5rem;">
                        <button disabled style="width: 100%; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #ccc; background-color: #f0f0f0; color: #666; cursor: not-allowed; text-align: left;">
                            {disabled_label}
                        </button>
                        <div style="font-size: 0.75rem; color: #999; margin-top: 0.25rem; padding-left: 0.5rem;">
                            {maintenance_msg}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Feature enabled - show normal button
                    if st.button(label, key=key):
                        st.switch_page(page)
            
            # 1. TRANG CHỦ
            if st.button("🏠 Trang Chủ", type="primary", key="nav_home"):
                st.switch_page("home.py")
            
            render_nav_button("📝 Kiểm Tra", "pages/00_Kiem_Tra_Dau_Vao.py", "nav_test", "kiem_tra_dau_vao")

            # 2. HỌC TẬP
            st.markdown('<p class="sidebar-section">📚 Học tập</p>', unsafe_allow_html=True)
            render_nav_button("🎯 Học Từ Vựng (SRS)", "pages/06_On_Tap.py", "nav_review", "on_tap_srs")
            render_nav_button("📖 Từ Điển", "pages/05_Kho_Tu_Vung.py", "nav_dict", "kho_tu_vung")
            render_nav_button("⚡ Động Từ BQT", "pages/13_Dong_Tu_Bat_Quy_Tac.py", "nav_irregular", "dong_tu_bat_quy_tac")
            render_nav_button("📐 Ngữ Pháp", "pages/07_Ngu_Phap.py", "nav_grammar", "ngu_phap")
            
            # 3. LUYỆN KỸ NĂNG
            st.markdown('<p class="sidebar-section">💪 Luyện tập</p>', unsafe_allow_html=True)
            render_nav_button("👂 Nghe", "pages/01_Luyen_Nghe.py", "nav_listen", "luyen_nghe")
            render_nav_button("💬 Nói", "pages/02_Luyen_Noi.py", "nav_speak", "luyen_noi")
            render_nav_button("📄 Đọc", "pages/03_Luyen_Doc.py", "nav_read", "luyen_doc")
            render_nav_button("✏️ Viết", "pages/04_Luyen_Viet.py", "nav_write", "luyen_viet")
            render_nav_button("🔄 Dịch", "pages/04_Luyen_Dich.py", "nav_translate", "luyen_dich")
            
            # 4. THỬ THÁCH
            st.markdown('<p class="sidebar-section">⚔️ Thử thách</p>', unsafe_allow_html=True)
            render_nav_button("📋 Thi thử", "pages/08_Thi_Thu.py", "nav_mock", "thi_thu")
            render_nav_button("🎮 PvP", "pages/09_Dau_Truong.py", "nav_pvp", "dau_truong")
            
            # 4.5. HỖ TRỢ (NEW - Easy to find for new users)
            st.markdown('<p class="sidebar-section">❓ Hỗ Trợ</p>', unsafe_allow_html=True)
            render_nav_button("📚 Hướng Dẫn", "pages/17_Huong_Dan.py", "nav_help", None)
            
            # 5. CÁ NHÂN
            st.markdown('<p class="sidebar-section">👤 Cá nhân</p>', unsafe_allow_html=True)
            render_nav_button("⭐ Nâng Cấp", "pages/15_Premium.py", "nav_premium", None)
            # Analytics - Premium/Basic/Pro only
            if is_premium or role == 'admin':
                render_nav_button("📊 Analytics", "pages/16_Analytics.py", "nav_analytics", None)
            render_nav_button("🏪 Cửa Hàng", "pages/11_Cua_Hang.py", "nav_shop", "cua_hang")
            render_nav_button("👤 Hồ Sơ", "pages/10_Ho_So.py", "nav_profile", "ho_so")
            render_nav_button("🔧 Cài Đặt", "pages/12_Cai_Dat.py", "nav_settings", "cai_dat")
            render_nav_button("📩 Góp ý", "pages/14_Gop_Y.py", "nav_feedback", "gop_y")

            # 6. ADMIN
            if role == 'admin':
                st.markdown('<p class="sidebar-section">🛡️ Quản trị</p>', unsafe_allow_html=True)
                if st.button("🔐 Admin", key="nav_admin"):
                    st.switch_page("pages/99_Quan_Tri.py")

            # LOGOUT
            st.divider()
            if st.button("🚪 Đăng xuất", key="btn_logout"):
                # Clear all caches khi logout
                from core.data_cache import clear_all_caches
                clear_all_caches()
                st.session_state.logged_in = False
                st.session_state.user_info = {}
                st.rerun()