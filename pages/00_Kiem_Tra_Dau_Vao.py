import streamlit as st
import time
from core.theme_applier import apply_page_theme
from core.llm import generate_response_with_fallback, parse_json_response, evaluate_placement_test
from core.tts import get_tts_audio
from core.stt import recognize_audio
from services.vocab_service import bulk_master_levels
from core.data import supabase, get_user_stats

# --- CONFIG ---
st.set_page_config(page_title="Kiểm Tra Đầu Vào", page_icon="🎯", layout="wide")

# --- AUTH CHECK ---
if not st.session_state.get("logged_in"):
    st.switch_page("Home.py")

apply_page_theme()  # Apply theme + sidebar + auth

# --- STATE MANAGEMENT ---
if 'pt_step' not in st.session_state: st.session_state.pt_step = 0 # 0: Intro, 1: Lis, 2: Read, 3: Write, 4: Speak, 5: Result, 6: Done
if 'pt_data' not in st.session_state: st.session_state.pt_data = {}
if 'pt_answers' not in st.session_state: st.session_state.pt_answers = {"lis": 0, "read": 0, "write": "", "speak": ""}

user_id = st.session_state.user_info.get("id")
user_plan = st.session_state.user_info.get("plan", "free")
user_role = st.session_state.user_info.get("role", "user")
is_premium = user_plan == 'premium' or user_role == 'admin'

st.title("🎯 Kiểm Tra Trình Độ Đầu Vào (Placement Test)")

# --- STEP 0: INTRO ---
if st.session_state.pt_step == 0:
    # Reset state khi bắt đầu lại
    st.session_state.pt_data = {}
    st.session_state.pt_answers = {"lis": 0, "read": 0, "write": "", "speak": ""}
    if 'pt_result' in st.session_state:
        del st.session_state.pt_result
    if 'pt_audio' in st.session_state:
        del st.session_state.pt_audio

    # Check if user has taken the test before
    stats = get_user_stats(user_id)
    has_taken_test = stats.get('latest_test_score') is not None

    if has_taken_test and not is_premium:
        st.warning("🔒 Bạn đã hoàn thành bài kiểm tra đầu vào.")
        st.info("Nâng cấp lên Premium để có thể làm lại bài kiểm tra và theo dõi tiến độ chi tiết.")
        if st.button("⭐ Xem gói Premium", type="primary"):
            st.switch_page("pages/15_Premium.py")
        st.stop()

    st.markdown("""
    ### Chào mừng bạn đến với bài kiểm tra năng lực toàn diện!
    
    AI sẽ đánh giá cả **4 kỹ năng** của bạn để xác định trình độ CEFR (A1 - C2).
    
    **Quyền lợi khi hoàn thành:**
    *   ✅ Xác định chính xác trình độ hiện tại.
    *   ✅ **Tự động mở khóa** và đánh dấu "Đã học" toàn bộ từ vựng ở các cấp độ thấp hơn.
    *   ✅ Nhận lộ trình học tập cá nhân hóa.
    
    **Cấu trúc bài thi (khoảng 10-15 phút):**
    1.  🎧 **Nghe:** 5 câu trắc nghiệm.
    2.  📖 **Đọc:** 5 câu trắc nghiệm.
    3.  ✍️ **Viết:** Viết một đoạn văn ngắn.
    4.  🗣️ **Nói:** Trả lời một câu hỏi bằng giọng nói.
    """)
    
    if st.button("🚀 Bắt đầu ngay", type="primary"):
        # Generate Test Data on Start
        with st.spinner("AI đang thiết kế đề thi phù hợp..."):
            # Prompt tạo đề tổng hợp
            # Đã điều chỉnh để đề thi dễ hơn (A1-A2)
            prompt = """
            Create a Placement Test content.
            1. Listening Script: A very simple conversation (80-100 words) about daily life (Level A1-A2).
            2. Listening Questions: 5 MCQs based on script.
            3. Reading Passage: A simple article about "My Family" (100-150 words, Level A1-A2).
            4. Reading Questions: 5 MCQs.
            5. Writing Topic: A simple question (e.g., "What is your favorite food?").
            6. Speaking Topic: A simple personal question (e.g., "What do you do in your free time?").
            
            Return JSON:
            {
                "lis_script": "...",
                "lis_qs": [{"q": "...", "opts": ["A", "B", "C", "D"], "a": "Correct Option"}],
                "read_passage": "...",
                "read_qs": [{"q": "...", "opts": ["A", "B", "C", "D"], "a": "Correct Option"}],
                "write_topic": "...",
                "speak_topic": "..."
            }
            """
            res = generate_response_with_fallback(prompt, ["ERROR"])
            data = parse_json_response(res)
            
            if data and "lis_script" in data:
                st.session_state.pt_data = data
                st.session_state.pt_step = 1
                st.rerun()
            else:
                st.error("Lỗi khởi tạo đề thi. Vui lòng thử lại.")

# --- STEP 1: LISTENING ---
elif st.session_state.pt_step == 1:
    st.subheader("Phần 1: Kỹ năng Nghe (Listening)")
    st.progress(20, text="Listening")
    
    data = st.session_state.pt_data
    
    # Audio
    if 'pt_audio' not in st.session_state:
        with st.spinner("Đang tải âm thanh..."):
            st.session_state.pt_audio = get_tts_audio(data['lis_script'])
            
    st.audio(st.session_state.pt_audio, format='audio/mp3')
    st.info("Hãy nghe đoạn hội thoại và trả lời câu hỏi bên dưới.")
    
    with st.form("pt_lis_form"):
        score = 0
        user_choices = {}
        for i, q in enumerate(data['lis_qs']):
            st.markdown(f"**{i+1}. {q['q']}**")
            user_choices[i] = st.radio(f"Lựa chọn {i+1}", q['opts'], key=f"l_{i}", label_visibility="collapsed")
            st.markdown("---")
            
        if st.form_submit_button("Tiếp tục ➡️", type="primary"):
            # Grade immediately
            for i, q in enumerate(data['lis_qs']):
                if user_choices.get(i) == q['a']:
                    score += 1
            st.session_state.pt_answers['lis'] = score
            st.session_state.pt_step = 2
            st.rerun()

# --- STEP 2: READING ---
elif st.session_state.pt_step == 2:
    st.subheader("Phần 2: Kỹ năng Đọc (Reading)")
    st.progress(40, text="Reading")
    
    data = st.session_state.pt_data
    st.markdown(f"""<div style="padding:15px; background:#f8f9fa; border-radius:8px; border:1px solid #ddd; margin-bottom:20px;">
    {data['read_passage']}
    </div>""", unsafe_allow_html=True)
    
    with st.form("pt_read_form"):
        score = 0
        user_choices = {}
        for i, q in enumerate(data['read_qs']):
            st.markdown(f"**{i+1}. {q['q']}**")
            user_choices[i] = st.radio(f"Lựa chọn {i+1}", q['opts'], key=f"r_{i}", label_visibility="collapsed")
            st.markdown("---")
            
        if st.form_submit_button("Tiếp tục ➡️", type="primary"):
            for i, q in enumerate(data['read_qs']):
                if user_choices.get(i) == q['a']:
                    score += 1
            st.session_state.pt_answers['read'] = score
            st.session_state.pt_step = 3
            st.rerun()

# --- STEP 3: WRITING ---
elif st.session_state.pt_step == 3:
    st.subheader("Phần 3: Kỹ năng Viết (Writing)")
    st.progress(60, text="Writing")
    
    topic = st.session_state.pt_data['write_topic']
    st.info(f"📝 **Topic:** {topic}")
    
    user_text = st.text_area("Viết câu trả lời của bạn (50-100 từ):", height=200)
    
    if st.button("Tiếp tục ➡️", type="primary"):
        if len(user_text.split()) < 10:
            st.warning("Bài viết quá ngắn. Hãy viết thêm.")
        else:
            st.session_state.pt_answers['write'] = user_text
            st.session_state.pt_step = 4
            st.rerun()

# --- STEP 4: SPEAKING ---
elif st.session_state.pt_step == 4:
    st.subheader("Phần 4: Kỹ năng Nói (Speaking)")
    st.progress(80, text="Speaking")
    
    topic = st.session_state.pt_data['speak_topic']
    st.info(f"🗣️ **Question:** {topic}")
    
    audio_val = st.audio_input("Ghi âm câu trả lời:", key="pt_rec")
    
    if audio_val:
        if st.button("Nộp bài & Chấm điểm 🏁", type="primary"):
            with st.spinner("Đang xử lý âm thanh..."):
                ok, text = recognize_audio(audio_val.read())
                if ok:
                    st.session_state.pt_answers['speak'] = text
                    st.session_state.pt_step = 5
                    st.rerun()
                else:
                    st.error("Không nghe rõ. Vui lòng ghi âm lại.")

# --- STEP 5: RESULT & PROCESSING ---
elif st.session_state.pt_step == 5:
    st.subheader("📊 Kết quả đánh giá năng lực")
    st.progress(100, text="Đang phân tích...")
    
    if 'pt_result' not in st.session_state:
        with st.spinner("AI đang chấm điểm toàn diện (có thể mất 30s)..."):
            # 1. Gọi AI đánh giá
            inputs = {
                "listening_score": st.session_state.pt_answers['lis'],
                "reading_score": st.session_state.pt_answers['read'],
                "writing_text": st.session_state.pt_answers['write'],
                "speaking_text": st.session_state.pt_answers['speak']
            }
            result = evaluate_placement_test(inputs)
            st.session_state.pt_result = result
            
    # Hiển thị kết quả
    res = st.session_state.pt_result
    if res:
        lvl = res.get('overall_level', 'A1')
        st.balloons()
        
        st.markdown(f"""
        <div style="text-align:center; padding:30px; background:#e3f2fd; border-radius:15px; border:2px solid #2196f3;">
            <h2 style="color:#0d47a1; margin:0;">TRÌNH ĐỘ CỦA BẠN: {lvl}</h2>
            <p>Hệ thống đã tự động cập nhật lộ trình học tập phù hợp.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Xem chi tiết đánh giá", expanded=True):
            st.markdown(f"#### 💡 Lời khuyên")
            st.write(res.get('recommendation', "Không có lời khuyên."))
            st.markdown(f"#### 💪 Điểm mạnh")
            st.write(res.get('strengths', "Chưa xác định."))
            st.markdown(f"#### 📉 Điểm yếu")
            st.write(res.get('weaknesses', "Chưa xác định."))
            
        st.divider()
        
        # --- ACTION OPTIONS ---
        st.markdown("### 🚀 Lựa chọn lộ trình của bạn")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Bắt đầu học ở cấp độ này", help="Hệ thống sẽ tự động đánh dấu hoàn thành các từ vựng ở cấp độ thấp hơn."):
                with st.spinner("Đang cập nhật lộ trình..."):
                    level = res.get('overall_level', 'A1')
                    # 1. Bỏ qua các level thấp hơn
                    bulk_master_levels(user_id, level)
                    # 2. Lưu kết quả thi
                    try:
                        score_map = {"A1": 2, "A2": 4, "B1": 6, "B2": 8, "C1": 9, "C2": 10}
                        supabase.table("MockTestResults").insert({
                            "user_id": int(user_id),
                            "level": level,
                            "score": score_map.get(level, 0),
                            "completed_at": time.strftime('%Y-%m-%dT%H:%M:%S%z')
                        }).execute()
                        # 3. Cập nhật level cho user
                        supabase.table("Users").update({
                            "current_level": level
                        }).execute()
                    except: pass
                    st.session_state.pt_step = 6 # Chuyển sang trang hoàn tất
                    st.rerun()

        with col2:
            if st.button("Học lại từ đầu", help="Học toàn bộ từ vựng từ cấp độ thấp nhất để xây dựng nền tảng vững chắc."):
                 st.session_state.pt_step = 6 # Chuyển sang trang hoàn tất
                 st.rerun()

        if st.button("Làm lại bài kiểm tra", type="secondary"):
            st.session_state.pt_step = 0
            st.rerun()
            
    else:
        st.error("Lỗi hiển thị kết quả.")

# --- STEP 6: DONE ---
elif st.session_state.pt_step == 6:
    st.success("🎉 **Lộ trình học tập của bạn đã được cập nhật!**")
    st.markdown("""
    Bạn có thể bắt đầu học ngay bây giờ.
    - Vào **Học & Ôn tập (SRS)** để học từ vựng mới theo lộ trình.
    - Khám phá các phòng luyện kỹ năng để áp dụng kiến thức.
    """)
    if st.button("Về trang chủ", type="primary"):
        st.switch_page("Home.py")
