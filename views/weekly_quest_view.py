"""
Weekly Quest View
Hiển thị và quản lý weekly quests
"""
import streamlit as st
from services.quest_service import (
    generate_weekly_quests, 
    complete_weekly_quest, 
    has_received_weekly_quest_reward
)

def render_weekly_quests(user_id):
    """Hiển thị nhiệm vụ hàng tuần và tự động thưởng coin khi complete"""
    st.markdown("### 📅 Nhiệm Vụ Hàng Tuần")
    st.caption("Nhiệm vụ lớn hơn với phần thưởng cao hơn, reset mỗi thứ 2")
    
    # Generate weekly quests
    quests = generate_weekly_quests(user_id)
    
    if not quests:
        st.info("Đang tải nhiệm vụ tuần...")
        return
    
    # Hiển thị nhiệm vụ
    for q in quests:
        is_done = q['current'] >= q['target']
        icon = "✅" if is_done else "⬜"
        reward_received = has_received_weekly_quest_reward(user_id, q['id']) if is_done else False
        reward_text = " (Đã nhận 🎉)" if reward_received else ""
        
        st.markdown(f"{icon} {q['desc']} ({q['current']}/{q['target']}) - **Thưởng: {q['reward']} 🪙**{reward_text}")
        
        # Tự động thưởng coin nếu quest complete và chưa nhận reward
        if is_done and not reward_received:
            if complete_weekly_quest(user_id, q['id'], q['reward']):
                st.toast(f"💰 Nhận thưởng lớn: {q['reward']} coins từ quest '{q['desc']}'!", icon="💰")
                st.rerun()
