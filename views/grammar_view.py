"""View components for Grammar page."""
import streamlit as st
from typing import Dict, Any, List, Tuple, Optional
import time


def render_grammar_guide() -> None:
    """Render learning guide for grammar section."""
    with st.expander("ℹ️ HƯỚNG DẪN HỌC (Quy trình R.E.A.P)", expanded=False):
        st.markdown("""
        1. **📖 Read:** Học lý thuyết & bài giảng AI.
        2. **✅ Examine:** Thi đạt 8/10 điểm để qua bài.
        3. **🔐 Unlock:** Hoàn thành 100% để mở khóa level sau.
        4. **♾️ Apply:** Luyện tập sâu.
        """)


def render_level_selector(
    level_map: Dict[str, str],
    is_unlocked_func,
    is_admin: bool
) -> Tuple[str, str]:
    """Render level selector with progress.
    
    Args:
        level_map: Mapping of display names to level codes
        is_unlocked_func: Function to check if level is unlocked
        is_admin: Whether user is admin
        
    Returns:
        Tuple of (selected_code, selected_label)
    """
    st.subheader("📍 Lộ trình học tập")
    col_lvl, col_prog = st.columns([1, 1])
    
    level_display = []
    level_codes = []
    
    for label, code in level_map.items():
        unlocked = is_unlocked_func(code)
        icon = "🔓" if unlocked or is_admin else "🔒"
        level_display.append(f"{icon} {label}")
        level_codes.append(code)
    
    with col_lvl:
        selected_label = st.selectbox(
            "Chọn Cấp độ:", 
            level_display, 
            label_visibility="collapsed"
        )
        current_idx = level_display.index(selected_label)
        curr_code = level_codes[current_idx]
    
    return curr_code, selected_label


def render_level_progress(curr_code: str, units: Dict, get_prog_func) -> None:
    """Render progress bar for current level.
    
    Args:
        curr_code: Current level code
        units: Dictionary of units for this level
        get_prog_func: Function to get progress (done, total)
    """
    d, t = get_prog_func(curr_code, units)
    st.progress(d/t if t > 0 else 0, text=f"Tiến độ {curr_code}: {d}/{t} bài")


def render_unit_selector(
    units: Dict,
    curr_code: str,
    progress_set: set
) -> Tuple[str, Dict[str, Any]]:
    """Render unit selector dropdown.
    
    Args:
        units: Dictionary of available units
        curr_code: Current level code
        progress_set: Set of completed unit IDs
        
    Returns:
        Tuple of (selected_unit_key, unit_data)
    """
    u_key = st.selectbox(
        "Chọn bài học cụ thể:", 
        list(units.keys()), 
        format_func=lambda k: (
            f"{'✅' if f'{curr_code}_{k}' in progress_set else '⬜'} "
            f"{units[k]['title']}"
        )
    )
    
    return u_key, units[u_key]


def render_unit_header(title: str, description: str) -> None:
    """Render unit header with title and description.
    
    Args:
        title: Unit title
        description: Unit description
    """
    st.markdown(f"""
    <div style="background:#f8f9fa; border-left:5px solid #007BFF; padding:20px; border-radius:8px; margin-bottom:20px;">
        <h3 style="margin:0; color:#003366;">{title}</h3>
        <p style="margin:5px 0 0 0; color:#666;">🎯 Mục tiêu: {description}</p>
    </div>
    """, unsafe_allow_html=True)


def render_theory_tab(
    user_id: int,
    curr_code: str,
    u_key: str,
    u_data: Dict[str, Any],
    cached_lecture: Optional[str],
    is_admin: bool
) -> None:
    """Render theory tab with original content and AI lecture.
    
    Args:
        user_id: Current user ID
        curr_code: Current level code
        u_key: Unit key
        u_data: Unit data
        cached_lecture: Cached lecture content
        is_admin: Whether user is admin
    """
    # Original content
    with st.expander("📚 Xem tóm tắt (Giáo trình gốc)", expanded=False):
        st.markdown(u_data['content'], unsafe_allow_html=True)
        
    st.divider()
    
    # Admin panel
    if is_admin:
        render_admin_panel(user_id, curr_code, u_key, u_data, cached_lecture)
    
    # Display AI lecture
    st.subheader(f"🎓 Bài giảng chi tiết: {u_data['title']}")
    if cached_lecture:
        st.markdown(cached_lecture, unsafe_allow_html=True)
        st.caption("--- Bài giảng được biên soạn bởi AI English Master ---")
    else:
        if not is_admin:
            st.info("🚧 Bài giảng chi tiết đang được cập nhật. Bạn vui lòng xem phần tóm tắt ở trên.")
        else:
            st.info("👋 Admin ơi, bài này chưa có nội dung AI. Hãy bấm nút tạo bên trên nhé!")
    
    # Comments & Votes Section (only if lecture exists)
    if cached_lecture:
        st.divider()
        render_comments_and_votes_section(user_id, curr_code, u_key)


def render_admin_panel(
    user_id: int,
    curr_code: str,
    u_key: str,
    u_data: Dict[str, Any],
    cached_lecture: Optional[str]
) -> None:
    """Render admin panel for grammar content generation.
    
    Args:
        user_id: Admin user ID
        curr_code: Current level code
        u_key: Unit key
        u_data: Unit data
        cached_lecture: Existing cached lecture
    """
    from core.debug_tools import render_debug_panel
    from services.grammar_service import save_theory_cache
    from core.llm import generate_response_with_fallback
    
    st.markdown("### 🛠️ Khu vực Quản trị viên")
    
    # Admin Edit Section (if lecture exists)
    if cached_lecture:
        with st.expander("✏️ Sửa bài giảng trực tiếp", expanded=False):
            edited_content = st.text_area(
                "Nội dung bài giảng (Markdown):",
                value=cached_lecture,
                height=400,
                key=f"admin_edit_{curr_code}_{u_key}"
            )
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("💾 Lưu", type="primary", key=f"admin_save_{curr_code}_{u_key}"):
                    if save_theory_cache(curr_code, u_key, edited_content):
                        st.success("✅ Đã lưu thành công!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Lỗi khi lưu.")
            with col2:
                if st.button("❌ Hủy", key=f"admin_cancel_{curr_code}_{u_key}"):
                    st.rerun()
    
    st.divider()
    
    # AI Generate Section
    btn_txt = "🔄 Tạo lại bài giảng bằng AI (Ghi đè)" if cached_lecture else "✨ Tạo bài giảng AI ngay"
    
    if st.button(btn_txt, type="primary", key=f"admin_generate_{curr_code}_{u_key}"):
        content_len = len(u_data.get('content', ''))
        st.caption(f"📊 Đang gửi {content_len} ký tự dữ liệu gốc cho AI...")
        
        if content_len == 0:
            st.error("Dữ liệu gốc trống, không thể tạo bài giảng.")
            return

        with st.spinner("🤖 AI đang soạn giáo án (có thể mất 10-20s)..."):
            prompt = f"""
            Act as an expert English teacher for Vietnamese students.
            Based on this raw content:
            '''{u_data['content']}'''
            
            Task: Write a comprehensive, engaging lecture in Vietnamese (Markdown format).
            Structure:
            1. 💡 Bản chất (Concept explanation)
            2. 📘 Công thức & Cách dùng (Structures & Usage with examples)
            3. ⚡ Mẹo nhớ nhanh (Mnemonics/Tips)
            4. ⚠️ Lỗi thường gặp (Common mistakes)
            5. 🧩 Ví dụ thực tế (Real-life examples)
            
            Tone: Friendly, encouraging, easy to understand.
            """
            
            new_content = generate_response_with_fallback(prompt, ["ERROR_AI"])
            
            if new_content and new_content != "ERROR_AI":
                if save_theory_cache(curr_code, u_key, new_content):
                    st.success("✅ Đã lưu bài giảng thành công!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Lỗi khi lưu vào cơ sở dữ liệu.")
            else:
                st.error("❌ AI không phản hồi hoặc gặp lỗi.")
                if 'last_gemini_error' in st.session_state:
                    st.error(f"🔍 Debug Info: {st.session_state.last_gemini_error}")


def render_test_tab(
    user_id: int,
    curr_code: str,
    u_key: str,
    u_data: Dict[str, Any],
    unit_full_id: str,
    progress_set: set
) -> None:
    """Render test/exam tab.
    
    Args:
        user_id: Current user ID
        curr_code: Current level code
        u_key: Unit key
        u_data: Unit data
        unit_full_id: Full unit ID (level_unit)
        progress_set: Set of completed units
    """
    from services.grammar_service import generate_grammar_test_questions, save_grammar_progress
    
    # State Init
    if 'test_quiz' not in st.session_state:
        st.session_state.test_quiz = []
    
    # Completion check
    if unit_full_id in progress_set:
        st.success("🎉 Chúc mừng! Bạn đã hoàn thành bài học này.")
    
    # Test logic
    if not st.session_state.test_quiz:
        st.info("Bài thi gồm 10 câu hỏi trắc nghiệm. Đạt 8/10 để qua bài.")
        if st.button("🚀 Bắt đầu làm bài", type="primary"):
            with st.spinner("AI đang tạo đề thi..."):
                raw = generate_grammar_test_questions(curr_code, u_data['title'], 10)
                if raw:
                    st.session_state.test_quiz = [
                        {
                            "q": i["question"],
                            "opts": i["options"],
                            "a": i["answer"],
                            "exp": i.get("explanation", "")
                        }
                        for i in raw
                    ]
                    st.session_state.test_score = None
                    st.rerun()
                else:
                    st.error("⚠️ AI đang bận, vui lòng thử lại sau.")
    else:
        render_test_interface(user_id, unit_full_id, progress_set)


def render_test_interface(user_id: int, unit_full_id: str, progress_set: set) -> None:
    """Render test interface with questions or results.
    
    Args:
        user_id: Current user ID
        unit_full_id: Full unit ID
        progress_set: Set of completed units
    """
    from services.grammar_service import save_grammar_progress
    
    # Cancel button
    if st.button("🗑️ Hủy bài làm lại"):
        st.session_state.test_quiz = []
        st.session_state.test_score = None
        st.rerun()

    # Submit callback
    def submit_quiz():
        score = 0
        for i, q in enumerate(st.session_state.test_quiz):
            if st.session_state.get(f"t_q_{i}") == q['a']:
                score += 1
        st.session_state.test_score = score
        if score >= 8:
            if save_grammar_progress(user_id, unit_full_id):
                progress_set.add(unit_full_id)

    if st.session_state.get('test_score') is None:
        # Show quiz
        with st.form("test_form"):
            for i, q in enumerate(st.session_state.test_quiz):
                st.markdown(f"**Câu {i+1}: {q['q']}**")
                st.radio(
                    "Chọn đáp án:", 
                    q['opts'], 
                    key=f"t_q_{i}", 
                    label_visibility="collapsed", 
                    index=None
                )
                st.markdown("---")
            st.form_submit_button("Nộp bài", on_click=submit_quiz, type="primary")
    else:
        # Show results
        score = st.session_state.test_score
        if score >= 8:
            st.balloons()
            st.success(f"Kết quả: {score}/10. Đạt yêu cầu! 🌟")
        else:
            st.error(f"Kết quả: {score}/10. Chưa đạt, hãy thử lại nhé.")
        
        with st.expander("Xem đáp án & Giải thích", expanded=True):
            for i, q in enumerate(st.session_state.test_quiz):
                st.markdown(f"**{i+1}. {q['q']}**")
                st.info(f"✅ Đáp án: {q['a']} | 💡 {q['exp']}")
        
        if st.button("Làm đề mới"):
            st.session_state.test_quiz = []
            st.session_state.test_score = None
            st.rerun()


def render_comments_and_votes_section(user_id: int, level: str, unit_key: str) -> None:
    """Render comments and votes section for grammar lesson.
    
    Args:
        user_id: Current user ID
        level: Level code (A1, A2, etc.)
        unit_key: Unit key (U1, U2, etc.)
    """
    from services.grammar_service import (
        get_lesson_comments, save_lesson_comment, get_user_comment,
        get_lesson_votes, get_user_vote, save_lesson_vote
    )
    
    st.subheader("💬 Bình luận & Đánh giá")
    
    # Votes Section
    votes = get_lesson_votes(level, unit_key)
    user_vote = get_user_vote(level, unit_key, user_id) if user_id else None
    
    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        like_color = "primary" if user_vote == 'like' else "secondary"
        if st.button(f"👍 Thích ({votes['like']})", key=f"vote_like_{level}_{unit_key}", type=like_color):
            if user_id:
                # Toggle: Nếu đã like thì đổi sang dislike, nếu chưa/dislike thì vote like
                new_vote = 'dislike' if user_vote == 'like' else 'like'
                save_lesson_vote(level, unit_key, user_id, new_vote)
                st.rerun()
            else:
                st.warning("Vui lòng đăng nhập để vote.")
    
    with col2:
        dislike_color = "primary" if user_vote == 'dislike' else "secondary"
        if st.button(f"👎 Không thích ({votes['dislike']})", key=f"vote_dislike_{level}_{unit_key}", type=dislike_color):
            if user_id:
                # Toggle: Nếu đã dislike thì đổi sang like, nếu chưa/like thì vote dislike
                new_vote = 'like' if user_vote == 'dislike' else 'dislike'
                save_lesson_vote(level, unit_key, user_id, new_vote)
                st.rerun()
            else:
                st.warning("Vui lòng đăng nhập để vote.")
    
    st.divider()
    
    # Comments Section
    comments = get_lesson_comments(level, unit_key)
    user_comment = get_user_comment(level, unit_key, user_id) if user_id else None
    
    # Comment Form
    if user_id:
        st.markdown("#### Viết bình luận")
        comment_key = f"comment_input_{level}_{unit_key}"
        new_comment = st.text_area(
            "Bình luận:",
            value=user_comment['comment_text'] if user_comment else "",
            placeholder="Nhập bình luận của bạn...",
            key=comment_key,
            height=100
        )
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("💬 Gửi", type="primary", key=f"submit_comment_{level}_{unit_key}"):
                if new_comment.strip():
                    if save_lesson_comment(level, unit_key, user_id, new_comment):
                        st.success("✅ Đã gửi bình luận!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Lỗi khi gửi bình luận.")
                else:
                    st.warning("Vui lòng nhập nội dung bình luận.")
    else:
        st.info("💡 Đăng nhập để viết bình luận.")
    
    st.divider()
    
    # Display Comments
    st.markdown("#### 📝 Bình luận")
    if comments:
        for comment in comments:
            user_data = comment.get('Users', {})
            user_name = user_data.get('name') or user_data.get('username') or "Ẩn danh"
            comment_text = comment.get('comment_text', '')
            created_at = comment.get('created_at', '')
            
            # Format date
            try:
                if created_at:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                else:
                    date_str = ""
            except:
                date_str = ""
            
            with st.container():
                st.markdown(f"**{user_name}** {f'({date_str})' if date_str else ''}")
                st.markdown(comment_text)
                st.divider()
    else:
        st.info("Chưa có bình luận nào. Hãy là người đầu tiên bình luận!")


def render_drill_tab(curr_code: str, u_data: Dict[str, Any]) -> None:
    """Render drill/practice tab.
    
    Args:
        curr_code: Current level code
        u_data: Unit data
    """
    from core.llm import generate_grammar_test_questions
    
    st.markdown("### 🏋️ Luyện tập sâu (Drill Mode)")
    st.caption("Tạo bài tập vô hạn để ôn luyện kiến thức.")
    
    c_n, c_b = st.columns([1, 2])
    num_q = c_n.number_input("Số câu:", 5, 50, 5, step=5)
    
    if c_b.button("✨ Sinh bài tập mới"):
        with st.spinner("Đang tạo bài tập..."):
            # Use generate_grammar_test_questions which has caching built-in
            questions = generate_grammar_test_questions(curr_code, u_data['title'], num_q)
            if questions and isinstance(questions, list):
                st.session_state.drill_quiz = questions
                st.rerun()
            else:
                st.error("Lỗi tạo bài tập.")
    
    if st.session_state.get('drill_quiz'):
        for i, q in enumerate(st.session_state.drill_quiz):
            st.markdown(f"**{i+1}. {q.get('q', q.get('question'))}**")
            opts = q.get('opts', q.get('options', []))
            ans = q.get('a', q.get('answer'))
            exp = q.get('exp', q.get('explanation', ''))
            
            c = st.radio(
                "Chọn:", 
                opts, 
                key=f"drill_{i}", 
                label_visibility="collapsed", 
                index=None
            )
            if c:
                if c == ans:
                    st.success(f"Đúng! {exp}")
                else:
                    st.warning(f"Sai. Đáp án: {ans}")
            st.markdown("---")

