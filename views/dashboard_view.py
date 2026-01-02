import streamlit as st
from core.config import LEVELS
import pandas as pd

def render_hero_section():
    """Hiển thị Hero Section"""
    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="background: -webkit-linear-gradient(45deg, #003366, #007BFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3em; margin-bottom: 0;">ENGLISH MASTER</h1>
            <p style="font-size: 1.2em; color: #666;">Học tập chủ động - Nâng tầm bản thân</p>
        </div>
    """, unsafe_allow_html=True)

def render_stats_bar(stats, current_streak):
    """Hiển thị thanh thống kê (Stats Bar)"""
    # Get total vocabulary count from database (import at top level to avoid runtime errors)
    try:
        from services.vocab_service import get_total_vocabulary_count
        total_vocab = get_total_vocabulary_count()
    except Exception as e:
        # Fallback if function not available
        total_vocab = 0
    
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        
        c1.metric("🔥 Streak", f"{current_streak} ngày")
        c2.metric("📚 Đã học", f"{stats.get('words_learned', 0)} từ")
        c3.metric("📖 Tổng từ vựng", f"{total_vocab:,} từ")
        c4.metric("🎯 Hôm nay", f"{stats.get('words_today', 0)}/10")
        
        # Smart CTA Logic
        btn_label = "🚀 Học Ngay" if stats.get('words_today', 0) < 10 else "⚔️ Đấu Trường"
        if c5.button(btn_label, type="primary"):
            target_page = "pages/06_On_Tap.py" if stats.get('words_today', 0) < 10 else "pages/09_Dau_Truong.py"
            st.switch_page(target_page)

def render_leaderboard(lb_data):
    """Hiển thị bảng xếp hạng theo kiểu podium (hạng 1 ở giữa, 2-3 hai bên, 4-5 ở dưới)"""
    st.markdown("### 🏆 Bảng Vàng Vinh Danh")
    st.caption("Top 5 học viên có số từ vựng đã học cao nhất.")
    
    if lb_data:
        # Add CSS for podium layout
        st.markdown("""
        <style>
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            .podium-card {
                text-align: center;
                border-radius: 15px;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .podium-card:hover {
                transform: translateY(-5px);
            }
            .rank-1 {
                min-height: 320px;
            }
            .rank-2 {
                min-height: 280px;
            }
            .rank-3 {
                min-height: 260px;
            }
            .rank-4, .rank-5 {
                min-height: 200px;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Top row: Rank 2, Rank 1 (center), Rank 3
        top_row = st.columns([2, 8, 2])
        
        # Map data to positions
        items = {0: None, 1: None, 2: None, 3: None, 4: None}
        for idx, item in enumerate(lb_data[:5]):
            items[idx] = item
        
        # Render Rank 2 (left)
        if items[1]:
            with top_row[0]:
                item = items[1]
                render_rank_card(item, 1, "rank-2")
        
        # Render Rank 1 (center - tallest)
        if items[0]:
            with top_row[1]:
                item = items[0]
                render_rank_card(item, 0, "rank-1")
        
        # Render Rank 3 (right)
        if items[2]:
            with top_row[2]:
                item = items[2]
                render_rank_card(item, 2, "rank-3")
        
        # Bottom row: Rank 4 and Rank 5
        if items[3] or items[4]:
            bottom_row = st.columns(2)
            
            if items[3]:
                with bottom_row[0]:
                    render_rank_card(items[3], 3, "rank-4")
            
            if items[4]:
                with bottom_row[1]:
                    render_rank_card(items[4], 4, "rank-5")
    else:
        st.info("Chưa có dữ liệu để xếp hạng.")

def render_rank_card(item, rank_idx, rank_class):
    """Helper function to render a single rank card"""
    rank_icon = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][rank_idx]
    avatar = item.get('avatar_url') or "https://cdn-icons-png.flaticon.com/512/197/197374.png"
    frame = item.get('active_avatar_frame')
    
    # Frame style from frame_service (simplified for leaderboard)
    from services.frame_service import get_frame_border_style
    frame_style = get_frame_border_style(frame)
    
    # Styles for each rank
    if rank_idx == 0:  # TOP 1 - NỔI BẬT NHẤT
        card_bg = "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)"
        border_color = "#FFD700"
        shadow = "0 8px 25px rgba(255, 215, 0, 0.6)"
        name_color = "#8B4513"
        icon_size = "4em"
        avatar_size = "100px"
        card_padding = "25px"
        animate = "animation: pulse 2s ease-in-out infinite;"
        text_size = "1.3em"
    elif rank_idx == 1:  # TOP 2
        card_bg = "linear-gradient(135deg, #C0C0C0 0%, #808080 100%)"
        border_color = "#C0C0C0"
        shadow = "0 6px 20px rgba(192, 192, 192, 0.5)"
        name_color = "#2F4F4F"
        icon_size = "3.2em"
        avatar_size = "85px"
        card_padding = "20px"
        animate = "animation: pulse 2.5s ease-in-out infinite;"
        text_size = "1.15em"
    elif rank_idx == 2:  # TOP 3
        card_bg = "linear-gradient(135deg, #CD7F32 0%, #8B4513 100%)"
        border_color = "#CD7F32"
        shadow = "0 5px 15px rgba(205, 127, 50, 0.4)"
        name_color = "#FFFFFF"
        icon_size = "3em"
        avatar_size = "75px"
        card_padding = "18px"
        animate = "animation: pulse 3s ease-in-out infinite;"
        text_size = "1.1em"
    else:  # TOP 4-5
        card_bg = "#FFFFFF"
        border_color = "#e0e0e0"
        shadow = "0 2px 8px rgba(0,0,0,0.1)"
        name_color = "#333333"
        icon_size = "2.5em"
        avatar_size = "65px"
        card_padding = "18px"
        animate = ""
        text_size = "1em"
    
    st.markdown(f"""
    <div class="podium-card {rank_class}" style="border: 3px solid {border_color}; padding: {card_padding}; background: {card_bg}; box-shadow: {shadow}; {animate}">
        <div style="font-size: {icon_size}; line-height: 1; margin-bottom: 12px;">{rank_icon}</div>
        <img src="{avatar}" style="width:{avatar_size}; height:{avatar_size}; border-radius:50%; margin: 10px 0; object-fit: cover; {frame_style} border: 4px solid white;">
        <div style="font-weight:800; font-size: {text_size}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 8px; color: {name_color}; text-shadow: {('1px 1px 2px rgba(0,0,0,0.3)' if rank_idx < 3 else 'none')};">{item.get('name', 'User')}</div>
        <span style="color: {'#FFFFFF' if rank_idx < 3 else '#2563eb'}; font-weight: 700; font-size: {text_size}; text-shadow: {('1px 1px 2px rgba(0,0,0,0.3)' if rank_idx < 3 else 'none')};">{item.get('words_learned', 0)} từ</span>
    </div>
    """, unsafe_allow_html=True)

def render_daily_quests(quests, user_id):
    """Hiển thị nhiệm vụ hàng ngày và tự động thưởng coin khi complete"""
    st.markdown("### 📜 Nhiệm Vụ Hàng Ngày")
    
    if not quests:
        st.info("Đang tải nhiệm vụ...")
        return
    
    from services.quest_service import complete_daily_quest, has_received_daily_quest_reward

    # Hiển thị nhiệm vụ
    all_done = True
    done_count = 0
    
    # Filter out the 'complete_all' quest for the loop
    individual_quests = [q for q in quests if q['id'] != 'complete_all']
    
    for q in individual_quests:
        is_done = q['current'] >= q['target']
        if is_done:
            done_count += 1
        else:
            all_done = False

        icon = "✅" if is_done else "⬜"
        reward_received = has_received_daily_quest_reward(user_id, q['id']) if is_done else False
        reward_text = " (Đã nhận 🎉)" if reward_received else ""
        
        st.markdown(f"{icon} {q['desc']} ({q['current']}/{q['target']}) - **Thưởng: {q['reward']} 🪙**{reward_text}")
        
        # Tự động thưởng coin nếu quest complete và chưa nhận reward
        if is_done and not reward_received:
            if complete_daily_quest(user_id, q['id'], q['reward']):
                st.toast(f"💰 Nhận thưởng: {q['reward']} coins từ quest '{q['desc']}'!", icon="💰")
                st.rerun()

    # Xử lý nhiệm vụ tổng hợp
    total_quest = next((q for q in quests if q['id'] == 'complete_all'), None)
    if total_quest:
        is_all_done = (done_count == total_quest['target'])
        icon = "✅" if is_all_done else "⬜"
        reward_received = has_received_daily_quest_reward(user_id, total_quest['id']) if is_all_done else False
        reward_text = " (Đã nhận 🎉)" if reward_received else ""
        
        st.markdown(f"**{icon} {total_quest['desc']} - Thưởng lớn: {total_quest['reward']} 🪙**{reward_text}")
        
        # Tự động thưởng coin nếu quest complete và chưa nhận reward
        if is_all_done and not reward_received:
            if complete_daily_quest(user_id, total_quest['id'], total_quest['reward']):
                st.toast(f"💰 Nhận thưởng lớn: {total_quest['reward']} coins!", icon="💰")
                st.rerun()

def render_weekly_quests(user_id):
    """Hiển thị nhiệm vụ hàng tuần (wrapper để import từ home.py)"""
    from views.weekly_quest_view import render_weekly_quests as render_wq
    render_wq(user_id)

def render_level_mastery(level_progress):
    """Hiển thị tổng quan cấp độ"""
    st.markdown("### 🗺️ Tổng quan cấp độ & Kỹ năng")
    st.caption("Hoàn thành các cột mốc từ vựng và kỹ năng để chinh phục từng cấp độ.")

    tabs = st.tabs([f"Cấp độ {lvl}" for lvl in LEVELS])

    for i, tab in enumerate(tabs):
        lvl = LEVELS[i]
        with tab:
            # 1. Calculate Vocab Stats - FIX: Ensure we have data
            prog = level_progress.get(lvl, {'total': 0, 'learned': 0})
            
            # Debug info - FIX: load_vocab_data returns list, not DataFrame
            if not prog or (prog.get('total', 0) == 0 and prog.get('learned', 0) == 0):
                # Try to fetch fresh data from vocab table
                from services.vocab_service import load_vocab_data
                try:
                    vocab_list = load_vocab_data(lvl)
                    if vocab_list and len(vocab_list) > 0:
                        prog = {'total': len(vocab_list), 'learned': 0}
                    else:
                        prog = {'total': 0, 'learned': 0}
                except Exception as e:
                    import logging
                    logging.error(f"Error loading vocab data for {lvl}: {e}")
                    prog = {'total': 0, 'learned': 0}
            
            total_words = prog.get('total', 0)
            learned_words = prog.get('learned', 0)
            pct = (learned_words / total_words) if total_words > 0 else 0
            
            # 2. Layout
            col_main, col_skills, col_test = st.columns([2, 1.5, 1])
            
            with col_main:
                st.subheader(f"📊 Tiến độ Từ vựng {lvl}")
                st.progress(pct, text=f"Đã thuộc: {learned_words}/{total_words} từ ({int(pct*100)}%)")
                
                if total_words == 0:
                    st.info(f"📚 Database có {total_words} từ vựng cấp {lvl}. Hãy bắt đầu học!")
                elif pct >= 1.0:
                    st.success("🎉 Xuất sắc! Bạn đã nắm vững từ vựng cấp độ này.")
                elif pct > 0:
                    st.info("💪 Đang học. Hãy tiếp tục cố gắng!")
                else:
                    st.write("Chưa bắt đầu.")
                    if st.button(f"Bắt đầu học {lvl}", key=f"start_{lvl}"):
                        st.switch_page("pages/06_On_Tap.py")

            with col_skills:
                st.subheader("🛠️ Rèn luyện 4 Kỹ năng")
                g1, g2 = st.columns(2)
                g1.page_link("pages/01_Luyen_Nghe.py", label="👂 Nghe", help=f"Luyện nghe {lvl}")
                g1.page_link("pages/02_Luyen_Noi.py", label="💬 Nói", help=f"Luyện nói {lvl}")
                g2.page_link("pages/03_Luyen_Doc.py", label="📄 Đọc", help=f"Luyện đọc {lvl}")
                g2.page_link("pages/04_Luyen_Viet.py", label="✏️ Viết", help=f"Luyện viết {lvl}")
                st.page_link("pages/07_Ngu_Phap.py", label="📐 Ngữ pháp")

            with col_test:
                st.subheader("🎓 Kiểm tra")
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; text-align: center; background-color: #f9f9f9;">
                    <h4>Mock Test {lvl}</h4>
                    <p style="font-size: 0.8em; color: #666;">Test 4 kỹ năng + Ngữ pháp</p>
                </div>
                """, unsafe_allow_html=True)
                st.write("") # Spacer
                if st.button(f"✍️ Vào thi {lvl}", key=f"test_{lvl}", type="primary"):
                    st.switch_page("pages/08_Thi_Thu.py")

def render_user_guide():
    """Hiển thị hướng dẫn sử dụng với link đến Help page"""
    # Banner for new users
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("""
        👋 **Chào mừng bạn đến với English Master!** 
        
        Bạn mới bắt đầu? Hãy xem hướng dẫn chi tiết để sử dụng app hiệu quả nhất!
        """)
    with col2:
        if st.button("📚 Xem Hướng Dẫn Đầy Đủ", type="primary", width='stretch'):
            st.switch_page("pages/17_Huong_Dan.py")
    
    with st.expander("📘 HƯỚNG DẪN SỬ DỤNG NHANH", expanded=False):
        guide_tabs = st.tabs(["🚀 Lộ trình học", "🧠 Phương pháp SRS", "🎮 Gamification", "🛠️ Công cụ AI"])
        
        with guide_tabs[0]:
            st.markdown("""
            ### 🗺️ Lộ trình chinh phục tiếng Anh
            1.  **Xác định trình độ:** Bắt đầu với các bài học từ vựng và ngữ pháp phù hợp (A1-C2).
            2.  **Học từ vựng hàng ngày:** Truy cập **Học & Ôn tập** mỗi ngày để nạp từ mới và ôn từ cũ.
            3.  **Nắm vững ngữ pháp:** Học lý thuyết và làm bài tập tại mục **Ngữ Pháp**.
            4.  **Luyện kỹ năng:** Sử dụng các phòng luyện Nghe, Nói, Đọc, Viết để áp dụng kiến thức.
            5.  **Kiểm tra:** Làm bài **Thi thử (Mock Test)** định kỳ để đo lường sự tiến bộ.
            """)
            st.info("💡 **Mẹo:** Hãy học đều đặn 15 phút mỗi ngày thay vì học dồn 2 tiếng một lần.")
            st.markdown("→ **[📚 Xem hướng dẫn chi tiết và FAQ đầy đủ](pages/17_Huong_Dan.py)**")

        with guide_tabs[1]:
            st.markdown("""
            ### 🧠 Hệ thống Lặp lại ngắt quãng (SRS)
            Ứng dụng sử dụng thuật toán thông minh để tính toán thời điểm "vàng" bạn sắp quên từ vựng để nhắc nhở.
            
            *   **🔴 Ôn tập (Review):** Những từ bạn đã học và cần ôn lại ngay hôm nay.
            *   **🔵 Từ mới (New):** Những từ chưa học, được hệ thống đề xuất dựa trên cấp độ của bạn.
            *   **Quy tắc:** Bạn cần hoàn thành tất cả từ ôn tập + số lượng từ mới mục tiêu để hoàn thành nhiệm vụ ngày.
            """)
            st.markdown("→ **[📚 Xem hướng dẫn chi tiết về SRS](pages/17_Huong_Dan.py)**")

        with guide_tabs[2]:
            st.markdown("""
            ### 🎮 Vừa học vừa chơi
            *   **🔥 Streak (Chuỗi ngày):** Học liên tục mỗi ngày để tăng chuỗi. Nếu lỡ 1 ngày, chuỗi sẽ về 0 (trừ khi có *Streak Freeze*).
            *   **🪙 Coin (Tiền vàng):** Kiếm Coin bằng cách học bài, thắng PvP hoặc đạt thành tựu.
            *   **🛒 Cửa hàng:** Dùng Coin để mua giao diện (Theme), khung Avatar, hoặc vật phẩm hỗ trợ.
            *   **⚔️ Đấu trường (PvP):** Thách đấu từ vựng với người dùng khác để nhận thưởng lớn.
            """)
            st.markdown("→ **[📚 Xem hướng dẫn chi tiết về Gamification](pages/17_Huong_Dan.py)**")

        with guide_tabs[3]:
            st.markdown("""
            ### 🤖 Trợ lý AI thông minh
            *   **Luyện Nói:** AI phân tích phát âm và giao tiếp hội thoại (Roleplay) với bạn.
            *   **Luyện Viết:** AI chấm điểm bài luận (Essay) và sửa lỗi ngữ pháp chi tiết.
            *   **Luyện Đọc:** AI tạo bài đọc và câu hỏi hiểu theo chủ đề bạn chọn.
            *   **Luyện Nghe:** AI tạo Podcast và bài tập chép chính tả (Dictation).
            """)
            st.markdown("→ **[📚 Xem hướng dẫn chi tiết về AI Features](pages/17_Huong_Dan.py)**")

