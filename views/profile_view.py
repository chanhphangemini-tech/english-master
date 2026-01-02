"""View components for Profile page."""
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from services.title_service import get_title_display_name
from services.frame_service import get_frame_style, get_frame_border_style

logger = logging.getLogger(__name__)


def render_profile_header(user: Dict[str, Any]) -> None:
    """Render profile header with avatar and basic info."""
    join_date_display = "Đang cập nhật..."
    created_at_str = user.get('created_at')
    
    if created_at_str:
        try:
            join_date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            join_date_display = join_date.strftime('%d-%m-%Y')
        except:
            join_date_display = created_at_str[:10]
    
    # Get active avatar frame and title
    active_frame = user.get('active_avatar_frame')
    active_title = user.get('active_title')
    
    # Get frame style from frame_service
    frame_container_style, frame_extra_css, frame_class = get_frame_style(active_frame)
    frame_border_style = get_frame_border_style(active_frame)
    
    # Format title with Vietnamese name
    title_display = get_title_display_name(active_title) if active_title else None
    title_badge = f'<span style="font-size: 0.5em; background: linear-gradient(135deg, #ff7675 0%, #fd79a8 50%, #fdcb6e 100%); padding: 6px 12px; border-radius: 10px; margin-left: 8px; color: white; font-weight: bold; box-shadow: 0 2px 4px rgba(255, 118, 117, 0.3);">{title_display}</span>' if title_display else ''
    
    # Add frame extra CSS if any (replace & with proper selector)
    frame_css_content = ""
    if frame_extra_css:
        if frame_class:
            # Replace & with .profile-avatar-frame.frame-XXX
            frame_css_content = frame_extra_css.replace('&', f'.profile-avatar-frame.{frame_class}')
        else:
            frame_css_content = frame_extra_css
    
    # Combine all CSS into a single style tag
    combined_css = f"""<style>
        {frame_css_content}
        .profile-avatar-frame {{
            width: 140px;
            height: 140px;
            border-radius: 50%;
            padding: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            position: relative;
            box-sizing: border-box;
            overflow: hidden;
        }}
        .profile-avatar-frame img {{
            width: 100% !important;
            height: 100% !important;
            object-fit: cover;
            border-radius: 50%;
        }}
    </style>"""
    
    st.markdown(combined_css, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #003366 0%, #0056b3 100%); padding: 30px; border-radius: 15px; color: white; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
            <div class="profile-avatar-frame {frame_class}" style="{frame_container_style}">
                <img src="{user.get('avatar_url') or 'https://cdn-icons-png.flaticon.com/512/197/197374.png'}" style="{frame_border_style}" alt="Avatar">
            </div>
            <div>
                <h1 style="color: white; margin: 0; font-size: 32px; display: flex; align-items: center; flex-wrap: wrap;">
                    {user.get('name', 'Learner')} 
                    <span style="font-size: 0.6em; background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 8px; margin-left: 8px;">LVL {user.get('current_level', 'A1')}</span>
                    {title_badge}
                </h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">@{user.get('username')} | 📧 {user.get('email', 'N/A')}</p>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">📅 Tham gia: {join_date_display}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats_overview(stats: Dict[str, Any]) -> None:
    """Render statistics overview cards."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🔥 Streak", f"{stats.get('streak', 0)} ngày", "Giữ vững phong độ!")
    with c2:
        st.metric("📚 Từ vựng", f"{stats.get('words_learned', 0)}", f"+{stats.get('words_today', 0)} hôm nay")
    with c3:
        st.metric("🪙 Coin", f"{stats.get('coins', 0)}", "Dùng trong Shop")
    with c4:
        st.metric("🏆 Điểm thi", stats.get('latest_test_score', 'N/A'), "Bài gần nhất")


def render_achievement_card(achievement: Dict[str, Any], current_val: int) -> None:
    """Render single achievement card."""
    is_unlocked = current_val >= achievement['target']
    progress = min(1.0, current_val / achievement['target']) if achievement['target'] > 0 else 0
    
    with st.container(border=True):
        # Icon & Title
        if is_unlocked:
            st.markdown(f"<div style='text-align:center; font-size: 32px; margin-bottom: 5px;'>{achievement['icon']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center; font-weight: bold; color: #003366; font-size: 14px; height: 35px; display: flex; align-items: center; justify-content: center;'>{achievement['name']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:center; font-size: 32px; margin-bottom: 5px; opacity: 0.5; filter: grayscale(100%);'>{achievement['icon']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center; font-weight: bold; color: gray; font-size: 14px; height: 35px; display: flex; align-items: center; justify-content: center;'>{achievement['name']}</div>", unsafe_allow_html=True)
        
        # Description
        st.markdown(f"<div style='text-align:center; font-size: 11px; color: #666; height: 30px; overflow: hidden; margin-bottom: 5px;'>{achievement['desc']}</div>", unsafe_allow_html=True)
        
        # Progress Bar
        st.progress(progress, text=f"{int(progress*100)}% ({current_val}/{achievement['target']})")
        
        # Footer: Status & Reward
        c_stat, c_rew = st.columns([1, 1])
        with c_stat:
            if is_unlocked: 
                st.markdown("✅ **Đã đạt**")
            else: 
                st.caption(f"🔒 {current_val}/{achievement['target']}")
        with c_rew:
            st.markdown(f"<div style='text-align:right; color: #d63031; font-weight: bold; font-size: 12px;'>+{achievement['reward']} 🪙</div>", unsafe_allow_html=True)


def render_vocab_progress_chart(vocab_data: pd.DataFrame) -> None:
    """Render vocabulary learning progress chart."""
    if vocab_data.empty:
        st.info("Chưa có dữ liệu học tập tuần qua.")
        return
    
    chart = alt.Chart(vocab_data).mark_bar().encode(
        x=alt.X('date', title='Ngày'),
        y=alt.Y('words', title='Số từ đã học'),
        color=alt.value("#003366"),
        tooltip=['date', 'words']
    ).properties(height=300)
    
    st.altair_chart(chart, width='stretch')
    
    # Stats
    total_week = vocab_data['words'].sum()
    avg_daily = round(total_week / 7, 1)
    best_day = vocab_data.loc[vocab_data['words'].idxmax()] if not vocab_data.empty else None
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng tuần", total_week, "từ")
    col2.metric("Trung bình", avg_daily, "từ/ngày")
    if best_day is not None:
        col3.metric("Ngày tốt nhất", best_day['words'], best_day['date'])


def render_test_history_chart(test_data: pd.DataFrame) -> None:
    """Render test history line chart."""
    if test_data.empty:
        st.info("Bạn chưa làm bài thi thử nào.")
        if st.button("Làm bài thi ngay"):
            st.switch_page("pages/08_Thi_Thu.py")
        return
    
    st.markdown("#### Biểu đồ tiến bộ")
    chart = alt.Chart(test_data).mark_line(
        point=alt.OverlayMarkDef(color="#003366", filled=True, size=60)
    ).encode(
        x=alt.X('completed_at:T', title='Ngày thi', axis=alt.Axis(format='%d/%m')),
        y=alt.Y('score:Q', title='Điểm (trên 10)', scale=alt.Scale(domain=[0, 10])),
        color=alt.Color('level:N', title='Cấp độ', legend=alt.Legend(orient="top")),
        tooltip=[
            alt.Tooltip('completed_at:T', title='Ngày thi', format='%d/%m/%Y'),
            alt.Tooltip('score:Q', title='Điểm'),
            alt.Tooltip('level:N', title='Cấp độ')
        ]
    ).properties(title='Điểm thi thử qua các lần').interactive()
    
    st.altair_chart(chart, width='stretch')
    st.divider()

    # List
    st.markdown("#### Chi tiết các lần thi")
    for index, test in test_data.iloc[::-1].iterrows():
        date_str = test['completed_at'].strftime("%d/%m/%Y %H:%M")
        score = test['score']
        
        color = "green" if score >= 8 else "orange" if score >= 6 else "red"
        status = "🎉 Xuất sắc" if score >= 8 else "👍 Tốt" if score >= 6 else "💪 Cần cố gắng"
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 2])
            c1.write(f"**{test['level']}**")
            c2.caption(f"📅 {date_str}")
            c3.markdown(f"<b style='color:{color}'>{score}/10</b>", unsafe_allow_html=True)
            c4.caption(status)

