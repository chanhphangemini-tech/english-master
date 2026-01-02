"""View components for Settings page."""
import streamlit as st
import time
from typing import Dict, Any, Tuple, Optional
from PIL import Image
import io

try:
    from streamlit_cropper import st_cropper
    HAS_CROPPER = True
except ImportError:
    HAS_CROPPER = False


def render_avatar_upload_section(username: str, on_upload_callback) -> None:
    """Render avatar upload section với chức năng crop ảnh cho phép user chọn vùng cắt."""
    st.subheader("Ảnh đại diện")
    
    # Hiển thị avatar hiện tại
    current_avatar = st.session_state.user_info.get('avatar_url')
    if current_avatar:
        st.markdown("**Ảnh đại diện hiện tại:**")
        st.image(current_avatar, width=150)
        st.markdown("---")
    
    st.info("ℹ️ **Lưu ý:** Ảnh sẽ được cắt thành hình vuông 1:1 để hiển thị đúng trong khung tròn của hệ thống. Bạn có thể kéo và điều chỉnh vùng cắt trực tiếp trên ảnh.")
    
    uploaded_file = st.file_uploader(
        "📤 Tải ảnh mới (PNG, JPG, JPEG)", 
        type=['png', 'jpg', 'jpeg'],
        help="Chọn ảnh để upload. Sau đó bạn có thể điều chỉnh vùng cắt."
    )
    
    crop_box = None
    
    if uploaded_file:
        # Đọc ảnh để hiển thị preview
        img = Image.open(uploaded_file)
        original_size = img.size
        
        # Convert RGBA nếu cần
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Tính toán kích thước crop box mặc định (hình vuông ở giữa)
        min_dimension = min(original_size[0], original_size[1])
        default_crop_size = min_dimension
        default_x = (original_size[0] - default_crop_size) // 2
        default_y = (original_size[1] - default_crop_size) // 2
        
        # Lưu vào session state để giữ giá trị khi rerun
        crop_key = f"crop_{username}_{uploaded_file.name}"
        if crop_key not in st.session_state:
            st.session_state[crop_key] = {
                'x': default_x,
                'y': default_y,
                'size': default_crop_size
            }
        
        crop_state = st.session_state[crop_key]
        
        # Hiển thị preview và controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**✂️ Kéo và điều chỉnh vùng cắt trực tiếp trên ảnh:**")
            st.caption("💡 Kéo các góc và cạnh của khung để điều chỉnh vùng cắt. Khung luôn là hình vuông 1:1.")
            
            if HAS_CROPPER:
                # Sử dụng streamlit_cropper để cho phép tương tác trực tiếp
                from core.auth import crop_image_to_square
                
                # Tính toán realtime_update để preview cập nhật ngay
                realtime_update = st.checkbox("Cập nhật preview theo thời gian thực", value=True, key=f"{crop_key}_realtime")
                
                # Hiển thị cropper với aspect ratio 1:1 (hình vuông)
                cropped_img = st_cropper(
                    img,
                    realtime_update=realtime_update,
                    box_color='#FF0000',
                    aspect_ratio=(1, 1),
                    return_type="box",  # Trả về box coordinates
                    key=f"{crop_key}_cropper"
                )
                
                # Lấy thông tin crop box từ cropper
                if cropped_img:
                    # cropped_img là dict với keys: left, top, width, height
                    crop_box = (
                        int(cropped_img['left']),
                        int(cropped_img['top']),
                        int(cropped_img['width']),
                        int(cropped_img['height'])
                    )
                    
                    # Cập nhật crop_state
                    crop_state['x'] = crop_box[0]
                    crop_state['y'] = crop_box[1]
                    crop_state['size'] = min(crop_box[2], crop_box[3])  # Đảm bảo hình vuông
                else:
                    # Fallback nếu không có dữ liệu
                    crop_box = (
                        crop_state['x'],
                        crop_state['y'],
                        crop_state['size'],
                        crop_state['size']
                    )
            else:
                # Fallback nếu không có streamlit_cropper
                st.warning("⚠️ Thư viện streamlit-cropper chưa được cài đặt. Vui lòng chạy: `pip install streamlit-cropper`")
                st.info("Đang sử dụng chế độ cắt tự động...")
                from core.auth import crop_image_to_square
                crop_box = None
        
        with col2:
            st.markdown("**Preview sau khi cắt:**")
            
            # Tạo preview ảnh đã crop
            from core.auth import crop_image_to_square
            
            if crop_box:
                preview_img = crop_image_to_square(img.copy(), crop_box)
            else:
                preview_img = crop_image_to_square(img.copy(), None)
            
            preview_img_resized = preview_img.resize((200, 200), Image.Resampling.LANCZOS)
            
            # Hiển thị ảnh trong khung tròn bằng cách sử dụng HTML/CSS
            # Convert ảnh sang base64 để embed vào HTML
            import base64
            buffered = io.BytesIO()
            preview_img_resized.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            st.markdown(f"""
            <div style="
                width: 200px; 
                height: 200px; 
                border-radius: 50%; 
                overflow: hidden; 
                border: 4px solid #667eea;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                margin: 0 auto;
                display: flex;
                align-items: center;
                justify-content: center;
                background: white;
            ">
                <img src="data:image/png;base64,{img_str}" 
                     style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;" 
                     alt="Preview">
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("👆 Đây là cách ảnh sẽ hiển thị trong hệ thống")
            
            # Hiển thị thông tin crop box (optional, để debug)
            if HAS_CROPPER and crop_box:
                with st.expander("ℹ️ Thông tin vùng cắt", expanded=False):
                    st.write(f"**Vị trí:** X={crop_box[0]}, Y={crop_box[1]}")
                    st.write(f"**Kích thước:** {crop_box[2]} x {crop_box[3]} px")
        
        # Nút upload
        if st.button("💾 Lưu Avatar mới", type="primary"):
            with st.spinner("🔄 Đang xử lý và tải lên..."):
                # Reset file pointer
                uploaded_file.seek(0)
                on_upload_callback(username, uploaded_file, crop_box)
                # Xóa crop state sau khi upload thành công
                if crop_key in st.session_state:
                    del st.session_state[crop_key]


def render_password_change_form(username: str, on_change_callback) -> None:
    """Render password change form."""
    st.subheader("Đổi mật khẩu đăng nhập")
    with st.form("change_pass_form"):
        cur_p = st.text_input("Mật khẩu cũ", type="password")
        new_p = st.text_input("Mật khẩu mới", type="password")
        cnf_p = st.text_input("Nhập lại mật khẩu mới", type="password")
        
        if st.form_submit_button("Lưu thay đổi", type="primary"):
            if new_p != cnf_p:
                st.error("Mật khẩu xác nhận không khớp.")
            else:
                on_change_callback(username, cur_p, new_p)


def render_notification_settings(username: str, settings: Dict[str, bool]) -> None:
    """Render notification preferences form."""
    st.subheader("Tuỳ chọn nhận email")
    
    with st.form("notif_form"):
        col1, col2 = st.columns(2)
        with col1:
            check_achieve = st.checkbox("🏆 Thành tựu & Huy hiệu", value=settings.get('achieve', True))
            check_daily = st.checkbox("⏰ Nhắc nhở học tập", value=settings.get('daily', True))
        with col2:
            check_streak = st.checkbox("🔥 Cảnh báo mất chuỗi", value=settings.get('streak', True))
            check_weekly = st.checkbox("📊 Báo cáo tuần", value=settings.get('weekly', True))
        
        if st.form_submit_button("💾 Lưu cài đặt"):
            st.success("Đã lưu cài đặt (Giả lập).")

