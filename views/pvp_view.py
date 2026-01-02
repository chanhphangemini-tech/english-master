"""View components for PvP Challenge page."""
import streamlit as st
from typing import Dict, Any, List, Optional


def render_waiting_screen(opponent_name: str, my_score: int) -> None:
    """Render waiting screen when player has finished.
    
    Args:
        opponent_name: Name of the opponent
        my_score: Current player's score
    """
    st.info(f"Bạn đã hoàn thành! Điểm số: {my_score}")
    st.markdown(f"### ⏳ Đang chờ đối thủ **{opponent_name}** hoàn thành...")
    
    if st.button("🔄 Kiểm tra kết quả"):
        st.rerun()


def render_game_interface(
    match_data: Dict[str, Any],
    uid: int,
    is_creator: bool,
    opponent_name: str
) -> None:
    """Render the main game interface.
    
    Args:
        match_data: Match information
        uid: Current user ID
        is_creator: Whether current user is the creator
        opponent_name: Name of the opponent
    """
    from services.game_service import submit_pvp_score
    import time
    
    questions = match_data.get('questions', [])
    if not questions:
        st.error("Lỗi dữ liệu câu hỏi.")
        st.stop()
        
    st.markdown(f"**Đối thủ:** {opponent_name} | **Cược:** {match_data['bet_amount']} 🪙")
    st.progress(0, text="Bắt đầu!")
    
    with st.form("pvp_game_form"):
        score = 0
        user_answers = {}
        
        for i, q in enumerate(questions):
            st.markdown(f"##### Câu {i+1}: {q['question']}")
            user_answers[i] = st.radio(
                f"Chọn đáp án câu {i+1}:", 
                q['options'], 
                key=f"q_{i}", 
                label_visibility="collapsed", 
                index=None
            )
            st.markdown("---")
        
        if st.form_submit_button("Nộp Bài 🚀", type="primary"):
            # Tính điểm
            for i, q in enumerate(questions):
                if user_answers.get(i) == q['answer']:
                    score += 1
            
            # Gửi điểm lên server
            with st.spinner("Đang gửi kết quả..."):
                res = submit_pvp_score(match_data['id'], uid, score, is_creator)
                if res == "Success":
                    st.success(f"Đã nộp! Điểm của bạn: {score}/{len(questions)}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Lỗi: {res}")


def render_room_list(uid: int, challenges: List[Dict[str, Any]]) -> None:
    """Render list of open challenge rooms.
    
    Args:
        uid: Current user ID
        challenges: List of open challenges
    """
    from services.game_service import join_pvp_challenge
    import time
    
    st.subheader("🔥 Các phòng đang chờ")
    if st.button("🔄 Làm mới danh sách"):
        st.rerun()
        
    if not challenges:
        st.info("Hiện không có phòng nào đang mở. Hãy tạo phòng mới!")
    else:
        for room in challenges:
            creator = room.get('Users') or {}
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
                c1.image(
                    creator.get('avatar_url') or "https://cdn-icons-png.flaticon.com/512/197/197374.png", 
                    width=50
                )
                c2.markdown(
                    f"**{creator.get('name', 'Unknown')}**\n\n"
                    f"Chủ đề: {room.get('topic')} ({room.get('level')})"
                )
                c3.markdown(f"💰 Cược: **{room.get('bet_amount')}**")
                if c4.button("Vào Chiến", key=f"join_{room['id']}", type="primary"):
                    res = join_pvp_challenge(room['id'], uid)
                    if res == "Success":
                        st.success("Đã tham gia! Đang vào trận...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {res}")


def render_create_room_form(uid: int) -> None:
    """Render form to create new PvP challenge.
    
    Args:
        uid: Current user ID
    """
    from services.game_service import create_pvp_challenge
    
    st.subheader("🛠️ Thiết lập trận đấu")
    
    with st.form("create_pvp_form"):
        c1, c2 = st.columns(2)
        topic = c1.selectbox("Chủ đề", ["General", "Travel", "Business", "Technology"])
        level = c2.selectbox("Cấp độ", ["A1", "A2", "B1", "B2"])
        
        bet = st.slider("Mức cược (Coin)", 0, 100, 10, 10)
        
        if st.form_submit_button("Tạo Phòng", type="primary"):
            # Tạo câu hỏi giả lập (Sau này sẽ dùng AI hoặc lấy từ DB)
            dummy_questions = [
                {
                    "question": "What is the synonym of 'Happy'?",
                    "options": ["Sad", "Joyful", "Angry", "Tired"],
                    "answer": "Joyful"
                },
                {
                    "question": "Choose the correct verb: He ___ to school.",
                    "options": ["go", "goes", "going", "gone"],
                    "answer": "goes"
                },
                {
                    "question": "Antonym of 'Big'?",
                    "options": ["Huge", "Large", "Small", "Giant"],
                    "answer": "Small"
                }
            ]
            
            data, msg = create_pvp_challenge(uid, level, topic, bet, dummy_questions)
            
            if data:
                st.success("Tạo phòng thành công! Đang chờ đối thủ...")
                st.info(f"Mã phòng: {data}")
            else:
                st.error(f"Lỗi: {msg}")

