"""
Progress Analytics Dashboard - Premium Feature
Hiển thị analytics chi tiết về tiến độ học tập
"""
import streamlit as st
from core.theme_applier import apply_page_theme

apply_page_theme()  # Apply theme + sidebar + auth

# --- Auth Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("🔒 Vui lòng đăng nhập để truy cập.")
    st.switch_page("home.py")
    st.stop()

# Check Premium status
user_info = st.session_state.get('user_info', {})
user_plan = user_info.get('plan', 'free')
user_role = str(user_info.get('role', 'user')).lower()

# Premium feature - only for Premium users or Admin
if user_plan != 'premium' and user_role != 'admin':
    st.error("📊 Analytics Dashboard là tính năng Premium!")
    st.info("💡 Nâng cấp lên Premium để xem analytics chi tiết về tiến độ học tập của bạn.")
    
    if st.button("⭐ Xem gói Premium", type="primary"):
        st.switch_page("pages/15_Premium.py")
    st.stop()

user_id = user_info.get('id')
if not user_id:
    st.error("Không tìm thấy user ID!")
    st.stop()

# --- Imports ---
from services.analytics_service import (
    get_user_progress_analytics,
    export_analytics_to_csv,
    export_analytics_to_pdf
)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Title ---
st.title("📊 Progress Analytics Dashboard")
st.caption("Phân tích chi tiết về tiến độ học tập của bạn")

# --- Date Range Selector ---
col_date1, col_date2, col_date3 = st.columns([1, 1, 2])
with col_date1:
    days_option = st.selectbox(
        "Khoảng thời gian",
        options=[7, 30, 90, 365],
        index=1,  # Default to 30 days
        format_func=lambda x: f"{x} ngày" if x < 365 else "1 năm"
    )

# Load analytics data
with st.spinner("Đang tải dữ liệu analytics..."):
    analytics = get_user_progress_analytics(user_id, days=days_option)

if not analytics:
    st.warning("Không thể tải dữ liệu analytics. Vui lòng thử lại sau.")
    st.stop()

# --- Overview Cards ---
st.markdown("### 📈 Tổng Quan")
overview = analytics.get('overview', {})
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Tổng từ đã học", f"{overview.get('total_words', 0):,}")
with col2:
    st.metric("Streak hiện tại", f"{overview.get('current_streak', 0)} ngày")
with col3:
    st.metric("Ngày học tập", f"{overview.get('days_active', 0)}/{days_option} ngày")
with col4:
    avg_time = overview.get('avg_study_time_minutes', 0)
    st.metric("Thời gian học TB", f"{avg_time} phút/ngày")

st.divider()

# --- Vocabulary Progress Timeline ---
st.markdown("### 📚 Tiến Độ Từ Vựng")
vocab_timeline = analytics.get('vocabulary_progress', [])
if vocab_timeline:
    # Create DataFrame for plotting
    df_vocab = pd.DataFrame(vocab_timeline)
    df_vocab['date'] = pd.to_datetime(df_vocab['date'])
    
    # Line chart
    fig_vocab = px.line(
        df_vocab,
        x='date',
        y='count',
        title='Số từ học theo thời gian',
        labels={'date': 'Ngày', 'count': 'Số từ'},
        markers=True
    )
    fig_vocab.update_layout(
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_vocab, width='stretch')
else:
    st.info("Chưa có dữ liệu từ vựng trong khoảng thời gian này.")

# --- Skills Progress (Radar Chart) ---
st.markdown("### 🎯 Tiến Độ Kỹ Năng")
skills_data = analytics.get('skills_progress', {})
if skills_data:
    skills_list = ['listening', 'speaking', 'reading', 'writing']
    skills_labels = ['Listening', 'Speaking', 'Reading', 'Writing']
    
    # Extract exercise counts for radar chart
    values = []
    for skill in skills_list:
        skill_info = skills_data.get(skill, {})
        exercises = skill_info.get('exercises_completed', 0)
        values.append(exercises)
    
    # Create radar chart
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values,
        theta=skills_labels,
        fill='toself',
        name='Exercises Completed'
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max(values) * 1.2, 100)]  # Auto-scale with padding
            )),
        showlegend=False,
        title="Progress by Skill",
        height=400
    )
    st.plotly_chart(fig_radar, width='stretch')
    
    # Skills table
    skills_df_data = []
    for skill in skills_list:
        skill_info = skills_data.get(skill, {})
        skills_df_data.append({
            "Kỹ năng": skills_labels[skills_list.index(skill)],
            "Bài tập đã làm": skill_info.get('exercises_completed', 0),
            "Độ chính xác": f"{skill_info.get('accuracy', 0)}%",
            "Cấp độ": skill_info.get('level', 'A1')
        })
    skills_df = pd.DataFrame(skills_df_data)
    st.dataframe(skills_df, hide_index=True, width='stretch')
else:
    st.info("Chưa có dữ liệu kỹ năng.")

st.divider()

# --- Activity Heatmap ---
st.markdown("### 🔥 Lịch Hoạt Động")
activity_heatmap = analytics.get('activity_heatmap', [])
if activity_heatmap:
    # Create DataFrame
    df_activity = pd.DataFrame(activity_heatmap)
    df_activity['date'] = pd.to_datetime(df_activity['date'])
    
    # Create calendar heatmap-style visualization
    # Group by week
    df_activity['week'] = df_activity['date'].dt.isocalendar().week
    df_activity['day_of_week'] = df_activity['date'].dt.dayofweek
    df_activity['week_start'] = df_activity['date'] - pd.to_timedelta(df_activity['day_of_week'], unit='d')
    
    # Bar chart for activity
    fig_activity = px.bar(
        df_activity,
        x='date',
        y='count',
        title='Hoạt động học tập theo ngày',
        labels={'date': 'Ngày', 'count': 'Số hoạt động'},
        color='count',
        color_continuous_scale='YlOrRd'
    )
    fig_activity.update_layout(
        height=300,
        xaxis_title="Ngày",
        yaxis_title="Số hoạt động"
    )
    st.plotly_chart(fig_activity, width='stretch')
else:
    st.info("Chưa có dữ liệu hoạt động trong khoảng thời gian này.")

st.divider()

# --- Topics & Levels Progress ---
col_topics, col_levels = st.columns(2)

with col_topics:
    st.markdown("### 📖 Từ Vựng Theo Chủ Đề")
    topics = analytics.get('topics_progress', {})
    if topics:
        df_topics = pd.DataFrame([
            {"Chủ đề": topic, "Số từ": count}
            for topic, count in topics.items()
        ])
        df_topics = df_topics.sort_values('Số từ', ascending=False)
        
        # Bar chart
        fig_topics = px.bar(
            df_topics,
            x='Chủ đề',
            y='Số từ',
            title='Từ vựng theo chủ đề',
            color='Số từ',
            color_continuous_scale='Blues'
        )
        fig_topics.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_topics, width='stretch')
        
        # Table
        st.dataframe(df_topics, hide_index=True, width='stretch')
    else:
        st.info("Chưa có dữ liệu chủ đề.")

with col_levels:
    st.markdown("### 📊 Từ Vựng Theo Cấp Độ")
    levels = analytics.get('level_progress', {})
    if levels:
        # Order levels
        level_order = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        df_levels = pd.DataFrame([
            {"Cấp độ": level, "Số từ": levels.get(level, 0)}
            for level in level_order
            if level in levels
        ])
        
        # Bar chart
        fig_levels = px.bar(
            df_levels,
            x='Cấp độ',
            y='Số từ',
            title='Từ vựng theo cấp độ',
            color='Số từ',
            color_continuous_scale='Greens'
        )
        fig_levels.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_levels, width='stretch')
        
        # Table
        st.dataframe(df_levels, hide_index=True, width='stretch')
    else:
        st.info("Chưa có dữ liệu cấp độ.")

st.divider()

# --- AI Usage Breakdown ---
st.markdown("### 🤖 Sử Dụng AI")
ai_usage = analytics.get('ai_usage', {})
if ai_usage:
    ai_df_data = []
    feature_labels = {
        'listening': 'Listening',
        'speaking': 'Speaking',
        'reading': 'Reading',
        'writing': 'Writing',
        'other': 'Khác'
    }
    
    for feature, count in ai_usage.items():
        if count > 0:  # Only show features with usage
            ai_df_data.append({
                "Tính năng": feature_labels.get(feature, feature),
                "Số lượt sử dụng": count
            })
    
    if ai_df_data:
        ai_df = pd.DataFrame(ai_df_data)
        ai_df = ai_df.sort_values('Số lượt sử dụng', ascending=False)
        
        # Pie chart
        fig_ai = px.pie(
            ai_df,
            values='Số lượt sử dụng',
            names='Tính năng',
            title='Phân bổ sử dụng AI'
        )
        fig_ai.update_layout(height=400)
        st.plotly_chart(fig_ai, width='stretch')
        
        # Table
        st.dataframe(ai_df, hide_index=True, width='stretch')
    else:
        st.info("Chưa sử dụng tính năng AI trong khoảng thời gian này.")
else:
    st.info("Chưa có dữ liệu sử dụng AI.")

st.divider()

# --- Export Options ---
st.markdown("### 💾 Xuất Dữ Liệu")
col_export1, col_export2 = st.columns(2)

with col_export1:
    if st.button("📥 Xuất CSV", width='stretch', type="primary"):
        csv_data = export_analytics_to_csv(user_id, days=days_option)
        if csv_data:
            st.download_button(
                label="⬇️ Tải file CSV",
                data=csv_data,
                file_name=f"analytics_{user_info.get('username', 'user')}_{days_option}days.csv",
                mime="text/csv",
                width='stretch'
            )
        else:
            st.error("Không thể xuất dữ liệu CSV.")

with col_export2:
    if st.button("📄 Xuất PDF", width='stretch'):
        pdf_data = export_analytics_to_pdf(user_id, days=days_option)
        if pdf_data:
            st.download_button(
                label="⬇️ Tải file PDF",
                data=pdf_data,
                file_name=f"analytics_{user_info.get('username', 'user')}_{days_option}days.pdf",
                mime="application/pdf",
                width='stretch'
            )
        else:
            st.info("PDF export chưa được triển khai. Sử dụng CSV để xuất dữ liệu.")

# --- Footer ---
st.caption("💡 Dữ liệu được cập nhật theo thời gian thực. Analytics Dashboard chỉ dành cho Premium users.")
