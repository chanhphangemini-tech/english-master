import streamlit as st
import time
import pandas as pd
from datetime import datetime
from core.theme_applier import apply_page_theme

apply_page_theme()  # Apply theme + sidebar + auth
from core.data import get_all_users, supabase, get_system_analytics, get_all_pvp_challenges
from core.auth import create_new_user, toggle_user_status, delete_user, admin_update_user_info
from services.admin_service import admin_update_user_comprehensive, admin_get_user_full_info, admin_reset_user_ai_usage
from core.theme import render_empty_state
from services.health_service import check_db_connection, check_ai_service, check_storage_service, check_tts_service, run_system_benchmark
from services.health_check_service import run_feature_health_check, get_health_check_summary
from core.security_monitor import SecurityMonitor
from services.bot_tester_service import run_bot_tests
from services.settings_service import get_all_system_settings, update_system_setting, get_email_config, update_email_config, toggle_email_enabled
from pages.admin_feedback_helpers import (
    get_all_feedback, get_all_users_list, get_user_subscription, 
    update_user_premium, get_all_feature_flags, update_feature_flag
)
from pages.admin_shop_helpers import (
    get_all_shop_items, create_shop_item, update_shop_item, delete_shop_item
)

# --- Auth Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("🔒 Vui lòng đăng nhập để truy cập.")
    st.switch_page("home.py") 
    st.stop()
elif str(st.session_state.user_info.get('role')).lower() != 'admin':
    st.error("⛔ Bạn không có quyền truy cập khu vực này!")
    st.stop()

# Sidebar already rendered by apply_page_theme()

def show():
    """Renders the Admin Dashboard."""
    st.title("🛡️ Quản Lý Hệ Thống (Admin)")
    
    curr_user = st.session_state.user_info.get('username')

    tab_dash, tab_pvp, tab_users, tab_premium, tab_features, tab_shop, tab_feedback_stats, tab_email, tab_security, tab_health, tab_bot = st.tabs([
        "📊 Tổng Quan", 
        "⚔️ PvP & Coin", 
        "👥 Quản Lý User", 
        "💳 Quản lý Subscription",
        "⚙️ Quản lý Tính năng",
        "🛍️ Quản lý Cửa hàng",
        "📊 Thống kê Feedback",
        "📧 Email Settings",
        "🔒 Security Monitor",
        "🩺 Health & Benchmark",
        "🤖 Bot Tester"
    ])

    with tab_dash:
        render_dashboard()

    with tab_pvp:
        render_pvp_dashboard()

    with tab_users:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("➕ Tạo User Mới")
            render_create_user_form()
        with c2:
            st.subheader("📋 Danh Sách User")
            render_user_list(curr_user)
    
    with tab_premium:
        render_premium_management()
    
    with tab_features:
        render_feature_flags_management()
    
    with tab_shop:
        render_shop_management()
    
    with tab_feedback_stats:
        render_feedback_stats()
    
    with tab_email:
        render_email_settings()

    with tab_security:
        render_security_monitor()

    with tab_health:
        render_health_check()
    
    with tab_bot:
        render_bot_tester()

def render_dashboard():
    st.subheader("📈 Thống kê học tập")
    stats = get_system_analytics()
    
    # Row 1: Learning Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng người dùng", stats.get('total_users', 0))
    c2.metric("Kho từ vựng", stats.get('total_vocab', 0))
    c3.metric("Lượt học (Items)", stats.get('total_reviews', 0))
    c4.metric("Active hôm nay", stats.get('active_users_today', 0))
    
    st.divider()
    
    # Row 2: Economy Stats
    st.subheader("💰 Kinh tế & Đấu trường")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Tổng Coin lưu thông", f"{int(stats.get('total_coins', 0) or 0):,} 🪙")
    c6.metric("Tổng trận PvP", int(stats.get('total_pvp', 0) or 0))
    c7.metric("PvP Hoàn thành", int(stats.get('completed_pvp', 0) or 0))
    c8.metric("Tổng cược PvP", f"{int(stats.get('total_bet', 0) or 0):,} 🪙")

def render_pvp_dashboard():
    st.subheader("⚔️ Lịch sử đấu trường (50 trận gần nhất)")
    
    challenges = get_all_pvp_challenges()
    
    if not challenges:
        render_empty_state("Chưa có trận đấu nào diễn ra.", "🛡️")
        return

    # Convert to DataFrame for easier display
    data = []
    for ch in challenges:
        creator = ch.get('creator', {}).get('name', 'Unknown') if ch.get('creator') else 'Unknown'
        challenger = ch.get('challenger', {}).get('name', 'Waiting...') if ch.get('challenger') else 'Waiting...'
        
        winner_id = ch.get('winner_id')
        winner = "Chưa có"
        if winner_id:
            if winner_id == ch.get('creator_id'): winner = creator
            elif winner_id == ch.get('challenger_id'): winner = challenger
            else: winner = "Hòa"
            
        data.append({
            "Thời gian": ch['created_at'][:16].replace('T', ' '),
            "Người tạo": creator,
            "Đối thủ": challenger,
            "Cược": f"{ch['bet_amount']} 🪙",
            "Trạng thái": ch['status'],
            "Người thắng": winner,
            "Level": ch['level']
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch')

    # Simple Chart: Battles by Level
    if not df.empty:
        st.caption("Phân bố trận đấu theo cấp độ")
        st.bar_chart(df['Level'].value_counts())

    st.divider()

def render_create_user_form():
    """Renders the form for creating a new user."""
    st.write("Điền thông tin để cấp tài khoản mới cho học viên.")
    with st.form("create_user_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_u = st.text_input("Tên đăng nhập (Username)*", placeholder="VD: hocvien01")
            new_n = st.text_input("Họ và tên*", placeholder="VD: Nguyễn Văn A")
            new_e = st.text_input("Email (Quan trọng)*", placeholder="Để lấy lại mật khẩu...")
        with c2:
            new_p = st.text_input("Mật khẩu*", type="password")
            new_r = st.selectbox("Phân quyền (Role)*", ["user", "admin"], index=0)
        
        if st.form_submit_button("🚀 Tạo Tài Khoản", type="primary"):
            if not all([new_u, new_p, new_n, new_e]):
                st.warning("⚠️ Vui lòng điền đầy đủ thông tin.")
            elif "@" not in new_e:
                st.warning("⚠️ Email không hợp lệ.")
            else:
                with st.spinner("Đang khởi tạo..."):
                    ok, msg = create_new_user(new_u, new_p, new_n, new_r, new_e)
                    if ok:
                        st.success(f"✅ {msg}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

def render_user_list(current_admin_user):
    """Renders the list of all users with management actions."""
    if st.button("🔄 Refresh User List"):
        st.rerun()
    
    try:
        users = get_all_users()
        
        if not users:
            render_empty_state("Chưa có người dùng nào", "👥")
            return

        st.caption(f"Tổng số: **{len(users)}** tài khoản")
        for user in users:
            render_user_card(user, current_admin_user)

    except Exception as e:
        st.error(f"Lỗi tải danh sách người dùng: {e}")

def render_user_card(user, current_admin_user):
    """Renders a single card for a user with action buttons."""
    u_name = str(user['username'])
    is_myself = (u_name == current_admin_user)

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{user['name']}** (`{u_name}`)")
            st.caption(f"Email: {user.get('email', 'N/A')} | Role: {str(user.get('role', 'user')).upper()}")
        
        with col2:
            status = str(user.get('status', 'active')).lower()
            if status == 'active':
                st.success("● Active")
            else:
                st.error("● Disabled")

        if not is_myself:
            # Quick actions
            col_quick1, col_quick2 = st.columns(2)
            with col_quick1:
                if status == 'active':
                    if st.button("🔒 Khóa tài khoản", key=f"lock_{u_name}"):
                        toggle_user_status(u_name, "disabled")
                        st.rerun()
                else:
                    if st.button("🔓 Mở khóa tài khoản", key=f"unlock_{u_name}"):
                        toggle_user_status(u_name, "active")
                        st.rerun()
            
            with col_quick2:
                if st.button("📊 Xem chi tiết", key=f"view_details_{u_name}"):
                    st.session_state[f"view_user_details_{u_name}"] = not st.session_state.get(f"view_user_details_{u_name}", False)
                    st.rerun()

            # Comprehensive Edit Form
            with st.expander(f"⚙️ Chỉnh sửa toàn diện - {u_name}", expanded=False):
                with st.form(f"edit_comprehensive_{u_name}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📝 Thông tin cơ bản")
                        new_name = st.text_input("Họ và tên *", value=user.get('name', ''), key=f"comp_name_{u_name}")
                        new_email = st.text_input("Email *", value=user.get('email', ''), key=f"comp_email_{u_name}")
                        st.text_input("Username", value=u_name, disabled=True, key=f"comp_username_{u_name}")
                        st.caption("⚠️ Username không thể thay đổi")
                        
                        st.markdown("#### 🔐 Bảo mật")
                        new_password = st.text_input(
                            "Mật khẩu mới (bỏ trống nếu không đổi)", 
                            type="password", 
                            key=f"comp_pass_{u_name}",
                            help="Để trống nếu không muốn đổi mật khẩu"
                        )
                        
                        st.markdown("#### 👤 Phân quyền & Gói")
                        # Role selection
                        role_options = ['user', 'admin', 'moderator']
                        current_role_val = user.get('role', 'user')
                        if current_role_val not in role_options:
                            current_role_index = 0
                        else:
                            current_role_index = role_options.index(current_role_val)
                        new_role = st.selectbox(
                            "Phân quyền", 
                            options=role_options, 
                            index=current_role_index, 
                            key=f"comp_role_{u_name}",
                            help="user: Người dùng thường | admin: Quản trị viên | moderator: Điều hành viên"
                        )
                        
                        # Plan selection
                        plan_options = ['free', 'basic', 'premium', 'pro']
                        current_plan_val = user.get('plan', 'free')
                        if current_plan_val not in plan_options:
                            current_plan_index = 0
                        else:
                            current_plan_index = plan_options.index(current_plan_val)
                        new_plan = st.selectbox("Gói dịch vụ", options=plan_options, index=current_plan_index, key=f"comp_plan_{u_name}")
                        
                        # Premium Tier (chỉ hiện khi plan là premium tier)
                        new_tier = None
                        if new_plan in ['basic', 'premium', 'pro']:
                            tier_options = ['basic', 'premium', 'pro']
                            # Map plan to tier if plan is a tier name
                            if new_plan in tier_options:
                                new_tier = new_plan
                            else:
                                current_tier_val = user.get('premium_tier', 'premium')
                                if current_tier_val not in tier_options:
                                    current_tier_index = 1  # Default to 'premium'
                                else:
                                    current_tier_index = tier_options.index(current_tier_val)
                                new_tier = st.selectbox(
                                    "Premium Tier", 
                                    options=tier_options,
                                    index=current_tier_index,
                                    key=f"comp_tier_{u_name}",
                                    help="basic: 300 lượt/tháng | premium: 600 lượt/tháng | pro: 1200 lượt/tháng"
                                )
                        elif new_plan == 'premium':
                            # Legacy: if plan='premium', show tier selector
                            tier_options = ['basic', 'premium', 'pro']
                            current_tier_val = user.get('premium_tier', 'premium')
                            if current_tier_val not in tier_options:
                                current_tier_index = 1  # Default to 'premium'
                            else:
                                current_tier_index = tier_options.index(current_tier_val)
                            new_tier = st.selectbox(
                                "Premium Tier", 
                                options=tier_options,
                                index=current_tier_index,
                                key=f"comp_tier_{u_name}",
                                help="basic: 300 lượt/tháng | premium: 600 lượt/tháng | pro: 1200 lượt/tháng"
                            )
                    
                    with col2:
                        st.markdown("#### 💰 Kinh tế & Thống kê")
                        
                        # Coins
                        current_coins = user.get('coins', 0) or 0
                        st.markdown("**Coin**")
                        new_coins = st.number_input(
                            "Số coin", 
                            min_value=0, 
                            value=int(current_coins), 
                            step=100,
                            key=f"comp_coins_{u_name}",
                            help="Dùng step +/-100 để thay đổi giá trị"
                        )
                        
                        # Streak
                        current_streak = user.get('current_streak', 0) or 0
                        st.markdown("**Streak**")
                        new_streak = st.number_input(
                            "Số ngày streak", 
                            min_value=0, 
                            value=int(current_streak), 
                            step=1,
                            key=f"comp_streak_{u_name}",
                            help="Admin override - chỉ dùng khi cần thiết"
                        )
                        
                        # Status
                        current_status = user.get('status', 'active')
                        new_status = st.selectbox(
                            "Trạng thái tài khoản",
                            options=['active', 'disabled'],
                            index=0 if current_status == 'active' else 1,
                            key=f"comp_status_{u_name}"
                        )
                        
                        # AI Usage Info (Read-only display)
                        st.markdown("#### 🤖 AI Usage")
                        try:
                            from services.premium_usage_service import get_premium_ai_usage_monthly, get_topup_balance
                            user_id = user.get('id')
                            if new_plan in ['basic', 'premium', 'pro'] or user.get('plan') in ['basic', 'premium', 'pro']:
                                usage = get_premium_ai_usage_monthly(user_id)
                                st.info(f"""
                                **Usage:** {usage.get('count', 0)}/{usage.get('limit', 0)}
                                **Remaining:** {usage.get('remaining', 0)}
                                **Top-up:** {usage.get('topup_balance', 0)}
                                **Total Remaining:** {usage.get('total_remaining', 0)}
                                """)
                            else:
                                topup = get_topup_balance(user_id)
                                st.info(f"**Top-up Balance:** {topup}")
                        except Exception as e:
                            st.caption(f"Không thể load AI usage info: {str(e)}")
                    
                    # Action buttons
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        save_btn = st.form_submit_button("💾 Lưu tất cả thay đổi", type="primary", width='stretch')
                    with col_btn2:
                        reset_ai_btn = st.form_submit_button("🔄 Reset AI Usage", width='stretch')
                    with col_btn3:
                        view_details_btn = st.form_submit_button("📊 Xem chi tiết", width='stretch')
                    
                    if save_btn:
                        # Validate
                        if not new_name or not new_email:
                            st.error("⚠️ Vui lòng điền đầy đủ tên và email!")
                        elif '@' not in new_email:
                            st.error("⚠️ Email không hợp lệ!")
                        else:
                            # Call comprehensive update function
                            success, msg = admin_update_user_comprehensive(
                                user_id=user.get('id'),
                                name=new_name,
                                email=new_email,
                                role=new_role,
                                plan=new_plan,
                                premium_tier=new_tier if new_plan in ['basic', 'premium', 'pro'] else None,
                                password=new_password if new_password else None,
                                coins=new_coins,
                                streak=new_streak,
                                status=new_status
                            )
                            if success:
                                st.success(f"✅ {msg}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                    
                    if reset_ai_btn:
                        success, msg = admin_reset_user_ai_usage(user.get('id'))
                        if success:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")
                    
                    if view_details_btn:
                        st.session_state[f"view_user_details_{u_name}"] = True
                        st.rerun()
                
                # User Details View (if requested)
                if st.session_state.get(f"view_user_details_{u_name}", False):
                    st.divider()
                    st.markdown("#### 📊 Chi tiết User")
                    try:
                        full_info = admin_get_user_full_info(user.get('id'))
                        st.json(full_info)
                        if st.button("❌ Đóng", key=f"close_details_{u_name}"):
                            st.session_state[f"view_user_details_{u_name}"] = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi load chi tiết: {str(e)}")
                
                # --- Deletion ---
                st.divider()
                with st.expander("🗑️ Xóa tài khoản này?"):
                    st.warning("⚠️ Hành động này không thể hoàn tác!")
                    if st.button("Xác nhận Xóa", key=f"confirm_del_{u_name}", type="primary"):
                        delete_user(u_name)
                        st.rerun()
        else:
            st.info("Đây là tài khoản của bạn. Không thể thực hiện hành động.")

def render_security_monitor():
    """Renders the Security Monitor tab."""
    st.subheader("🔒 Security Monitor")
    st.caption("Theo dõi và quản lý các hành vi nghi ngờ từ users")
    
    # Get all users for selection
    users_list = get_all_users()
    if not users_list:
        st.warning("Không có users nào.")
        return
    
    # User selection
    col1, col2 = st.columns([2, 1])
    with col1:
        user_options = {f"{user.get('username', 'N/A')} (ID: {user.get('id', 'N/A')})": user.get('id') for user in users_list}
        selected_display = st.selectbox("Chọn user để xem thống kê Security:", options=list(user_options.keys()))
        selected_user_id = user_options[selected_display]
    
    with col2:
        st.write("")
        if st.button("🔍 Xem thống kê", type="primary"):
            st.session_state['security_user_id'] = selected_user_id
            st.rerun()
    
    # Display stats if user selected
    if 'security_user_id' in st.session_state and st.session_state['security_user_id']:
        user_id = st.session_state['security_user_id']
        
        with st.spinner("Đang lấy thống kê Security..."):
            stats = SecurityMonitor.get_user_security_stats(user_id)
            
            if stats:
                st.divider()
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Actions (24h)", stats.get('actions_24h', 0))
                col2.metric("Failed (24h)", stats.get('failed_24h', 0))
                col3.metric("Security Alerts (7d)", stats.get('security_alerts_7d', 0))
                col4.metric("Recent Flags", len(stats.get('recent_flags', [])))
                
                # Recent flags
                if stats.get('recent_flags'):
                    st.divider()
                    st.subheader("🚩 Recent Security Flags")
                    for flag in stats['recent_flags']:
                        metadata = flag.get('metadata', {})
                        reason = metadata.get('reason', 'Unknown')
                        details = metadata.get('details', 'No details')
                        flagged_at = metadata.get('flagged_at', 'Unknown')
                        
                        with st.expander(f"🚩 {reason} - {flagged_at}"):
                            st.write(f"**Chi tiết:** {details}")
                            st.json(metadata)
                
                # Security alerts from ActivityLog
                st.divider()
                st.subheader("📊 Security Activity Log")
                
                try:
                    from core.timezone_utils import get_vn_now_utc
                    from datetime import datetime, timedelta, timezone
                    now = datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00'))
                    window_7d = timedelta(days=7)
                    
                    alerts_res = supabase.table("ActivityLog")\
                        .select("*, Users(username, name)")\
                        .eq("user_id", user_id)\
                        .eq("action_type", "security_alert")\
                        .gte("created_at", (now - window_7d).isoformat())\
                        .order("created_at", desc=True)\
                        .limit(20)\
                        .execute()
                    
                    if alerts_res.data:
                        alerts_df = pd.DataFrame(alerts_res.data)
                        # Format for display
                        display_data = []
                        for _, row in alerts_df.iterrows():
                            metadata = row.get('metadata', {})
                            display_data.append({
                                "Thời gian": row.get('created_at', '')[:16].replace('T', ' ') if row.get('created_at') else 'N/A',
                                "Pattern": metadata.get('pattern_type', 'N/A'),
                                "Message": metadata.get('message', 'N/A'),
                                "Blocked": "✅" if metadata.get('blocked') else "❌"
                            })
                        
                        st.dataframe(pd.DataFrame(display_data), hide_index=True, width='stretch')
                    else:
                        st.info("Không có security alerts nào trong 7 ngày qua.")
                
                except Exception as e:
                    st.error(f"Lỗi lấy security alerts: {e}")
            
            else:
                st.warning("Không thể lấy thống kê Security cho user này.")
    
    st.divider()
    
    # Instructions
    with st.expander("ℹ️ Hướng dẫn"):
        st.markdown("""
        **Security Monitor** theo dõi và phát hiện các hành vi nghi ngờ:
        
        - **Rapid Actions**: > 50 actions trong 60 giây
        - **Failed Requests**: > 20 failed requests trong 5 phút
        - **Excessive AI Calls**: > 100 AI calls trong 10 phút
        - **Abnormal Vocab Learning**: > 500 từ trong 1 giờ
        - **Repeated Errors**: > 30 errors trong 5 phút
        
        Khi phát hiện pattern nghi ngờ, system sẽ tự động log vào ActivityLog và có thể flag user.
        """)

def render_health_check():
    """Renders the system health check tab."""
    
    # Tabs cho các loại health check
    tab_basic, tab_features, tab_benchmark = st.tabs([
        "🩺 Kiểm tra Cơ bản",
        "🔍 Kiểm tra Chi tiết (Features)",
        "🚀 Benchmark"
    ])
    
    with tab_basic:
        st.subheader("🩺 Kiểm tra kết nối (Health Check)")
        st.caption("Kiểm tra trạng thái hoạt động của từng dịch vụ.")
        
        if st.button("🔍 Quét toàn bộ hệ thống", type="primary"):
            with st.status("Đang kiểm tra hệ thống...", expanded=True) as status:
                # 1. Database
                st.write("Checking Database...")
                db_ok, db_msg, db_dbg = check_db_connection()
                if db_ok: st.success(f"Database: {db_msg}")
                else: st.error(f"Database: {db_msg} | {db_dbg}")
                
                # 2. Storage
                st.write("Checking Storage...")
                st_ok, st_msg, st_dbg = check_storage_service()
                if st_ok: st.success(f"Storage: {st_msg}")
                else: st.error(f"Storage: {st_msg} | {st_dbg}")

                # 3. AI
                st.write("Checking AI Service...")
                ai_ok, ai_msg, ai_dbg = check_ai_service()
                if ai_ok: st.success(f"AI Gemini: {ai_msg}")
                else: st.error(f"AI Gemini: {ai_msg} | {ai_dbg}")

                # 4. TTS
                st.write("Checking TTS Service...")
                tts_ok, tts_msg, tts_dbg = check_tts_service()
                if tts_ok: st.success(f"Edge TTS: {tts_msg}")
                else: st.error(f"Edge TTS: {tts_msg} | {tts_dbg}")
                
                status.update(label="Hoàn tất kiểm tra!", state="complete", expanded=True)
    
    with tab_features:
        st.subheader("🔍 Kiểm tra Chi tiết từng Tính năng")
        st.caption("Kiểm tra sâu từng tính năng trong ứng dụng.")
        
        feature_options = {
            "Tất cả": "all",
            "Vocabulary (Học Từ Vựng)": "vocabulary",
            "Mock Test (Thi Thử)": "mock_test",
            "Shop (Cửa Hàng)": "shop",
            "PvP (Đấu Trường)": "pvp",
            "Grammar (Ngữ Pháp)": "grammar",
            "Listening (Luyện Nghe)": "listening",
            "Speaking (Luyện Nói)": "speaking",
            "Reading (Luyện Đọc)": "reading",
            "Writing (Luyện Viết)": "writing",
            "Translation (Dịch)": "translation",
            "Dashboard": "dashboard",
            "Profile (Hồ Sơ)": "profile"
        }
        
        selected_feature = st.selectbox("Chọn tính năng cần kiểm tra:", options=list(feature_options.keys()))
        
        if st.button("🔍 Kiểm tra Tính năng", type="primary"):
            feature_key = feature_options[selected_feature]
            
            with st.spinner(f"Đang kiểm tra {selected_feature}..."):
                results = run_feature_health_check(feature_key)
                summary = get_health_check_summary(results)
                
                # Display Summary
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Tổng số", summary['total'])
                col2.metric("✅ Thành công", summary['success'], delta=f"{summary['success_rate']}%")
                col3.metric("⚠️ Cảnh báo", summary['warning'])
                col4.metric("❌ Lỗi", summary['error'])
                
                st.metric("⏱️ Thời gian TB", f"{summary['avg_duration_ms']:.2f} ms")
                
                st.divider()
                
                # Display Results
                st.subheader("📋 Chi tiết Kết quả")
                for result in results:
                    status_icon = {
                        'success': '✅',
                        'warning': '⚠️',
                        'error': '❌'
                    }.get(result.status, '❓')
                    
                    with st.expander(f"{status_icon} {result.name} ({result.duration_ms:.2f}ms)", expanded=result.status == 'error'):
                        st.write(f"**Trạng thái:** {result.status.upper()}")
                        st.write(f"**Thông báo:** {result.message}")
                        if result.details:
                            st.code(result.details)
    
    with tab_benchmark:
        st.subheader("🚀 System Benchmark")
        st.caption("Đo tốc độ xử lý thực tế của hệ thống.")
        
        if st.button("⏱️ Chạy Benchmark", type="secondary"):
            with st.spinner("Đang thực hiện Benchmark (Vui lòng đợi)..."):
                results, logs = run_system_benchmark()
                
                # Display Score
                score = results.get('total_score', 0)
                score_color = "green" if score > 80 else "orange" if score > 50 else "red"
                st.markdown(f"""
                <div style="text-align:center; padding: 20px; border: 2px solid {score_color}; border-radius: 10px;">
                    <h1 style="color:{score_color}; margin:0;">{score}/100</h1>
                    <p>Hiệu năng hệ thống</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.divider()
                
                # Metrics
                b1, b2 = st.columns(2)
                b1.metric("DB Read", f"{results.get('db_read', 0):.0f} ms")
                b1.metric("DB Write", f"{results.get('db_write', 0):.0f} ms")
                b2.metric("AI Gen", f"{results.get('ai_gen', 0):.0f} ms")
                b2.metric("TTS Gen", f"{results.get('tts_gen', 0):.0f} ms")
                
                # Chart
                chart_data = pd.DataFrame({
                    'Service': ['DB Read', 'DB Write', 'AI Gen', 'TTS Gen'],
                    'Latency (ms)': [
                        results.get('db_read', 0), 
                        results.get('db_write', 0), 
                        results.get('ai_gen', 0), 
                        results.get('tts_gen', 0)
                    ]
                })
                st.bar_chart(chart_data.set_index('Service'))
                
                with st.expander("📜 Xem Log chi tiết"):
                    for log in logs:
                        st.text(log)

def render_email_settings():
    """Render Email Settings management UI."""
    st.subheader("📧 Cài Đặt Email Thông Báo")
    
    st.info("""
    💡 **Hướng dẫn**:
    - Email này sẽ được dùng để gửi OTP và thông báo cho users
    - Bạn cần sử dụng Gmail với **App Password** (không phải mật khẩu thường)
    - Để tạo App Password: [Google Account → Security → 2FA → App Passwords](https://myaccount.google.com/apppasswords)
    """)
    
    # Get current email config
    email_config = get_email_config()
    current_sender = email_config.get('sender', '')
    current_enabled = email_config.get('enabled', True)
    
    # Display current status
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        status_color = "🟢" if current_enabled else "🔴"
        st.metric("Trạng thái", f"{status_color} {'Đang bật' if current_enabled else 'Đã tắt'}")
    with col2:
        st.metric("Email hiện tại", current_sender if current_sender else "Chưa cấu hình")
    
    st.divider()
    
    # Email Settings Form
    with st.form("email_settings_form"):
        st.subheader("⚙️ Cập Nhật Cấu Hình")
        
        new_sender = st.text_input(
            "📧 Email gửi đi",
            value=current_sender,
            placeholder="your-email@gmail.com",
            help="Địa chỉ Gmail sẽ được dùng để gửi email"
        )
        
        new_password = st.text_input(
            "🔑 App Password",
            type="password",
            placeholder="Nhập App Password (16 ký tự)",
            help="App Password từ Google (không phải mật khẩu Gmail thường)"
        )
        
        email_enabled = st.checkbox(
            "✅ Bật gửi email",
            value=current_enabled,
            help="Bật/tắt chức năng gửi email thông báo"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit_btn = st.form_submit_button("💾 Lưu Cấu Hình", type="primary")
        with col2:
            test_btn = st.form_submit_button("🧪 Test Email")
        
        if submit_btn:
            admin_id = st.session_state.user_info.get('id')
            
            # Validate
            if not new_sender or '@' not in new_sender:
                st.error("❌ Email không hợp lệ!")
            elif not new_password and not email_config.get('password'):
                st.error("❌ Vui lòng nhập App Password!")
            else:
                # Update email config
                password_to_save = new_password if new_password else email_config.get('password', '')
                
                success = update_email_config(new_sender, password_to_save, admin_id)
                
                if success:
                    # Update enabled status
                    toggle_email_enabled(email_enabled, admin_id)
                    
                    st.success("✅ Đã cập nhật cấu hình email thành công!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Không thể cập nhật cấu hình. Vui lòng thử lại!")
        
        if test_btn:
            if not new_sender or not (new_password or email_config.get('password')):
                st.error("❌ Vui lòng nhập đầy đủ email và password để test!")
            else:
                st.info("🧪 Đang gửi email test...")
                
                # Test send email
                from core.email import send_otp_email
                import random
                
                test_otp = random.randint(100000, 999999)
                success, message = send_otp_email(new_sender, test_otp)
                
                if success:
                    st.success(f"✅ Test thành công! Email đã được gửi đến {new_sender}")
                    st.info(f"📧 OTP test: {test_otp}")
                else:
                    st.error(f"❌ Test thất bại: {message}")
    
    # Advanced Settings (Optional)
    with st.expander("⚙️ Cài Đặt Nâng Cao"):
        st.caption("**SMTP Server Settings** (Mặc định cho Gmail)")
        
        all_settings = get_all_system_settings()
        settings_dict = {s['setting_key']: s for s in all_settings}
        
        smtp_server = settings_dict.get('email_smtp_server', {}).get('setting_value', 'smtp.gmail.com')
        smtp_port = settings_dict.get('email_smtp_port', {}).get('setting_value', '587')
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("SMTP Server", value=smtp_server, disabled=True)
        with col2:
            st.text_input("SMTP Port", value=smtp_port, disabled=True)
        
        st.caption("💡 Nếu cần thay đổi SMTP settings, vui lòng liên hệ developer.")
    
    # System Settings Table (for reference)
    st.divider()
    with st.expander("🔍 Xem Tất Cả System Settings"):
        all_settings = get_all_system_settings()
        
        if all_settings:
            df = pd.DataFrame(all_settings)
            # Hide password values
            df['setting_value'] = df.apply(
                lambda row: '***HIDDEN***' if row.get('setting_type') == 'password' 
                else row.get('setting_value'), 
                axis=1
            )
            
            st.dataframe(
                df[['setting_key', 'setting_value', 'setting_type', 'description', 'updated_at']],
                hide_index=True,
                width='stretch'
            )
        else:
            st.warning("Không có settings nào trong database.")

def render_premium_management():
    """Quản lý Subscription"""
    st.subheader("💳 Quản lý Subscription")
    st.write("Điều chỉnh thời hạn Premium và số coin của user")
    
    users_list = get_all_users_list()
    if not users_list:
        st.warning("Không có user nào.")
    else:
        user_options = {f"{u['username']} ({u.get('name', '')}) - Plan: {u.get('plan', 'free')}": u['id'] for u in users_list}
        
        selected_display = st.selectbox("Chọn user:", options=list(user_options.keys()))
        selected_user_id = user_options[selected_display]
        selected_user = next((u for u in users_list if u['id'] == selected_user_id), None)
        
        if selected_user:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Thông tin hiện tại")
                current_plan = selected_user.get('plan', 'free')
                current_coins = selected_user.get('coins', 0)
                subscription = get_user_subscription(selected_user_id)
                
                st.info(f"**Plan:** {current_plan}\n\n**Coin:** {current_coins:,}")
                if subscription:
                    end_date = subscription.get('end_date')
                    if end_date:
                        try:
                            end_dt = pd.to_datetime(end_date)
                            now_dt = pd.Timestamp.now()
                            days_left = (end_dt - now_dt).days
                            st.info(f"**Hết hạn:** {end_dt.strftime('%Y-%m-%d %H:%M')}\n\n**Còn lại:** {days_left} ngày")
                        except:
                            st.info(f"**Hết hạn:** {end_date}")
            
            with col2:
                st.markdown("#### Cập nhật")
                with st.form("premium_update_form"):
                    plan_options_all = ["free", "basic", "premium", "pro"]
                    current_plan_index = plan_options_all.index(current_plan) if current_plan in plan_options_all else 0
                    new_plan = st.selectbox("Plan:", plan_options_all, index=current_plan_index)
                    
                    # Premium Tier selector (only for premium tier plans)
                    new_tier = None
                    if new_plan in ['basic', 'premium', 'pro']:
                        tier_options = ['basic', 'premium', 'pro']
                        current_tier = selected_user.get('premium_tier', 'premium')
                        if current_tier in tier_options:
                            tier_index = tier_options.index(current_tier)
                        else:
                            tier_index = tier_options.index(new_plan) if new_plan in tier_options else 1
                        new_tier = st.selectbox(
                            "Tier:", 
                            tier_options, 
                            index=tier_index,
                            help="basic: 300 lượt/tháng | premium: 600 lượt/tháng | pro: 1200 lượt/tháng"
                        )
                    
                    col_date1, col_date2 = st.columns(2)
                    with col_date1:
                        end_date_input = st.date_input("Ngày hết hạn:", value=pd.to_datetime(subscription.get('end_date')).date() if subscription and subscription.get('end_date') else pd.Timestamp.now().date() + pd.Timedelta(days=30))
                    with col_date2:
                        end_time_input = st.time_input("Giờ hết hạn:", value=pd.Timestamp.now().time())
                    
                    end_datetime = pd.Timestamp.combine(end_date_input, end_time_input).isoformat()
                    
                    coin_change = st.number_input("Thay đổi coin (có thể âm để giảm):", value=0, step=100)
                    new_coin = current_coins + coin_change
                    
                    if st.form_submit_button("✅ Cập nhật", type="primary"):
                        # Update plan and tier
                        from services.admin_service import admin_update_user_comprehensive
                        success, msg = admin_update_user_comprehensive(
                            user_id=selected_user_id,
                            plan=new_plan,
                            premium_tier=new_tier if new_plan in ['basic', 'premium', 'pro'] else None
                        )
                        if success and update_user_premium(selected_user_id, new_plan, end_datetime, new_coin):
                            # Clear cache to show updated coin immediately
                            st.cache_data.clear()
                            st.success("✅ Đã cập nhật thành công!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Lỗi cập nhật.")
        
        st.divider()
        st.subheader("📋 Danh sách Premium Users")
        premium_users = [u for u in users_list if u.get('plan') in ['basic', 'premium', 'pro']]
        if premium_users:
            df_premium = pd.DataFrame(premium_users)
            st.dataframe(df_premium[['username', 'name', 'plan', 'coins']], width='stretch')
            
            # Premium AI Usage Statistics
            st.divider()
            st.subheader("📊 Thống Kê Sử Dụng AI (Premium Users)")
            try:
                from services.premium_usage_service import get_all_premium_users_usage
                usage_list = get_all_premium_users_usage()
                
                if usage_list:
                    df_usage = pd.DataFrame(usage_list)
                    # Calculate remaining from limit - usage_count
                    df_usage['remaining'] = df_usage.apply(lambda row: max(0, row['limit'] - row['usage_count']), axis=1)
                    df_usage['status'] = df_usage.apply(lambda row: 
                        '🔴 Hết Limit' if row['usage_count'] >= row['limit'] 
                        else ('🟡 Gần Hết' if row['usage_count'] >= row['limit'] * 0.8 
                              else '🟢 Bình Thường'), axis=1)
                    
                    # Display with color coding
                    display_cols = ['username', 'name', 'tier', 'usage_count', 'limit', 'remaining', 'topup_balance', 'total_remaining', 'percentage', 'status']
                    available_cols = [col for col in display_cols if col in df_usage.columns]
                    st.dataframe(
                        df_usage[available_cols],
                        width='stretch'
                    )
                    
                    # Summary stats
                    col1, col2, col3 = st.columns(3)
                    total_usage = df_usage['usage_count'].sum()
                    total_limit = df_usage['limit'].sum()
                    avg_usage = df_usage['usage_count'].mean()
                    
                    col1.metric("Tổng Usage", f"{total_usage:,}")
                    col2.metric("Tổng Limit", f"{total_limit:,}")
                    col3.metric("TB Usage/User", f"{avg_usage:.0f}")
                    
                    # Warning for high usage users
                    high_usage = df_usage[df_usage['usage_count'] >= df_usage['limit'] * 0.8]
                    if len(high_usage) > 0:
                        st.warning(f"⚠️ {len(high_usage)} user(s) đang sử dụng > 80% limit:")
                        for _, row in high_usage.iterrows():
                            st.write(f"- **{row['username']}**: {row['usage_count']}/{row['limit']} ({row['percentage']}%)")
                else:
                    st.info("Chưa có dữ liệu usage cho Premium users.")
            except Exception as e:
                st.error(f"Lỗi khi lấy thống kê usage: {e}")
        else:
            st.info("Chưa có premium user nào.")

def render_feature_flags_management():
    """Quản lý Feature Flags"""
    st.subheader("⚙️ Quản lý Tính năng")
    st.write("Bật/tắt các tính năng trên ứng dụng. Khi tắt, tính năng sẽ hiển thị 'đang bảo trì' trên sidebar.")
    
    df_flags = get_all_feature_flags()
    if df_flags.empty:
        st.warning("Chưa có feature flag nào. Chạy SQL script để tạo.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("")
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        # Display flags in a form for each
        for idx, row in df_flags.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{row['feature_name']}** (`{row['feature_key']}`)")
                    current_status = "🟢 Đang hoạt động" if row['is_enabled'] else "🔴 Đang bảo trì"
                    st.caption(current_status)
                
                with col2:
                    new_status = st.checkbox("Bật", value=bool(row['is_enabled']), key=f"flag_{row['feature_key']}")
                
                with col3:
                    if st.button("💾 Lưu", key=f"save_{row['feature_key']}"):
                        if update_feature_flag(row['feature_key'], new_status):
                            st.success("✅ Đã cập nhật!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Lỗi!")
                
                if not row['is_enabled']:
                    maintenance_msg = st.text_input(
                        "Thông báo bảo trì:", 
                        value=row.get('maintenance_message', 'Tính năng đang được bảo trì'),
                        key=f"msg_{row['feature_key']}"
                    )
                    if st.button("💾 Cập nhật thông báo", key=f"upd_msg_{row['feature_key']}"):
                        if update_feature_flag(row['feature_key'], False, maintenance_msg):
                            st.success("✅ Đã cập nhật!")
                            time.sleep(0.5)
                            st.rerun()
                
                st.divider()

def render_shop_management():
    """Quản lý Cửa hàng"""
    st.subheader("🛍️ Quản lý Cửa hàng")
    st.write("Thêm, sửa, xóa và quản lý các vật phẩm trong cửa hàng")
    
    shop_items = get_all_shop_items()
    
    # Tabs cho các chức năng
    tab_list, tab_add, tab_edit, tab_delete = st.tabs([
        "📋 Danh sách vật phẩm",
        "➕ Thêm vật phẩm",
        "✏️ Sửa vật phẩm",
        "🗑️ Xóa vật phẩm"
    ])
    
    with tab_list:
        st.subheader("📋 Danh sách vật phẩm hiện có")
        if not shop_items:
            st.info("Chưa có vật phẩm nào trong cửa hàng.")
        else:
            df = pd.DataFrame(shop_items)
            # Reorder columns for better display
            display_cols = ['id', 'icon', 'name', 'type', 'cost', 'value', 'description']
            available_cols = [col for col in display_cols if col in df.columns]
            st.dataframe(df[available_cols], hide_index=True, width='stretch')
    
    with tab_add:
        st.subheader("➕ Thêm vật phẩm mới")
        with st.form("add_shop_item", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Tên vật phẩm *", placeholder="VD: Gold Frame")
                new_icon = st.text_input("Icon (emoji) *", placeholder="VD: 🏆")
                new_type = st.selectbox(
                    "Loại vật phẩm *",
                    ["theme", "avatar_frame", "title", "streak_freeze", "powerup"],
                    index=0
                )
                new_cost = st.number_input("Giá (coin) *", min_value=0, value=100, step=10)
            with col2:
                new_description = st.text_area("Mô tả", placeholder="Mô tả về vật phẩm")
                new_value = st.text_input("Giá trị (optional)", placeholder="VD: gold_frame, fire_frame")
            
            if st.form_submit_button("✅ Thêm vật phẩm", type="primary"):
                if not new_name or not new_icon or not new_cost:
                    st.error("❌ Vui lòng điền đầy đủ các trường bắt buộc (*)")
                else:
                    success, message = create_shop_item(
                        name=new_name,
                        description=new_description or "",
                        icon=new_icon,
                        cost=new_cost,
                        item_type=new_type,
                        value=new_value if new_value else None
                    )
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    with tab_edit:
        st.subheader("✏️ Sửa vật phẩm")
        if not shop_items:
            st.info("Chưa có vật phẩm nào để sửa.")
        else:
            item_options = {f"{item['icon']} {item['name']} (ID: {item['id']})": item['id'] for item in shop_items}
            selected_display = st.selectbox("Chọn vật phẩm cần sửa:", options=list(item_options.keys()))
            selected_item_id = item_options[selected_display]
            selected_item = next((item for item in shop_items if item['id'] == selected_item_id), None)
            
            if selected_item:
                with st.form("edit_shop_item"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("Tên vật phẩm", value=selected_item.get('name', ''))
                        edit_icon = st.text_input("Icon (emoji)", value=selected_item.get('icon', ''))
                        edit_type = st.selectbox(
                            "Loại vật phẩm",
                            ["theme", "avatar_frame", "title", "streak_freeze", "powerup"],
                            index=["theme", "avatar_frame", "title", "streak_freeze", "powerup"].index(selected_item.get('type', 'theme')) if selected_item.get('type') in ["theme", "avatar_frame", "title", "streak_freeze", "powerup"] else 0
                        )
                        edit_cost = st.number_input("Giá (coin)", min_value=0, value=int(selected_item.get('cost', 0)), step=10)
                    with col2:
                        edit_description = st.text_area("Mô tả", value=selected_item.get('description', ''))
                        edit_value = st.text_input("Giá trị", value=selected_item.get('value', '') or '')
                    
                    if st.form_submit_button("💾 Cập nhật", type="primary"):
                        success, message = update_shop_item(
                            item_id=selected_item_id,
                            name=edit_name,
                            description=edit_description,
                            icon=edit_icon,
                            cost=edit_cost,
                            item_type=edit_type,
                            value=edit_value if edit_value else None
                        )
                        if success:
                            st.success(f"✅ {message}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
    
    with tab_delete:
        st.subheader("🗑️ Xóa vật phẩm")
        st.warning("⚠️ Lưu ý: Chỉ có thể xóa vật phẩm chưa có người dùng nào sở hữu!")
        
        if not shop_items:
            st.info("Chưa có vật phẩm nào để xóa.")
        else:
            item_options = {f"{item['icon']} {item['name']} (ID: {item['id']})": item['id'] for item in shop_items}
            selected_display = st.selectbox("Chọn vật phẩm cần xóa:", options=list(item_options.keys()), key="delete_select")
            selected_item_id = item_options[selected_display]
            selected_item = next((item for item in shop_items if item['id'] == selected_item_id), None)
            
            if selected_item:
                st.info(f"**Vật phẩm:** {selected_item['icon']} {selected_item['name']}\n\n**Mô tả:** {selected_item.get('description', 'N/A')}\n\n**Giá:** {selected_item.get('cost', 0)} coin")
                
                if st.button("🗑️ Xóa vật phẩm này", type="primary"):
                    success, message = delete_shop_item(selected_item_id)
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

def render_bot_tester():
    """Render Bot Tester UI"""
    st.subheader("🤖 Bot Tester - Kiểm tra tự động toàn bộ chức năng")
    st.caption("Bot sẽ đóng vai một user và test 100% chức năng trong app")
    
    # Get all users for selection
    users_list = get_all_users()
    
    if not users_list:
        st.warning("Không có user nào trong hệ thống. Vui lòng tạo user trước khi chạy bot test.")
        return
    
    # User selection
    user_options = {f"{u.get('username', 'Unknown')} (ID: {u.get('id')})": u.get('id') for u in users_list}
    selected_user_label = st.selectbox(
        "Chọn user account để bot test:",
        options=list(user_options.keys()),
        help="Bot sẽ sử dụng account này để test các chức năng"
    )
    selected_user_id = user_options[selected_user_label]
    
    # Display selected user info
    selected_user = next((u for u in users_list if u.get('id') == selected_user_id), None)
    if selected_user:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Username", selected_user.get('username', 'N/A'))
        with col2:
            st.metric("Role", selected_user.get('role', 'N/A'))
        with col3:
            st.metric("Status", selected_user.get('status', 'N/A'))
    
    st.divider()
    
    # Run tests button
    if st.button("🚀 Chạy Bot Test", type="primary", width='stretch'):
        with st.spinner("🤖 Bot đang test toàn bộ chức năng... Vui lòng đợi..."):
            try:
                report = run_bot_tests(selected_user_id)
                st.session_state['bot_test_report'] = report
                st.success("✅ Bot test hoàn thành!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Lỗi khi chạy bot test: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display report if available
    if 'bot_test_report' in st.session_state:
        report = st.session_state['bot_test_report']
        
        st.divider()
        st.subheader("📊 Kết quả Test")
        
        summary = report.get('summary', {})
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tổng số Test", summary.get('total', 0))
        with col2:
            st.metric("✅ Passed", summary.get('passed', 0), delta=f"{summary.get('pass_rate', 0):.1f}%")
        with col3:
            st.metric("❌ Failed", summary.get('failed', 0), delta=None, delta_color="inverse")
        with col4:
            st.metric("⏭️ Skipped", summary.get('skipped', 0))
        
        if summary.get('duration_seconds'):
            st.caption(f"⏱️ Thời gian test: {summary.get('duration_seconds', 0):.2f} giây")
        
        st.divider()
        
        # Failed tests
        failed_tests = report.get('failed_tests', [])
        if failed_tests:
            st.subheader("❌ Các Test Bị Lỗi")
            with st.expander(f"Xem chi tiết {len(failed_tests)} test bị lỗi", expanded=True):
                for test in failed_tests:
                    st.error(f"**{test['feature']} - {test['test_name']}**")
                    st.write(f"📝 Message: {test['message']}")
                    if test.get('error'):
                        with st.expander("🔍 Chi tiết lỗi"):
                            st.code(test['error'], language='python')
                    st.divider()
        else:
            st.success("🎉 Tuyệt vời! Không có test nào bị lỗi!")
        
        st.divider()
        
        # Results by feature
        st.subheader("📋 Kết quả theo Feature")
        by_feature = report.get('by_feature', {})
        
        for feature, data in by_feature.items():
            pass_count = data.get('pass', 0)
            fail_count = data.get('fail', 0)
            skip_count = data.get('skip', 0)
            total = pass_count + fail_count + skip_count
            
            status_icon = "✅" if fail_count == 0 else "❌"
            
            with st.expander(f"{status_icon} **{feature}** (Pass: {pass_count} | Fail: {fail_count} | Skip: {skip_count})"):
                for test in data.get('tests', []):
                    if test['status'] == 'pass':
                        st.success(f"✅ {test['test_name']}: {test['message']}")
                    elif test['status'] == 'fail':
                        st.error(f"❌ {test['test_name']}: {test['message']}")
                    else:
                        st.info(f"⏭️ {test['test_name']}: {test['message']}")
        
        # Export report button
        st.divider()
        import json
        report_json = json.dumps(report, indent=2, ensure_ascii=False)
        st.download_button(
            "💾 Tải báo cáo JSON",
            data=report_json,
            file_name=f"bot_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # Clear report button
        if st.button("🗑️ Xóa báo cáo", width='stretch'):
            if 'bot_test_report' in st.session_state:
                del st.session_state['bot_test_report']
            st.rerun()
    
    # Instructions
    with st.expander("ℹ️ Hướng dẫn sử dụng Bot Tester"):
        st.markdown("""
        **Bot Tester** sẽ tự động test toàn bộ chức năng trong app như một user thật:
        
        **Các chức năng được test:**
        - ✅ Authentication & User Info
        - ✅ Dashboard & Stats
        - ✅ Vocabulary Learning
        - ✅ Mock Test
        - ✅ Shop (Items, Inventory, Coins)
        - ✅ Profile & Settings
        - ✅ Daily & Weekly Quests
        - ✅ Grammar
        - ✅ PvP
        - ✅ Admin Features (nếu user là admin)
        
        **Cách sử dụng:**
        1. Chọn user account để bot sử dụng (khuyên dùng account test riêng)
        2. Click "🚀 Chạy Bot Test"
        3. Đợi bot test xong (thường mất vài giây)
        4. Xem báo cáo chi tiết về các test pass/fail/skip
        5. Fix các lỗi được báo cáo
        
        **Lưu ý:**
        - Bot sẽ sử dụng account được chọn để test
        - Một số test có thể modify dữ liệu (ví dụ: thêm coin)
        - Khuyên dùng account test riêng, không dùng account production
        """)

def render_feedback_stats():
    """Thống kê Feedback"""
    df_fb = get_all_feedback()
    
    if df_fb.empty:
        st.info("Chưa có dữ liệu để thống kê.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        total = len(df_fb)
        new_count = len(df_fb[df_fb['status'] == 'New'])
        processing_count = len(df_fb[df_fb['status'] == 'Processing'])
        done_count = len(df_fb[df_fb['status'] == 'Done'])
        
        with col1:
            st.metric("📊 Tổng số", total)
        with col2:
            st.metric("🆕 Mới", new_count, delta=None)
        with col3:
            st.metric("⚙️ Đang xử lý", processing_count)
        with col4:
            st.metric("✅ Đã xử lý", done_count)
        
        st.divider()
        
        # Statistics by type
        st.subheader("📈 Thống kê theo loại")
        type_counts = df_fb['type'].value_counts() if 'type' in df_fb.columns else pd.Series()
        if not type_counts.empty:
            st.bar_chart(type_counts)
        
        # Statistics by module
        st.subheader("📦 Thống kê theo module")
        module_counts = df_fb['module'].value_counts() if 'module' in df_fb.columns else pd.Series()
        if not module_counts.empty:
            st.bar_chart(module_counts)

# Run the page
show()
