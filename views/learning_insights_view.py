"""
Learning Insights View - UI Components for Learning Insights
"""
import streamlit as st
from typing import Dict, List


def render_learning_insights(user_id: int, days: int = 30):
    """
    Render Learning Insights section in Dashboard.
    
    Args:
        user_id: User ID
        days: Number of days to analyze
    """
    st.markdown("### 💡 Learning Insights")
    st.caption("Phân tích điểm mạnh/yếu và đề xuất học tập cá nhân hóa (AI-Powered)")
    
    try:
        from services.learning_insights_service import get_learning_insights
        
        with st.spinner("Đang phân tích dữ liệu học tập..."):
            insights = get_learning_insights(user_id, days=days)
        
        if not insights:
            st.info("Chưa đủ dữ liệu để phân tích. Hãy học thêm để nhận insights!")
            return
        
        weaknesses = insights.get('weaknesses', {})
        strengths = insights.get('strengths', {})
        recommendations = insights.get('recommendations', [])
        
        # Display Top 3 Weaknesses
        st.markdown("#### 🔴 Điểm cần cải thiện (Top 3)")
        
        vocab_weak = weaknesses.get('vocabulary_weaknesses', [])[:3]
        grammar_weak = weaknesses.get('grammar_weaknesses', [])[:3]
        skill_weak = weaknesses.get('skill_weaknesses', {})
        topic_weak = weaknesses.get('topic_weaknesses', [])[:3]
        
        weakness_items = []
        
        # Vocabulary weaknesses
        if vocab_weak:
            for word in vocab_weak[:2]:
                weakness_items.append({
                    'type': 'vocabulary',
                    'title': f"Từ vựng: {word.get('word', 'N/A')}",
                    'description': f"Quên {word.get('mistake_count', 0)} lần",
                    'icon': '📚'
                })
        
        # Grammar weaknesses
        if grammar_weak:
            for grammar in grammar_weak[:2]:
                weakness_items.append({
                    'type': 'grammar',
                    'title': f"Ngữ pháp: {grammar.get('topic', 'N/A')}",
                    'description': f"Điểm trung bình: {grammar.get('avg_score', 0)}/10",
                    'icon': '📝'
                })
        
        # Skill weaknesses
        weak_skills = [k for k, v in skill_weak.items() if v < 70][:2]
        skill_names = {
            'listening': ('👂 Nghe', 'pages/01_Luyen_Nghe.py'),
            'speaking': ('💬 Nói', 'pages/02_Luyen_Noi.py'),
            'reading': ('📄 Đọc', 'pages/03_Luyen_Doc.py'),
            'writing': ('✏️ Viết', 'pages/04_Luyen_Viet.py')
        }
        for skill in weak_skills:
            skill_display, skill_url = skill_names.get(skill, (skill, 'home.py'))
            weakness_items.append({
                'type': 'skill',
                'title': f"Kỹ năng: {skill_display}",
                'description': f"Tiến độ: {skill_weak.get(skill, 0)}%",
                'icon': '💪',
                'action_url': skill_url
            })
        
        # Topic weaknesses
        if topic_weak and len(weakness_items) < 3:
            for topic in topic_weak[:1]:
                weakness_items.append({
                    'type': 'vocabulary',
                    'title': f"Chủ đề: {topic.get('topic', 'N/A')}",
                    'description': f"Thuộc {topic.get('mastery_percent', 0)}% từ vựng",
                    'icon': '📖'
                })
        
        # Display weakness items
        if weakness_items:
            cols = st.columns(min(3, len(weakness_items)))
            for i, item in enumerate(weakness_items[:3]):
                with cols[i]:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 8px; background-color: #fff3cd; border-left: 4px solid #ffc107; margin-bottom: 10px;">
                        <div style="font-size: 1.5em; margin-bottom: 5px;">{item.get('icon', '⚠️')}</div>
                        <div style="font-weight: bold; color: #856404; margin-bottom: 5px;">{item.get('title', '')}</div>
                        <div style="color: #856404; font-size: 0.9em;">{item.get('description', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("🎉 Bạn đang làm tốt! Không có điểm yếu nào cần cải thiện ngay lập tức.")
        
        st.divider()
        
        # Display Top 3 Recommendations
        st.markdown("#### 🎯 Đề xuất học tập (AI-Powered)")
        
        if recommendations:
            # Display top 3 recommendations
            for i, rec in enumerate(recommendations[:3], 1):
                rec_type = rec.get('type', 'general')
                title = rec.get('title', 'Đề xuất học tập')
                description = rec.get('description', '')
                priority = rec.get('priority', 'medium')
                action_url = rec.get('action_url', 'home.py')
                
                # Priority colors
                priority_colors = {
                    'high': ('#dc3545', '🔴'),
                    'medium': ('#ffc107', '🟡'),
                    'low': ('#28a745', '🟢')
                }
                priority_color, priority_icon = priority_colors.get(priority, ('#6c757d', '⚪'))
                
                # Type icons
                type_icons = {
                    'vocabulary': '📚',
                    'grammar': '📝',
                    'skill': '💪',
                    'general': '💡'
                }
                type_icon = type_icons.get(rec_type, '💡')
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 8px; background-color: #f8f9fa; border-left: 4px solid {priority_color}; margin-bottom: 10px;">
                        <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 5px;">
                            {type_icon} {title}
                        </div>
                        <div style="color: #495057; font-size: 0.95em;">{description}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("👉 Làm ngay", key=f"rec_action_{i}", width='stretch'):
                        st.switch_page(action_url)
        else:
            st.info("💡 Chưa có đề xuất. Hãy học thêm để nhận recommendations từ AI!")
        
        # Display Strengths (collapsible)
        with st.expander("✨ Điểm mạnh của bạn", expanded=False):
            vocab_strengths = strengths.get('vocabulary_strengths', [])
            grammar_strengths = strengths.get('grammar_strengths', [])
            skill_strengths = strengths.get('skill_strengths', {})
            
            if vocab_strengths:
                st.markdown("**📚 Từ vựng:**")
                for strength in vocab_strengths[:3]:
                    st.markdown(f"- {strength.get('topic', 'N/A')}: {strength.get('mastery_percent', 0)}% mastery ({strength.get('learned', 0)}/{strength.get('total', 0)} từ)")
            
            if grammar_strengths:
                st.markdown("**📝 Ngữ pháp:**")
                for strength in grammar_strengths[:3]:
                    st.markdown(f"- {strength.get('topic', 'N/A')}: Điểm trung bình {strength.get('avg_score', 0)}/10")
            
            strong_skills = [k for k, v in skill_strengths.items() if v >= 70]
            if strong_skills:
                skill_names = {
                    'listening': '👂 Nghe',
                    'speaking': '💬 Nói',
                    'reading': '📄 Đọc',
                    'writing': '✏️ Viết'
                }
                st.markdown("**💪 Kỹ năng:**")
                for skill in strong_skills:
                    skill_display = skill_names.get(skill, skill)
                    st.markdown(f"- {skill_display}: {skill_strengths.get(skill, 0)}%")
    
    except Exception as e:
        st.error(f"Lỗi khi tải Learning Insights: {e}")
        import logging
        logging.error(f"Error rendering learning insights: {e}")
