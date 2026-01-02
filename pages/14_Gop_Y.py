import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

from core.theme_applier import apply_page_theme

# Apply theme (includes global theme + sidebar + auth)
apply_page_theme()

from core.data import supabase

st.title("📩 Góp ý & Báo lỗi")

PAGE_ID = "feedback_page"
st.session_state.active_page = PAGE_ID

# Helper functions
def save_feedback_to_db(username, fb_type, fb_module, content):
    """Lưu feedback vào database"""
    try:
        user_id = st.session_state.user_info.get('id')
        if not supabase or not user_id:
            return False
        
        # Map Vietnamese type to English
        type_map = {
            "🐞 Báo lỗi": "bug",
            "💡 Đề xuất tính năng": "feature",
            "❤️ Lời khen": "compliment",
            "Khác": "other"
        }
        
        fb_type_en = type_map.get(fb_type, "other")
        
        result = supabase.table("feedback").insert({
            "user_id": user_id,
            "username": username,
            "type": fb_type_en,
            "module": fb_module,
            "content": content,
            "status": "New",
            "created_at": get_vn_now_utc()
        }).execute()
        
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Lỗi lưu feedback: {e}")
        return False

def get_all_feedback():
    """Lấy tất cả feedback (admin only)"""
    try:
        if not supabase:
            return pd.DataFrame()
        
        result = supabase.table("feedback").select("*").order("created_at", desc=True).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            # Map English types back to Vietnamese for display
            type_display_map = {
                "bug": "🐞 Báo lỗi",
                "feature": "💡 Đề xuất tính năng",
                "compliment": "❤️ Lời khen",
                "other": "Khác"
            }
            if 'type' in df.columns:
                df['type'] = df['type'].map(type_display_map).fillna(df['type'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi lấy dữ liệu: {e}")
        return pd.DataFrame()

def update_feedback_status(feedback_id, new_status):
    """Cập nhật trạng thái feedback"""
    try:
        if not supabase:
            return False
        
        # Only update status, trigger will handle updated_at automatically
        result = supabase.table("feedback").update({
            "status": new_status
        }).eq("id", feedback_id).execute()
        
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Lỗi cập nhật: {e}")
        return False

def render_admin_view():
    """Hiển thị giao diện admin để quản lý feedback"""
    st.info("👋 Chào Admin! Đây là trang quản lý Feedback.")
    
    df_fb = get_all_feedback()

    if df_fb.empty:
        st.warning("Chưa có góp ý nào.")
    else:
        available_statuses = df_fb['status'].unique()
        default_statuses = [status for status in ["New", "Processing"] if status in available_statuses]
        
        col1, col2 = st.columns([3, 1])
        with col1:
            filter_status = st.multiselect(
                "Lọc trạng thái:", 
                options=available_statuses, 
                default=default_statuses
            )
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        df_show = df_fb[df_fb['status'].isin(filter_status)] if filter_status else df_fb
        
        # Format timestamp
        if 'created_at' in df_show.columns:
            df_show = df_show.copy()
            try:
                df_show['created_at'] = pd.to_datetime(df_show['created_at']).dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        
        st.dataframe(df_show, height=400, width='stretch')
        
        st.divider()
        st.subheader("🛠️ Cập nhật trạng thái")
        
        if not df_show.empty:
            c1, c2, c3 = st.columns([2, 1, 1])
            
            # Create options map for selectbox
            options_map = {
                f"ID {row['id']}: [{row['type']}] {row['content'][:40]}...": row['id'] 
                for _, row in df_show.iterrows()
            }

            with c1:
                selected_display_string = st.selectbox(
                    "Chọn vấn đề để xử lý:", 
                    options=list(options_map.keys())
                )
            with c2:
                new_stat = st.selectbox("Đổi trạng thái:", ["New", "Processing", "Done"])
            with c3:
                st.write("")
                st.write("")
                if st.button("✅ Cập nhật", type="primary"):
                    selected_id = options_map[selected_display_string]
                    if update_feedback_status(selected_id, new_stat):
                        st.success("✅ Đã cập nhật trạng thái!")
                        st.rerun()
                    else:
                        st.error("❌ Lỗi cập nhật.")

def render_user_view():
    """Hiển thị giao diện user để gửi feedback"""
    st.subheader("🗣️ Chúng tôi lắng nghe bạn")
    st.write("Mọi ý kiến đóng góp của bạn đều giúp ứng dụng tốt hơn mỗi ngày!")
    
    # User's feedback history
    with st.expander("📋 Lịch sử góp ý của tôi", expanded=False):
        try:
            user_id = st.session_state.user_info.get('id')
            if supabase and user_id:
                user_feedback = supabase.table("feedback").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
                if user_feedback.data:
                    df_user = pd.DataFrame(user_feedback.data)
                    # Format timestamp
                    if 'created_at' in df_user.columns:
                        df_user['created_at'] = pd.to_datetime(df_user['created_at']).dt.strftime("%Y-%m-%d %H:%M")
                    
                    # Map types
                    type_display_map = {
                        "bug": "🐞 Báo lỗi",
                        "feature": "💡 Đề xuất tính năng",
                        "compliment": "❤️ Lời khen",
                        "other": "Khác"
                    }
                    if 'type' in df_user.columns:
                        df_user['type'] = df_user['type'].map(type_display_map).fillna(df_user['type'])
                    
                    st.dataframe(df_user, width='stretch')
                else:
                    st.info("Bạn chưa gửi góp ý nào.")
        except Exception as e:
            st.warning(f"Không thể tải lịch sử: {e}")
    
    st.divider()
    
    # Feedback form
    with st.form("feedback_form", border=True):
        st.markdown("#### ✍️ Gửi góp ý mới")
        
        c1, c2 = st.columns(2)
        with c1:
            fb_type = st.selectbox(
                "Loại góp ý:", 
                ["🐞 Báo lỗi", "💡 Đề xuất tính năng", "❤️ Lời khen", "Khác"],
                help="Chọn loại góp ý phù hợp nhất"
            )
        with c2:
            fb_mod = st.selectbox(
                "Module liên quan:", 
                ["Học Từ Vựng", "Kho Từ Vựng", "Luyện Nghe", "Luyện Nói", "Luyện Viết", "Luyện Đọc", "Luyện Dịch", "Ngữ Pháp", "Thi Thử", "Đấu Trường", "Chung"],
                help="Chọn module/trang bạn muốn góp ý"
            )
        
        content = st.text_area(
            "Nội dung chi tiết:", 
            height=150, 
            placeholder="Mô tả chi tiết lỗi hoặc tính năng bạn mong muốn...\n\nVí dụ:\n- Mô tả lỗi: Khi click vào nút X, trang bị crash\n- Đề xuất: Tôi muốn có tính năng Y để làm Z",
            help="Càng chi tiết càng tốt, sẽ giúp chúng tôi cải thiện nhanh hơn!"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit_btn = st.form_submit_button("🚀 Gửi Góp Ý", type="primary")
        
        if submit_btn:
            if not content or len(content.strip()) < 10:
                st.warning("⚠️ Vui lòng nhập nội dung chi tiết (ít nhất 10 ký tự).")
            else:
                curr_user = st.session_state.user_info.get('username', 'unknown')
                with st.spinner("⏳ Đang gửi..."):
                    if save_feedback_to_db(curr_user, fb_type, fb_mod, content):
                        st.success("✅ Cảm ơn bạn! Chúng tôi đã nhận được thông tin và sẽ xem xét sớm nhất có thể.")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Lỗi kết nối. Vui lòng thử lại sau.")

# Main logic
curr_role = st.session_state.user_info.get('role', 'user')

if curr_role == 'admin':
    render_admin_view()
else:
    render_user_view()
