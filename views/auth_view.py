import streamlit as st
import time
import secrets
from core.auth import check_login, get_email_by_username, update_user_password, create_new_user, check_username_exists, check_email_exists
from services.shop_service import get_user_inventory
from core.email import send_otp_email

def render_auth_page():
    """Hiển thị trang xác thực (Đăng nhập / Đăng ký / Quên mật khẩu)"""
    
    # Ẩn sidebar khi ở màn hình login
    if not st.session_state.get('logged_in', False):
        st.markdown("""<style>section[data-testid="stSidebar"] {display: none !important;}</style>""", unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 1.2], gap="large")

    with left_col:
        if st.session_state.auth_mode == 'login':
            st.markdown("<h1 style='text-align: center; color: #003366;'>English Master</h1>", unsafe_allow_html=True)
            st.caption("Hệ thống học tập thông minh All-in-One")
            
            with st.form("login_form"):
                u = st.text_input("Tên đăng nhập", autocomplete="username")
                p = st.text_input("Mật khẩu", type="password", autocomplete="current-password")
                if st.form_submit_button("Đăng nhập", type="primary"):
                    user = check_login(u, p)
                    if user == "LOCKED":
                        st.error("Tài khoản đã bị khóa.")
                    elif user:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user
                        try:
                            inv = get_user_inventory(user['id'])
                            active_theme = next((item['ShopItems']['value'] for item in inv if item.get('is_active') and item.get('ShopItems')), None)
                            if active_theme: st.session_state.active_theme_value = active_theme
                        except: pass
                        
                        # Pre-load vocabulary data in background for faster page loads
                        try:
                            from core.vocab_preloader import preload_vocabulary_data
                            preload_vocabulary_data()
                        except Exception as e:
                            # Silent fail - preload is not critical
                            pass
                        
                        st.rerun()
                    else:
                        st.error("Sai tên đăng nhập hoặc mật khẩu.")
            
            if st.button("Quên mật khẩu?", type="tertiary"):
                st.session_state.auth_mode = 'forgot'
                st.rerun()
            if st.button("Chưa có tài khoản? Đăng ký ngay", type="secondary"):
                st.session_state.auth_mode = 'register'
                st.rerun()

        elif st.session_state.auth_mode == 'forgot':
            st.subheader("Khôi phục mật khẩu")
            if 'otp_step' not in st.session_state: st.session_state.otp_step = 1
            
            if st.session_state.otp_step == 1:
                u_reset = st.text_input("Nhập tên đăng nhập:", autocomplete="username")
                if st.button("Gửi mã OTP"):
                    email = get_email_by_username(u_reset)
                    if email:
                        otp = str(secrets.randbelow(900000) + 100000)
                        send_otp_email(email, otp)
                        st.session_state.otp_gen = otp
                        st.session_state.reset_u = u_reset
                        st.session_state.otp_step = 2
                        st.success("Đã gửi mã OTP!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Không tìm thấy tài khoản.")
                if st.button("Quay lại"):
                    st.session_state.auth_mode = 'login'
                    st.rerun()
            
            elif st.session_state.otp_step == 2:
                otp_in = st.text_input("Nhập mã OTP:", autocomplete="one-time-code")
                new_p = st.text_input("Mật khẩu mới:", type="password", autocomplete="new-password")
                if st.button("Xác nhận đổi"):
                    if otp_in == st.session_state.otp_gen:
                        update_user_password(st.session_state.reset_u, new_p)
                        st.success("Đổi mật khẩu thành công!")
                        st.session_state.auth_mode = 'login'
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Sai mã OTP.")

        elif st.session_state.auth_mode == 'register':
            st.subheader("Tạo tài khoản mới")
            
            # OTP step management
            if 'otp_step' not in st.session_state:
                st.session_state.otp_step = 1
                st.session_state.reg_data = {}
            
            if st.session_state.otp_step == 1:
                # Step 1: Registration form
                with st.form("register_form"):
                    reg_name = st.text_input("Họ và tên*")
                    reg_email = st.text_input("Email*")
                    reg_user = st.text_input("Tên đăng nhập*")
                    reg_pass = st.text_input("Mật khẩu*", type="password", help="Mật khẩu phải có ít nhất 6 ký tự, bao gồm chữ cái và số")
                    
                    # Password requirements note
                    st.caption("🔒 **Yêu cầu mật khẩu:** Tối thiểu 6 ký tự, khuyến nghị bao gồm chữ cái và số để bảo mật tốt hơn")
                    
                    reg_role = "user"

                    st.markdown("---")
                    st.markdown("###### Gói dịch vụ:")
                    
                    # Only Free plan is available (all paid plans disabled until payment gateway is ready)
                    st.markdown("**Free (Miễn phí)** - 5 lượt AI/ngày")
                    st.caption("💡 Gói Free: Miễn phí, phù hợp cho người mới bắt đầu")
                    
                    reg_plan = "free"  # Force Free plan only
                    
                    # Show disabled plans info
                    st.info("ℹ️ **Gói Basic** (300 lượt/tháng), **Gói Premium** (600 lượt/tháng) và **Gói Pro** (1200 lượt/tháng) đang được cập nhật. Sẽ sớm có mặt sau khi triển khai phương thức thanh toán. Admin có thể nâng cấp tài khoản thủ công.")
                    
                    if st.form_submit_button("Tiếp tục", type="primary"):
                        # Validation
                        errors = []
                        
                        if not all([reg_name, reg_email, reg_user, reg_pass]):
                            errors.append("Vui lòng điền đầy đủ thông tin.")
                        
                        # Password validation
                        if reg_pass and len(reg_pass) < 6:
                            errors.append("Mật khẩu phải có ít nhất 6 ký tự.")
                        
                        # Check username and email uniqueness (only if form is filled)
                        if reg_user and reg_email and not errors:
                            # Check username
                            if check_username_exists(reg_user):
                                errors.append(f"Tên đăng nhập '{reg_user}' đã được sử dụng. Vui lòng chọn tên khác.")
                            
                            # Check email
                            if check_email_exists(reg_email):
                                errors.append(f"Email '{reg_email}' đã được sử dụng. Vui lòng sử dụng email khác hoặc đăng nhập.")
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        else:
                            # Store registration data and send OTP
                            st.session_state.reg_data = {
                                'name': reg_name,
                                'email': reg_email,
                                'username': reg_user,
                                'password': reg_pass,
                                'role': reg_role,
                                'plan': reg_plan
                            }
                            
                            # Generate and send OTP
                            otp = str(secrets.randbelow(900000) + 100000)
                            try:
                                send_otp_email(reg_email, otp)
                                st.session_state.otp_gen = otp
                                st.session_state.otp_step = 2
                                st.success("Đã gửi mã OTP đến email của bạn! Vui lòng kiểm tra hộp thư.")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Không thể gửi email OTP. Vui lòng thử lại sau. Lỗi: {str(e)}")
            
            elif st.session_state.otp_step == 2:
                # Step 2: OTP verification
                st.info("📧 Mã OTP đã được gửi đến email của bạn. Vui lòng nhập mã để hoàn tất đăng ký.")
                otp_in = st.text_input("Nhập mã OTP (6 chữ số):", max_chars=6, placeholder="000000")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Xác nhận OTP", type="primary"):
                        if otp_in == st.session_state.otp_gen:
                            # OTP correct, create user
                            reg_data = st.session_state.reg_data
                            ok, msg = create_new_user(
                                reg_data['username'],
                                reg_data['password'],
                                reg_data['name'],
                                reg_data['role'],
                                reg_data['email'],
                                plan=reg_data['plan']
                            )
                            if ok:
                                st.success(f"Đăng ký thành công gói {reg_data['plan'].upper()}! Vui lòng đăng nhập.")
                                # Clear registration data
                                if 'otp_step' in st.session_state:
                                    del st.session_state.otp_step
                                if 'otp_gen' in st.session_state:
                                    del st.session_state.otp_gen
                                if 'reg_data' in st.session_state:
                                    del st.session_state.reg_data
                                st.session_state.auth_mode = 'login'
                                time.sleep(2)
                                st.rerun()
                            else:
                                # Check if error is about duplicate
                                if "already exists" in msg.lower() or "đã được sử dụng" in msg.lower():
                                    if "username" in msg.lower():
                                        st.error(f"Tên đăng nhập '{reg_data['username']}' đã được sử dụng. Vui lòng chọn tên khác.")
                                    elif "email" in msg.lower():
                                        st.error(f"Email '{reg_data['email']}' đã được sử dụng. Vui lòng sử dụng email khác hoặc đăng nhập.")
                                    else:
                                        st.error(f"Lỗi: {msg}")
                                else:
                                    st.error(f"Lỗi: {msg}")
                        else:
                            st.error("Mã OTP không đúng. Vui lòng thử lại.")
                
                with col2:
                    if st.button("Gửi lại OTP"):
                        reg_data = st.session_state.reg_data
                        otp = str(secrets.randbelow(900000) + 100000)
                        try:
                            send_otp_email(reg_data['email'], otp)
                            st.session_state.otp_gen = otp
                            st.success("Đã gửi lại mã OTP!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Không thể gửi email OTP. Vui lòng thử lại sau. Lỗi: {str(e)}")
                
                if st.button("Quay lại"):
                    st.session_state.otp_step = 1
                    st.rerun()
            if st.button("Đã có tài khoản? Đăng nhập"):
                st.session_state.auth_mode = 'login'
                st.rerun()

    with right_col:
        st.markdown("## Nâng Tầm Tiếng Anh Của Bạn")
        st.markdown("**English Master** không chỉ là một ứng dụng học từ vựng, mà là một hệ sinh thái toàn diện giúp bạn chinh phục tiếng Anh một cách hiệu quả và thú vị.")
        
        st.markdown("""
        <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <span>Học từ vựng thông minh với thuật toán **Lặp lại ngắt quãng (SRS)**.</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <span>Luyện 4 kỹ năng Nghe-Nói-Đọc-Viết với **phản hồi tức thì từ AI**.</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🎮</span>
            <span>Hệ thống **Gamification** (Streak, Coin, PvP) tạo động lực mỗi ngày.</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🎯</span>
            <span>**Kiểm tra đầu vào** và nhận lộ trình học tập cá nhân hóa.</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.markdown("### So Sánh Gói Dịch Vụ")
        
        st.markdown("""
        <style>
        .comp-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.9em; }
        .comp-table th, .comp-table td { padding: 10px 8px; text-align: left; border-bottom: 1px solid #eee; }
        .comp-table th { background-color: #f8f9fa; color: #333; font-weight: bold; text-align: center; }
        .comp-table td.check { color: #2ecc71; font-weight: bold; text-align: center; }
        .comp-table td.cross { color: #e74c3c; text-align: center; }
        .comp-table td.center { text-align: center; }
        .comp-table tr:hover { background-color: #f1f1f1; }
        .comp-table .tier-basic { color: #3498db; font-weight: bold; }
        .comp-table .tier-premium { color: #d35400; font-weight: bold; }
        .comp-table .tier-pro { color: #9b59b6; font-weight: bold; }
        </style>
        
        <table class="comp-table">
            <thead>
                <tr>
                    <th style="width: 25%;">Tính năng</th>
                    <th style="width: 18.75%;">Free</th>
                    <th style="width: 18.75%;" class="tier-basic">Basic</th>
                    <th style="width: 18.75%;" class="tier-premium">Premium</th>
                    <th style="width: 18.75%;" class="tier-pro">Pro</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>📚 Học từ vựng (SRS)</td>
                    <td class="center">20 từ/ngày</td>
                    <td class="check">♾️ Không giới hạn</td>
                    <td class="check">♾️ Không giới hạn</td>
                    <td class="check">♾️ Không giới hạn</td>
                </tr>
                <tr>
                    <td>🤖 Luyện kỹ năng AI</td>
                    <td class="center">5 lượt/ngày</td>
                    <td class="center">300 lượt/tháng</td>
                    <td class="center">600 lượt/tháng</td>
                    <td class="center">1200 lượt/tháng</td>
                </tr>
                <tr>
                    <td>⚡ Mua thêm lượt AI (Top-up)</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                </tr>
                <tr>
                    <td>🧪 Bài học Ngữ pháp</td>
                    <td class="center">Chỉ A1, A2</td>
                    <td class="check">🔓 A1-C2</td>
                    <td class="check">🔓 A1-C2</td>
                    <td class="check">🔓 A1-C2</td>
                </tr>
                <tr>
                    <td>🎯 Kiểm tra lại trình độ</td>
                    <td class="cross">❌</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                </tr>
                <tr>
                    <td>📊 Xuất dữ liệu (CSV/Excel)</td>
                    <td class="cross">❌</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                </tr>
                <tr>
                    <td>💎 Khung Avatar & Danh hiệu VIP</td>
                    <td class="cross">❌</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                    <td class="check">✅</td>
                </tr>
                <tr>
                    <td>🚫 Quảng cáo</td>
                    <td class="center">Có thể có</td>
                    <td class="check">✅ Không quảng cáo</td>
                    <td class="check">✅ Không quảng cáo</td>
                    <td class="check">✅ Không quảng cáo</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)
        
        st.caption("ℹ️ **Lưu ý:** Gói **Free** đang có sẵn để đăng ký. Các gói **Basic** (300 lượt/tháng), **Premium** (600 lượt/tháng) và **Pro** (1200 lượt/tháng) đang được cập nhật và sẽ sớm có mặt sau khi triển khai phương thức thanh toán. Admin có thể nâng cấp tài khoản thủ công.")