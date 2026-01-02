import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from core.theme_applier import apply_page_theme
from core.data import get_user_stats, supabase, get_user_grammar_progress
from core.theme import render_empty_state
from views.profile_view import (
    render_profile_header,
    render_stats_overview,
    render_achievement_card,
    render_vocab_progress_chart,
    render_test_history_chart
)
from services.user_service import get_user_badges

logger = logging.getLogger(__name__)

# --- Auth Check ---
if not st.session_state.get("logged_in"):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth

# Refresh user info from database to get latest plan/tier/role updates
user_id = st.session_state.get("user_info", {}).get("id")
if user_id:
    try:
        from core.auth import refresh_user_info
        refresh_user_info(user_id)
    except Exception as e:
        logger.warning(f"Could not refresh user info: {e}")

user: Dict[str, Any] = st.session_state.get("user_info")

if user:
    user_id = user.get("id")
    
    # --- Header Profile ---
    render_profile_header(user)

    # --- Stats ---
    try:
        stats = get_user_stats(user_id)
        render_stats_overview(stats)
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        st.warning("Không thể tải thống kê người dùng.")

    st.divider()

    # --- Tabs ---
    tab_achievements, tab_long_term, tab_milestones, tab_vocab, tab_tests = st.tabs([
        "🏆 Thành Tựu & Huy Hiệu", 
        "🌟 Thành Tựu Dài Hạn", 
        "🔥 Streak Milestones",
        "📈 Biểu Đồ Học Tập", 
        "📝 Lịch Sử Thi"
    ])

    with tab_achievements:
        st.subheader("Bảng Thành Tích & Phần Thưởng")
        st.caption("Hoàn thành các cột mốc để nhận Coin và Huy hiệu danh giá!")
    
    with tab_long_term:
        st.subheader("🌟 Long-term Achievements")
        st.caption("Các thành tựu dài hạn bạn đã đạt được và đang phấn đấu!")
        
        try:
            from services.achievement_service import get_achievement_progress
            progress_data = get_achievement_progress(user_id)
            
            achievements = progress_data.get('achievements', {})
            achieved_list = achievements.get('achieved', [])
            progress_list = achievements.get('progress', [])
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Đã đạt được", f"{progress_data.get('achieved_count', 0)}/{progress_data.get('total_count', 0)}")
            with col2:
                st.metric("Đang phấn đấu", len(progress_list))
            with col3:
                completion_rate = (progress_data.get('achieved_count', 0) / max(progress_data.get('total_count', 1), 1)) * 100
                st.metric("Tỷ lệ hoàn thành", f"{completion_rate:.1f}%")
            
            st.divider()
            
            # Achieved Achievements
            if achieved_list:
                st.markdown("### ✅ Đã đạt được")
                
                # Group by type
                type_groups = {}
                for ach in achieved_list:
                    ach_type = ach.get('type', 'other')
                    if ach_type not in type_groups:
                        type_groups[ach_type] = []
                    type_groups[ach_type].append(ach)
                
                type_names = {
                    'vocab': '📚 Từ vựng',
                    'skill': '💪 Kỹ năng',
                    'grammar': '📝 Ngữ pháp',
                    'pvp': '⚔️ PvP',
                    'quest': '📜 Quests'
                }
                
                for ach_type, type_achs in type_groups.items():
                    st.markdown(f"##### {type_names.get(ach_type, ach_type)}")
                    cols = st.columns(3)
                    for i, ach in enumerate(type_achs):
                        with cols[i % 3]:
                            st.markdown(f"""
                            <div style="padding: 15px; border-radius: 8px; background-color: #d4edda; border-left: 4px solid #28a745; margin-bottom: 10px;">
                                <div style="font-size: 1.5em; margin-bottom: 5px;">{ach.get('icon', '🏆')}</div>
                                <div style="font-weight: bold; color: #155724; margin-bottom: 5px;">{ach.get('name', '')}</div>
                                <div style="color: #155724; font-size: 0.9em; margin-bottom: 5px;">{ach.get('description', '')}</div>
                                <div style="color: #155724; font-size: 0.85em;">💰 {ach.get('reward_coins', 0)} coins</div>
                            </div>
                            """, unsafe_allow_html=True)
                    st.divider()
            else:
                st.info("Bạn chưa đạt achievement nào. Hãy học tập để đạt các thành tựu!")
            
            # In-Progress Achievements
            if progress_list:
                st.markdown("### 🎯 Đang phấn đấu")
                
                # Group by type
                type_groups = {}
                for ach in progress_list:
                    ach_type = ach.get('type', 'other')
                    if ach_type not in type_groups:
                        type_groups[ach_type] = []
                    type_groups[ach_type].append(ach)
                
                type_names = {
                    'vocab': '📚 Từ vựng',
                    'skill': '💪 Kỹ năng',
                    'grammar': '📝 Ngữ pháp',
                    'pvp': '⚔️ PvP',
                    'quest': '📜 Quests'
                }
                
                for ach_type, type_achs in type_groups.items():
                    st.markdown(f"##### {type_names.get(ach_type, ach_type)}")
                    for ach in type_achs[:5]:  # Show top 5 per type
                        progress_val = ach.get('progress', 0)
                        target_val = ach.get('target', 1)
                        progress_percent = (progress_val / max(target_val, 1)) * 100
                        
                        st.markdown(f"**{ach.get('icon', '🏆')} {ach.get('name', '')}**")
                        st.progress(progress_percent / 100)
                        st.caption(f"{ach.get('description', '')} - {progress_val}/{target_val} ({progress_percent:.1f}%)")
                    if len(type_achs) > 5:
                        st.caption(f"... và {len(type_achs) - 5} achievements khác")
                    st.divider()
            else:
                st.info("🎉 Tuyệt vời! Bạn đã đạt tất cả achievements đang theo dõi!")
        
        except Exception as e:
            st.error(f"Lỗi khi tải achievements: {e}")
            import logging
            logging.error(f"Error loading achievements: {e}")
    
    with tab_milestones:
        st.subheader("🔥 Streak Milestones")
        st.caption("Các cột mốc streak bạn đã đạt được và phần thưởng!")
        
        try:
            from services.streak_service import get_milestone_progress
            current_streak = stats.get('streak', 0)
            milestone_progress = get_milestone_progress(user_id, current_streak)
            
            achieved_milestones = milestone_progress.get('achieved_milestones', [])
            next_milestone = milestone_progress.get('next_milestone')
            
            # Display achieved milestones
            if achieved_milestones:
                st.markdown("### ✅ Đã đạt được")
                for milestone in achieved_milestones:
                    milestone_days = milestone.get('milestone_days', 0)
                    name = milestone.get('name', f"{milestone_days} Days")
                    coins = milestone.get('reward_coins', 0)
                    achieved_at = milestone.get('achieved_at', '')
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**{name}** ({milestone_days} ngày)")
                    with col2:
                        st.markdown(f"💰 {coins} coins")
                    with col3:
                        if achieved_at:
                            try:
                                from datetime import datetime
                                date_obj = datetime.fromisoformat(achieved_at.replace('Z', '+00:00'))
                                st.caption(date_obj.strftime("%d/%m/%Y"))
                            except:
                                st.caption("—")
                        else:
                            st.caption("—")
                    st.divider()
            else:
                st.info("Bạn chưa đạt milestone nào. Hãy giữ streak để nhận phần thưởng!")
            
            # Display next milestone
            if next_milestone:
                st.markdown("### 🎯 Milestone tiếp theo")
                milestone_days = next_milestone.get('milestone_days', 0)
                name = next_milestone.get('name', f"{milestone_days} Days")
                days_remaining = next_milestone.get('days_remaining', 0)
                coins = next_milestone.get('reward_coins', 0)
                
                progress_percent = ((current_streak / milestone_days) * 100) if milestone_days > 0 else 0
                progress_percent = min(100, max(0, progress_percent))
                
                st.markdown(f"**{name}** - Còn {days_remaining} ngày")
                st.progress(progress_percent / 100)
                st.markdown(f"💰 Phần thưởng: **{coins} coins**")
            else:
                st.success("🎉 Bạn đã đạt tất cả milestones! Tuyệt vời!")
        
        except Exception as e:
            st.error(f"Lỗi khi tải milestone: {e}")
            import logging
            logging.error(f"Error loading milestones: {e}")
        
        # 1. Định nghĩa danh sách thành tựu (Hardcoded for Gamification Logic)
        achievements = [
            # Streak
            {"id": "streak_3", "name": "Khởi động", "desc": "Chuỗi 3 ngày", "icon": "🔥", "type": "streak", "target": 3, "reward": 20},
            {"id": "streak_7", "name": "Tuần lễ vàng", "desc": "Chuỗi 7 ngày", "icon": "📅", "type": "streak", "target": 7, "reward": 50},
            {"id": "streak_14", "name": "Kiên trì", "desc": "Chuỗi 14 ngày", "icon": "🛡️", "type": "streak", "target": 14, "reward": 100},
            {"id": "streak_30", "name": "Thói quen thép", "desc": "Chuỗi 30 ngày", "icon": "⚔️", "type": "streak", "target": 30, "reward": 300},
            {"id": "streak_60", "name": "Bất khả chiến bại", "desc": "Chuỗi 60 ngày", "icon": "👑", "type": "streak", "target": 60, "reward": 600},
            {"id": "streak_90", "name": "Huyền thoại", "desc": "Chuỗi 90 ngày", "icon": "💎", "type": "streak", "target": 90, "reward": 1000},
            {"id": "streak_180", "name": "Thần thánh", "desc": "Chuỗi 180 ngày", "icon": "⚡", "type": "streak", "target": 180, "reward": 2000},
            {"id": "streak_365", "name": "Bất tử", "desc": "Chuỗi 365 ngày", "icon": "🌟", "type": "streak", "target": 365, "reward": 5000},
            
            # Vocab
            {"id": "vocab_10", "name": "Bước đầu tiên", "desc": "Thuộc 10 từ", "icon": "🌱", "type": "vocab", "target": 10, "reward": 10},
            {"id": "vocab_50", "name": "Mọt sách", "desc": "Thuộc 50 từ", "icon": "🐛", "type": "vocab", "target": 50, "reward": 50},
            {"id": "vocab_100", "name": "Thông thái", "desc": "Thuộc 100 từ", "icon": "🦉", "type": "vocab", "target": 100, "reward": 100},
            {"id": "vocab_200", "name": "Từ điển sống", "desc": "Thuộc 200 từ", "icon": "📘", "type": "vocab", "target": 200, "reward": 200},
            {"id": "vocab_500", "name": "Bậc thầy từ vựng", "desc": "Thuộc 500 từ", "icon": "🎓", "type": "vocab", "target": 500, "reward": 500},
            {"id": "vocab_1000", "name": "Thần đồng", "desc": "Thuộc 1000 từ", "icon": "🧠", "type": "vocab", "target": 1000, "reward": 1000},
            {"id": "vocab_2000", "name": "Siêu trí tuệ", "desc": "Thuộc 2000 từ", "icon": "🌌", "type": "vocab", "target": 2000, "reward": 2500},
            {"id": "vocab_5000", "name": "Vua tiếng Anh", "desc": "Thuộc 5000 từ", "icon": "👑", "type": "vocab", "target": 5000, "reward": 5000},
            
            # Grammar (NEW)
            {"id": "grammar_5", "name": "Tập sự ngữ pháp", "desc": "Xong 5 bài ngữ pháp", "icon": "📝", "type": "grammar", "target": 5, "reward": 50},
            {"id": "grammar_10", "name": "Hiểu biết", "desc": "Xong 10 bài ngữ pháp", "icon": "📒", "type": "grammar", "target": 10, "reward": 100},
            {"id": "grammar_20", "name": "Thành thạo ngữ pháp", "desc": "Xong 20 bài ngữ pháp", "icon": "📘", "type": "grammar", "target": 20, "reward": 150},
            {"id": "grammar_50", "name": "Chuyên gia ngữ pháp", "desc": "Xong 50 bài ngữ pháp", "icon": "🎓", "type": "grammar", "target": 50, "reward": 300},
            {"id": "grammar_100", "name": "Giáo sư", "desc": "Xong 100 bài ngữ pháp", "icon": "🏛️", "type": "grammar", "target": 100, "reward": 1000},
            
            # Coin
            {"id": "coin_100", "name": "Tiết kiệm", "desc": "Có 100 Coin", "icon": "🐷", "type": "coin", "target": 100, "reward": 20},
            {"id": "coin_500", "name": "Khá giả", "desc": "Có 500 Coin", "icon": "💰", "type": "coin", "target": 500, "reward": 50},
            {"id": "coin_1000", "name": "Đại gia", "desc": "Có 1000 Coin", "icon": "💎", "type": "coin", "target": 1000, "reward": 100},
            {"id": "coin_5000", "name": "Triệu phú", "desc": "Có 5000 Coin", "icon": "🏦", "type": "coin", "target": 5000, "reward": 500},
            {"id": "coin_10000", "name": "Tỷ phú", "desc": "Có 10000 Coin", "icon": "🚀", "type": "coin", "target": 10000, "reward": 1000},
            {"id": "coin_50000", "name": "Vua tiền tệ", "desc": "Có 50000 Coin", "icon": "🪐", "type": "coin", "target": 50000, "reward": 5000},
            
            # PvP
            {"id": "pvp_1", "name": "Tân binh", "desc": "Thắng 1 trận PvP", "icon": "⚔️", "type": "pvp", "target": 1, "reward": 20},
            {"id": "pvp_5", "name": "Đấu sĩ", "desc": "Thắng 5 trận PvP", "icon": "🛡️", "type": "pvp", "target": 5, "reward": 100},
            {"id": "pvp_10", "name": "Chiến tướng", "desc": "Thắng 10 trận PvP", "icon": "🏆", "type": "pvp", "target": 10, "reward": 200},
            {"id": "pvp_20", "name": "Huyền thoại", "desc": "Thắng 20 trận PvP", "icon": "🐉", "type": "pvp", "target": 20, "reward": 500},
            {"id": "pvp_50", "name": "Thần chiến tranh", "desc": "Thắng 50 trận PvP", "icon": "👹", "type": "pvp", "target": 50, "reward": 1000},
            {"id": "pvp_100", "name": "Độc cô cầu bại", "desc": "Thắng 100 trận PvP", "icon": "☠️", "type": "pvp", "target": 100, "reward": 2000},
        ]

        # 2. Lấy chỉ số hiện tại của User
        current_streak = stats.get('streak', 0)
        current_vocab = stats.get('words_learned', 0)
        current_coins = stats.get('coins', 0)
        
        # Lấy số trận thắng PvP (Query riêng vì không có trong stats mặc định)
        pvp_wins = 0
        try:
            pvp_res = supabase.table("PvPChallenges").select("id", count="exact").eq("winner_id", user_id).execute()
            pvp_wins = pvp_res.count
        except: pass
        
        # Lấy tiến độ Grammar
        current_grammar = 0
        try:
            grammar_prog = get_user_grammar_progress(user_id)
            current_grammar = len([k for k, v in grammar_prog.items() if v == 'completed'])
        except: pass

        # 3. Render Grid Thành Tựu (Phân loại theo nhóm)
        groups = [
            ("streak", "🔥 Chuỗi Ngày (Streak)"),
            ("vocab", "📚 Từ Vựng (Vocabulary)"),
            ("grammar", "🧪 Ngữ Pháp (Grammar)"),
            ("coin", "💰 Tài Sản (Coin)"),
            ("pvp", "⚔️ Đấu Trường (PvP)")
        ]

        for g_type, g_name in groups:
            group_items = [a for a in achievements if a['type'] == g_type]
            if not group_items: continue
            
            st.markdown(f"##### {g_name}")
            cols = st.columns(3)
            
            for i, ach in enumerate(group_items):
                # Xác định tiến độ
                current_val = 0
                if ach['type'] == 'streak': current_val = current_streak
                elif ach['type'] == 'vocab': current_val = current_vocab
                elif ach['type'] == 'coin': current_val = current_coins
                elif ach['type'] == 'pvp': current_val = pvp_wins
                elif ach['type'] == 'grammar': current_val = current_grammar
                
                with cols[i % 3]:
                    render_achievement_card(ach, current_val)
            
            st.divider()

    with tab_vocab:
        st.subheader("Tiến độ học từ vựng (7 ngày qua)")
        
        # Fetch data for chart
        try:
            # Lấy dữ liệu học trong 7 ngày gần nhất
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            res = supabase.table("UserVocabulary") \
                .select("created_at") \
                .eq("user_id", str(user_id)) \
                .gte("created_at", start_date.strftime('%Y-%m-%d')) \
                .execute()
                
            if res.data:
                df = pd.DataFrame(res.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['date'] = df['created_at'].dt.strftime('%d/%m')
                chart_data = df.groupby('date').size().reset_index(name='words')
                render_vocab_progress_chart(chart_data)
            else:
                render_empty_state("Chưa có dữ liệu học tập tuần qua", "📉")
                
        except Exception as e:
            logger.error(f"Vocabulary chart error: {e}")
            st.info("Chưa có đủ dữ liệu để vẽ biểu đồ tiến độ.")

    with tab_tests:
        st.subheader("Lịch sử bài thi thử")
        try:
            res = supabase.table("MockTestResults") \
                .select("level, score, completed_at") \
                .eq("user_id", str(user_id)) \
                .order("completed_at", desc=False) \
                .execute()
                
            if res.data:
                df_tests = pd.DataFrame(res.data)
                df_tests['completed_at'] = pd.to_datetime(df_tests['completed_at'])
                render_test_history_chart(df_tests)
            else:
                render_empty_state("Bạn chưa làm bài thi thử nào", "📝")
                if st.button("Làm bài thi ngay"):
                    st.switch_page("pages/08_Thi_Thu.py")
        except Exception as e:
            logger.error(f"Test history error: {e}")
            err_msg = str(e)
            if "PGRST205" in err_msg:
                st.warning("⚠️ Chưa tìm thấy bảng dữ liệu điểm thi. Vui lòng chạy lệnh SQL tạo bảng 'MockTestResults' trong Supabase.")
            else:
                st.error(f"Lỗi tải lịch sử thi: {e}")

else:
    st.warning("⚠️ Không tìm thấy thông tin người dùng. Vui lòng đăng nhập lại.")
    if st.button("Về trang chủ"):
        st.switch_page("home.py")

