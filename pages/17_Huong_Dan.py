import streamlit as st
import logging

from core.theme_applier import apply_page_theme
from core.sidebar import render_sidebar

logger = logging.getLogger(__name__)

# --- Page Config ---
st.set_page_config(
    page_title="Hướng Dẫn Sử Dụng | English Master",
    page_icon="📚",
    layout="wide"
)

# --- Theme & Sidebar ---
apply_page_theme()

# --- Page Title ---
st.title("📚 Hướng Dẫn Sử Dụng")
st.markdown("---")

# --- Tabs for different sections ---
tab_overview, tab_features, tab_tutorials, tab_qa = st.tabs([
    "🏠 Tổng Quan",
    "✨ Tính Năng",
    "🎓 Hướng Dẫn Chi Tiết",
    "❓ Câu Hỏi Thường Gặp"
])

# ========== TAB 1: TỔNG QUAN ==========
with tab_overview:
    st.header("🏠 Giới Thiệu English Master")
    
    st.markdown("""
    ### Chào mừng bạn đến với English Master!
    
    **English Master** là ứng dụng học tiếng Anh toàn diện được thiết kế đặc biệt cho người Việt Nam. 
    Ứng dụng giúp bạn học tiếng Anh từ cơ bản đến nâng cao một cách hiệu quả và thú vị.
    
    #### 🎯 Mục tiêu của ứng dụng:
    - Học tiếng Anh từ con số 0
    - Cải thiện 4 kỹ năng: Nghe, Nói, Đọc, Viết
    - Học từ vựng và ngữ pháp có hệ thống
    - Theo dõi tiến độ học tập chi tiết
    - Tạo động lực học tập thông qua gamification
    
    #### 🚀 Bắt đầu nhanh:
    1. **Đăng ký/Đăng nhập** tài khoản
    2. **Làm bài kiểm tra đầu vào** để xác định trình độ
    3. **Bắt đầu học** với các bài học phù hợp với trình độ của bạn
    4. **Theo dõi tiến độ** qua Dashboard và Analytics
    
    ---
    """)
    
    st.subheader("📋 Cấu Trúc Ứng Dụng")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 🎓 Phần Học Tập
        - **Kiểm Tra Đầu Vào**: Đánh giá trình độ ban đầu
        - **Luyện Nghe**: Podcast, dictation, listening exercises
        - **Luyện Nói**: Speech recognition, pronunciation
        - **Luyện Đọc**: Reading comprehension, vocabulary
        - **Luyện Viết**: Writing exercises với AI feedback
        - **Luyện Dịch**: Translation exercises
        - **Ngữ Pháp**: Grammar lessons và exercises
        - **Kho Từ Vựng**: Vocabulary library với SRS
        - **Ôn Tập**: Spaced repetition system
        """)
    
    with col2:
        st.markdown("""
        #### 🎮 Phần Gamification
        - **Đấu Trường**: PvP challenges
        - **Thi Thử**: Mock tests
        - **Cửa Hàng**: Mua items, badges, frames
        - **Hồ Sơ**: Xem achievements, stats
        - **Quest**: Daily và weekly quests
        
        #### ⚙️ Phần Quản Lý
        - **Cài Đặt**: Tùy chỉnh app
        - **Góp Ý**: Gửi feedback
        - **Premium**: Nâng cấp tài khoản
        """)
    
    st.divider()
    
    st.subheader("🎯 Lộ Trình Học Tập Đề Xuất")
    
    st.markdown("""
    #### Cho người mới bắt đầu:
    1. **Bước 1**: Đăng ký và làm bài kiểm tra đầu vào
    2. **Bước 2**: Bắt đầu với **Kho Từ Vựng** - học 10-20 từ mới mỗi ngày
    3. **Bước 3**: Sử dụng **Luyện Nghe** để làm quen với phát âm
    4. **Bước 4**: Thực hành **Ngữ Pháp** cơ bản (A1)
    5. **Bước 5**: Ôn tập hàng ngày với **Ôn Tập SRS**
    6. **Bước 6**: Duy trì streak và hoàn thành daily quests
    
    #### Cho người đã có nền tảng:
    - Tập trung vào **Luyện Nói** và **Luyện Viết**
    - Tham gia **Đấu Trường** để cạnh tranh
    - Làm **Thi Thử** để đánh giá trình độ
    - Học từ vựng nâng cao và ngữ pháp B1-B2
    """)

# ========== TAB 2: TÍNH NĂNG ==========
with tab_features:
    st.header("✨ Tất Cả Tính Năng Chi Tiết")
    
    # Feature Categories
    features_data = [
        {
            "category": "🎯 Kiểm Tra & Đánh Giá",
            "features": [
                {
                    "name": "Kiểm Tra Đầu Vào",
                    "path": "pages/00_Kiem_Tra_Dau_Vao.py",
                    "description": "Bài kiểm tra AI để đánh giá trình độ tiếng Anh của bạn và đề xuất lộ trình học phù hợp",
                    "how_to": "Truy cập menu 'Kiểm Tra Đầu Vào', làm bài test theo hướng dẫn. Kết quả sẽ xác định level của bạn (A1-C2).",
                    "tips": "Làm bài nghiêm túc để có kết quả chính xác. Bạn có thể làm lại test sau 30 ngày."
                },
                {
                    "name": "Thi Thử",
                    "path": "pages/08_Thi_Thu.py",
                    "description": "Mock tests để luyện thi và đánh giá trình độ định kỳ",
                    "how_to": "Chọn đề thi, làm bài trong thời gian quy định, xem kết quả và phân tích chi tiết.",
                    "tips": "Làm thi thử thường xuyên để theo dõi sự tiến bộ. Premium users có nhiều đề thi hơn."
                }
            ]
        },
        {
            "category": "📚 Học Tập Cơ Bản",
            "features": [
                {
                    "name": "Kho Từ Vựng",
                    "path": "pages/05_Kho_Tu_Vung.py",
                    "description": "Thư viện từ vựng đầy đủ với giải nghĩa, ví dụ, phát âm. Học từ theo chủ đề và level",
                    "how_to": "Browse từ vựng theo chủ đề/level, click 'Thêm vào danh sách học' để bắt đầu học. Free: 20 từ/ngày, Premium: không giới hạn.",
                    "tips": "Học từ vựng mỗi ngày là cách tốt nhất để cải thiện. Sử dụng SRS để ghi nhớ lâu dài."
                },
                {
                    "name": "Ôn Tập SRS",
                    "path": "pages/06_On_Tap.py",
                    "description": "Hệ thống ôn tập Spaced Repetition System - lặp lại từ vựng đã học theo khoa học để ghi nhớ lâu",
                    "how_to": "Truy cập 'Ôn Tập', xem từ cần ôn, chọn mức độ nhớ (Dễ/Nhớ/Khó/Quên). Hệ thống sẽ tự động sắp xếp lịch ôn tập.",
                    "tips": "Ôn tập đều đặn mỗi ngày. Đánh giá chính xác mức độ nhớ sẽ giúp SRS hoạt động tốt hơn."
                },
                {
                    "name": "Ngữ Pháp",
                    "path": "pages/07_Ngu_Phap.py",
                    "description": "Học ngữ pháp từ A1 đến C2 với bài giảng, ví dụ và bài tập",
                    "how_to": "Chọn level (A1-C2), chọn bài học, đọc lý thuyết, làm bài tập, xem đáp án và giải thích.",
                    "tips": "Học ngữ pháp kết hợp với từ vựng. Làm lại bài tập khi sai để ghi nhớ tốt hơn."
                },
                {
                    "name": "Động Từ Bất Quy Tắc",
                    "path": "pages/13_Dong_Tu_Bat_Quy_Tac.py",
                    "description": "Học và ghi nhớ động từ bất quy tắc quan trọng trong tiếng Anh",
                    "how_to": "Xem danh sách động từ, học từng nhóm, làm quiz để kiểm tra.",
                    "tips": "Học theo nhóm có cùng pattern để dễ nhớ hơn."
                }
            ]
        },
        {
            "category": "🎧 Kỹ Năng Nghe & Nói",
            "features": [
                {
                    "name": "Luyện Nghe",
                    "path": "pages/01_Luyen_Nghe.py",
                    "description": "Luyện kỹ năng nghe với podcast AI, dictation (chính tả), và listening comprehension",
                    "how_to": """
                    **Podcast:**
                    - Chọn chủ đề hoặc để AI tự chọn
                    - Nghe podcast và đọc transcript
                    - Xem vocabulary highlights
                    
                    **Dictation:**
                    - Nghe câu và viết lại
                    - Xem đáp án và phát âm
                    - Luyện với các level khác nhau
                    
                    **Free:** 5 lượt AI/ngày/tính năng
                    **Premium:** 600-1200 lượt/tháng tùy gói
                    """,
                    "tips": "Nghe đi nghe lại nhiều lần. Bắt đầu với tốc độ chậm, tăng dần khi quen."
                },
                {
                    "name": "Luyện Nói",
                    "path": "pages/02_Luyen_Noi.py",
                    "description": "Luyện phát âm và speaking với AI speech recognition và feedback",
                    "how_to": "Chọn bài luyện nói, nghe câu mẫu, nhấn nút để nói, AI sẽ đánh giá phát âm và đưa feedback.",
                    "tips": "Nói rõ ràng, đúng tốc độ. Luyện tập thường xuyên để cải thiện phát âm."
                }
            ]
        },
        {
            "category": "📖 Kỹ Năng Đọc & Viết",
            "features": [
                {
                    "name": "Luyện Đọc",
                    "path": "pages/03_Luyen_Doc.py",
                    "description": "Đọc hiểu với bài đọc theo level, câu hỏi comprehension và vocabulary building",
                    "how_to": "Đọc bài text, trả lời câu hỏi, xem đáp án và giải thích. Học từ vựng mới từ bài đọc.",
                    "tips": "Đọc kỹ trước khi trả lời. Ghi chú từ vựng mới để học thêm."
                },
                {
                    "name": "Luyện Viết",
                    "path": "pages/04_Luyen_Viet.py",
                    "description": "Luyện viết với AI feedback về ngữ pháp, từ vựng và style",
                    "how_to": "Chọn chủ đề hoặc đề bài, viết bài, gửi để AI đánh giá. Xem feedback chi tiết và sửa lại.",
                    "tips": "Viết đủ độ dài, chú ý ngữ pháp và từ vựng. Đọc lại feedback cẩn thận để cải thiện."
                },
                {
                    "name": "Luyện Dịch",
                    "path": "pages/04_Luyen_Dich.py",
                    "description": "Luyện dịch Việt-Anh và Anh-Việt với AI assistance",
                    "how_to": "Chọn bài dịch, dịch câu/đoạn văn, xem đáp án mẫu và so sánh.",
                    "tips": "Dịch nghĩa chứ không dịch word-by-word. Hiểu ngữ cảnh để dịch chính xác hơn."
                }
            ]
        },
        {
            "category": "🎮 Gamification & Social",
            "features": [
                {
                    "name": "Đấu Trường (PvP)",
                    "path": "pages/09_Dau_Truong.py",
                    "description": "Thách đấu bạn bè, cạnh tranh điểm số, xếp hạng leaderboard",
                    "how_to": "Tạo challenge hoặc chấp nhận challenge từ người khác, làm bài thi, xem kết quả và ranking.",
                    "tips": "Chọn đối thủ phù hợp với trình độ. Luyện tập trước khi thách đấu."
                },
                {
                    "name": "Quest (Nhiệm Vụ)",
                    "description": "Daily quests và weekly quests để nhận phần thưởng",
                    "how_to": "Xem quests trên Dashboard, hoàn thành yêu cầu, nhận coins và rewards tự động.",
                    "tips": "Hoàn thành daily quests mỗi ngày để duy trì streak và nhận coins."
                },
                {
                    "name": "Achievements & Milestones",
                    "description": "Hệ thống thành tựu và milestone để theo dõi tiến độ",
                    "how_to": "Xem trong Hồ Sơ > Thành Tựu. Hoàn thành mục tiêu để unlock achievements.",
                    "tips": "Streak milestones cho rewards lớn. Long-term achievements cho mục tiêu dài hạn."
                }
            ]
        },
        {
            "category": "💰 Shop & Premium",
            "features": [
                {
                    "name": "Cửa Hàng",
                    "path": "pages/11_Cua_Hang.py",
                    "description": "Mua items, badges, frames, titles bằng coins",
                    "how_to": "Browse items, click 'Mua' nếu đủ coins, item sẽ được thêm vào inventory.",
                    "tips": "Kiếm coins bằng cách học tập và hoàn thành quests. Items giúp customize profile."
                },
                {
                    "name": "Premium Plans",
                    "path": "pages/15_Premium.py",
                    "description": "Nâng cấp tài khoản để có nhiều tính năng và giới hạn cao hơn",
                    "how_to": "Chọn gói (Basic/Premium/Pro), xem so sánh, thanh toán để nâng cấp.",
                    "how_to_detail": """
                    **Gói Basic (39k/tháng):**
                    - 300 lượt AI/tháng
                    - Không giới hạn từ vựng/ngày
                    - Export data
                    
                    **Gói Premium (49k/tháng):**
                    - 600 lượt AI/tháng
                    - Analytics dashboard
                    - Tất cả tính năng Basic
                    
                    **Gói Pro (69k/tháng):**
                    - 1200 lượt AI/tháng
                    - Ưu tiên support
                    - Tất cả tính năng Premium
                    
                    **Top-up AI:** Free users cũng có thể mua thêm lượt AI khi cần.
                    """,
                    "tips": "Bắt đầu với Free để trải nghiệm. Nâng cấp khi cần nhiều tính năng hơn."
                }
            ]
        },
        {
            "category": "📊 Theo Dõi & Quản Lý",
            "features": [
                {
                    "name": "Dashboard",
                    "description": "Trang chủ với overview tiến độ, stats, leaderboard, quests",
                    "how_to": "Xem ngay khi đăng nhập. Dashboard cập nhật real-time tiến độ học tập.",
                    "tips": "Check dashboard mỗi ngày để theo dõi streak và tiến độ."
                },
                {
                    "name": "Analytics (Premium)",
                    "path": "pages/16_Analytics.py",
                    "description": "Phân tích chi tiết tiến độ học tập với charts và insights",
                    "how_to": "Chỉ dành cho Premium users. Xem vocabulary progress, skills progress, activity heatmap, etc.",
                    "tips": "Sử dụng analytics để xác định điểm mạnh/yếu và điều chỉnh lộ trình học."
                },
                {
                    "name": "Hồ Sơ",
                    "path": "pages/10_Ho_So.py",
                    "description": "Xem profile, achievements, badges, stats chi tiết",
                    "how_to": "Truy cập từ menu. Xem các tabs: Thành Tựu, Thành Tựu Dài Hạn, Streak Milestones, Biểu Đồ, Lịch Sử Thi.",
                    "tips": "Customize profile với badges và frames từ shop."
                },
                {
                    "name": "Learning Insights (AI)",
                    "description": "AI phân tích điểm mạnh/yếu và đề xuất lộ trình học",
                    "how_to": "Xem trên Dashboard. AI tự động phân tích dữ liệu học tập và đưa ra recommendations.",
                    "tips": "Làm theo recommendations để học hiệu quả hơn."
                }
            ]
        },
        {
            "category": "⚙️ Cài Đặt & Hỗ Trợ",
            "features": [
                {
                    "name": "Cài Đặt",
                    "path": "pages/12_Cai_Dat.py",
                    "description": "Tùy chỉnh cài đặt app, profile, notifications",
                    "how_to": "Truy cập từ menu, thay đổi settings, save changes.",
                    "tips": "Cấu hình notifications để không bỏ lỡ quests và reminders."
                },
                {
                    "name": "Góp Ý",
                    "path": "pages/14_Gop_Y.py",
                    "description": "Gửi feedback, báo lỗi, đề xuất tính năng mới",
                    "how_to": "Điền form feedback, gửi. Admin sẽ xem và phản hồi.",
                    "tips": "Feedback giúp cải thiện app. Hãy chia sẻ ý kiến của bạn!"
                }
            ]
        }
    ]
    
    # Display features
    for category_data in features_data:
        with st.expander(category_data["category"], expanded=True):
            for feature in category_data["features"]:
                st.markdown(f"### {feature['name']}")
                st.markdown(f"**Mô tả:** {feature['description']}")
                
                if 'how_to_detail' in feature:
                    st.markdown("**Cách sử dụng:**")
                    st.markdown(feature['how_to_detail'])
                elif 'how_to' in feature:
                    st.markdown(f"**Cách sử dụng:** {feature['how_to']}")
                
                if 'tips' in feature:
                    st.info(f"💡 **Tips:** {feature['tips']}")
                
                st.divider()

# ========== TAB 3: HƯỚNG DẪN CHI TIẾT ==========
with tab_tutorials:
    st.header("🎓 Hướng Dẫn Chi Tiết Từng Bước")
    
    tutorials = [
        {
            "title": "🚀 Bắt Đầu: Đăng Ký & Kiểm Tra Đầu Vào",
            "steps": [
                "1. Truy cập trang chủ, click 'Đăng Ký'",
                "2. Điền thông tin: username, email, password",
                "3. Xác nhận email (nếu có)",
                "4. Đăng nhập lần đầu",
                "5. Làm bài 'Kiểm Tra Đầu Vào' để xác định trình độ",
                "6. Xem kết quả và lộ trình học được đề xuất"
            ],
            "video": False  # Có thể thêm link video sau
        },
        {
            "title": "📚 Học Từ Vựng Hiệu Quả",
            "steps": [
                "1. Vào 'Kho Từ Vựng'",
                "2. Chọn level và chủ đề phù hợp (bắt đầu với A1-A2)",
                "3. Xem từ vựng: word, meaning, example, pronunciation",
                "4. Click 'Thêm vào danh sách học' cho từ muốn học",
                "5. Học tối đa 20 từ/ngày (Free) hoặc không giới hạn (Premium)",
                "6. Sử dụng 'Ôn Tập SRS' mỗi ngày để ghi nhớ",
                "7. Đánh giá chính xác mức độ nhớ khi ôn tập"
            ]
        },
        {
            "title": "🔄 Sử Dụng Hệ Thống SRS (Spaced Repetition)",
            "steps": [
                "1. Vào 'Ôn Tập' hàng ngày",
                "2. Xem danh sách từ cần ôn (sắp xếp tự động)",
                "3. Xem từ và nghĩa, nhớ lại",
                "4. Chọn mức độ nhớ:",
                "   - ⭐⭐⭐ Dễ: Từ sẽ xuất hiện lại sau 4 ngày",
                "   - ⭐⭐ Nhớ: Từ sẽ xuất hiện lại sau 2 ngày",
                "   - ⭐ Khó: Từ sẽ xuất hiện lại ngay hôm sau",
                "   - ❌ Quên: Từ sẽ xuất hiện lại ngay hôm sau",
                "5. Hệ thống tự động tính toán lịch ôn tập tối ưu",
                "6. Duy trì ôn tập đều đặn để đạt hiệu quả tốt nhất"
            ]
        },
        {
            "title": "🎧 Luyện Nghe với Podcast",
            "steps": [
                "1. Vào 'Luyện Nghe' > Tab 'Podcast'",
                "2. Chọn chủ đề hoặc để AI tự chọn",
                "3. Click 'Tạo Podcast' và đợi AI generate (30-60 giây)",
                "4. Nghe podcast (5-7 phút)",
                "5. Đọc transcript để hiểu nội dung",
                "6. Xem vocabulary highlights và học từ mới",
                "7. Lưu ý: Free users có 5 lượt/tính năng/ngày"
            ]
        },
        {
            "title": "🎤 Luyện Nói & Phát Âm",
            "steps": [
                "1. Vào 'Luyện Nói'",
                "2. Chọn level bài luyện",
                "3. Nghe câu mẫu (click play)",
                "4. Nhấn nút 'Bắt đầu ghi âm'",
                "5. Nói câu đó (rõ ràng, đúng tốc độ)",
                "6. Nhấn 'Dừng ghi âm'",
                "7. Xem kết quả: accuracy score và feedback",
                "8. Lặp lại cho đến khi đạt điểm cao"
            ]
        },
        {
            "title": "✍️ Luyện Viết với AI Feedback",
            "steps": [
                "1. Vào 'Luyện Viết'",
                "2. Chọn chủ đề hoặc đề bài",
                "3. Viết bài (tối thiểu 50-100 từ tùy yêu cầu)",
                "4. Click 'Gửi bài' và đợi AI đánh giá (10-20 giây)",
                "5. Xem feedback chi tiết:",
                "   - Ngữ pháp (grammar errors)",
                "   - Từ vựng (vocabulary suggestions)",
                "   - Style và coherence",
                "6. Sửa bài dựa trên feedback",
                "7. Gửi lại để được đánh giá tiếp"
            ]
        },
        {
            "title": "📊 Theo Dõi Tiến Độ với Analytics (Premium)",
            "steps": [
                "1. Nâng cấp lên Premium để truy cập Analytics",
                "2. Vào 'Analytics' từ menu",
                "3. Xem Overview Stats: tổng quan tiến độ",
                "4. Vocabulary Progress: biểu đồ từ vựng đã học",
                "5. Skills Progress: tiến độ 4 kỹ năng",
                "6. Activity Heatmap: hoạt động theo ngày",
                "7. Topics Progress: tiến độ theo chủ đề",
                "8. Level Progress: tiến độ theo level (A1-C2)",
                "9. AI Usage: thống kê sử dụng AI",
                "10. Export data ra CSV/PDF nếu cần"
            ]
        },
        {
            "title": "🏆 Hoàn Thành Quests & Nhận Rewards",
            "steps": [
                "1. Xem Daily Quests trên Dashboard mỗi ngày",
                "2. Các quest thường gồm:",
                "   - Học X từ vựng mới",
                "   - Ôn tập X từ",
                "   - Hoàn thành X bài nghe/nói/đọc/viết",
                "   - Duy trì streak",
                "3. Hoàn thành quests để nhận coins",
                "4. Weekly Quests cho rewards lớn hơn",
                "5. Duy trì streak để không mất tiến độ"
            ]
        },
        {
            "title": "⚔️ Tham Gia Đấu Trường (PvP)",
            "steps": [
                "1. Vào 'Đấu Trường'",
                "2. Xem danh sách challenges mở",
                "3. Chấp nhận challenge hoặc tạo challenge mới",
                "4. Làm bài thi trong thời gian quy định",
                "5. Xem kết quả và so sánh với đối thủ",
                "6. Người thắng nhận coins và tăng ranking",
                "7. Xem leaderboard để biết vị trí của mình"
            ]
        },
        {
            "title": "💰 Quản Lý Coins & Mua Items",
            "steps": [
                "1. Kiếm coins bằng cách:",
                "   - Học từ vựng (1 coin/từ mới)",
                "   - Hoàn thành quests",
                "   - Thắng PvP",
                "   - Đạt achievements và milestones",
                "2. Vào 'Cửa Hàng' để mua items:",
                "   - Badges (huy hiệu)",
                "   - Frames (khung avatar)",
                "   - Titles (danh hiệu)",
                "   - Power-ups (tạm thời)",
                "3. Items sẽ được thêm vào Inventory",
                "4. Vào 'Hồ Sơ' để active items"
            ]
        },
        {
            "title": "⭐ Nâng Cấp Premium",
            "steps": [
                "1. Vào 'Gói Dịch Vụ' (Premium) từ menu",
                "2. So sánh các gói: Free, Basic, Premium, Pro",
                "3. Chọn gói phù hợp với nhu cầu",
                "4. Click 'Nâng Cấp' và thanh toán",
                "5. Tài khoản được nâng cấp ngay lập tức",
                "6. Nếu hết lượt AI, có thể mua Top-up",
                "7. Free users cũng có thể mua Top-up"
            ]
        }
    ]
    
    for tutorial in tutorials:
        with st.expander(tutorial["title"], expanded=False):
            st.markdown("**Các bước thực hiện:**")
            for step in tutorial["steps"]:
                st.markdown(f"- {step}")
            if tutorial.get("video"):
                st.video(tutorial["video"])

# ========== TAB 4: Q&A ==========
with tab_qa:
    st.header("❓ Câu Hỏi Thường Gặp (FAQ)")
    
    faq_categories = [
        {
            "category": "🚀 Bắt Đầu",
            "questions": [
                {
                    "q": "Làm sao để đăng ký tài khoản?",
                    "a": "Click nút 'Đăng Ký' trên trang chủ, điền username, email, password. Sau đó đăng nhập và làm bài kiểm tra đầu vào."
                },
                {
                    "q": "Tôi có thể đổi mật khẩu không?",
                    "a": "Có, vào 'Cài Đặt' > 'Đổi mật khẩu' để thay đổi password."
                },
                {
                    "q": "Kiểm tra đầu vào mất bao lâu?",
                    "a": "Khoảng 10-15 phút. Bạn cần trả lời các câu hỏi để AI đánh giá trình độ."
                },
                {
                    "q": "Tôi có thể làm lại kiểm tra đầu vào không?",
                    "a": "Có, nhưng phải đợi 30 ngày kể từ lần làm trước để có kết quả chính xác."
                }
            ]
        },
        {
            "category": "📚 Học Tập",
            "questions": [
                {
                    "q": "SRS là gì và tại sao quan trọng?",
                    "a": "SRS (Spaced Repetition System) là hệ thống lặp lại ngắt quãng - phương pháp khoa học giúp ghi nhớ từ vựng lâu dài. Hệ thống tự động nhắc bạn ôn tập từ vựng vào thời điểm tối ưu dựa trên mức độ nhớ của bạn."
                },
                {
                    "q": "Tôi nên học bao nhiêu từ vựng mỗi ngày?",
                    "a": "Khuyến nghị: 10-20 từ mới/ngày cho người mới bắt đầu, 20-30 từ/ngày cho người đã có nền tảng. Quan trọng là ôn tập đều đặn, không chỉ học từ mới."
                },
                {
                    "q": "Làm sao để học từ vựng hiệu quả?",
                    "a": """
                    - Học từ theo chủ đề và ngữ cảnh
                    - Sử dụng SRS để ôn tập đều đặn
                    - Học cả pronunciation và example sentences
                    - Áp dụng từ vựng vào speaking và writing
                    - Đánh giá chính xác mức độ nhớ khi ôn tập
                    """
                },
                {
                    "q": "Tại sao từ vựng tôi đã học lại xuất hiện trong ôn tập?",
                    "a": "Đây là tính năng của SRS. Từ vựng cần được ôn tập nhiều lần với khoảng cách tăng dần để ghi nhớ lâu dài. Nếu bạn đánh giá 'Dễ', từ sẽ xuất hiện lại sau 4 ngày hoặc lâu hơn."
                },
                {
                    "q": "Tôi có thể học ngữ pháp mà không học từ vựng không?",
                    "a": "Không nên. Từ vựng và ngữ pháp bổ sung cho nhau. Học song song cả hai sẽ hiệu quả hơn."
                }
            ]
        },
        {
            "category": "🤖 AI Features",
            "questions": [
                {
                    "q": "Lượt AI là gì và được tính như thế nào?",
                    "a": "Mỗi lần sử dụng tính năng AI (generate podcast, dictation, writing feedback, etc.) được tính là 1 lượt. Free: 5 lượt/tính năng/ngày. Premium: 600-1200 lượt/tháng tùy gói."
                },
                {
                    "q": "Tôi hết lượt AI thì làm sao?",
                    "a": "Bạn có thể: (1) Đợi đến ngày mai để reset (Free), (2) Nâng cấp Premium để có nhiều lượt hơn, (3) Mua Top-up AI ngay cả khi là Free user."
                },
                {
                    "q": "AI có chính xác không?",
                    "a": "AI của chúng tôi sử dụng công nghệ tiên tiến (Gemini) và được cải thiện liên tục. Tuy nhiên, bạn nên tham khảo thêm từ các nguồn khác để đảm bảo tính chính xác."
                },
                {
                    "q": "Tại sao generate podcast mất nhiều thời gian?",
                    "a": "AI cần time để generate nội dung chất lượng (5-7 phút audio) và convert sang speech. Thường mất 30-60 giây. Vui lòng kiên nhẫn."
                }
            ]
        },
        {
            "category": "💰 Premium & Pricing",
            "questions": [
                {
                    "q": "Sự khác biệt giữa Free và Premium là gì?",
                    "a": """
                    **Free:**
                    - 5 lượt AI/tính năng/ngày (tổng 20 lượt/ngày)
                    - 20 từ vựng/ngày
                    - Không có Analytics
                    - Không export data
                    
                    **Premium (Basic/Premium/Pro):**
                    - 300/600/1200 lượt AI/tháng
                    - Không giới hạn từ vựng
                    - Analytics dashboard chi tiết
                    - Export data (CSV/PDF)
                    - Ưu tiên support (Pro)
                    """
                },
                {
                    "q": "Tôi có thể hủy Premium bất cứ lúc nào không?",
                    "a": "Có, bạn có thể hủy subscription bất cứ lúc nào. Tài khoản sẽ về Free sau khi hết hạn đã thanh toán."
                },
                {
                    "q": "Coins có mất khi hết hạn không?",
                    "a": "Không, coins của bạn được lưu vĩnh viễn và không bao giờ mất."
                },
                {
                    "q": "Top-up AI là gì?",
                    "a": "Top-up AI là gói mua thêm lượt AI khi bạn hết limit. Có thể mua ngay cả khi là Free user. Top-up sẽ hết hạn vào cuối tháng."
                }
            ]
        },
        {
            "category": "🎮 Gamification",
            "questions": [
                {
                    "q": "Streak là gì và làm sao để duy trì?",
                    "a": "Streak là số ngày học liên tiếp. Để duy trì: học ít nhất 10 từ mới hoặc ôn tập ít nhất 10 từ mỗi ngày. Mất streak nếu không học trong 1 ngày."
                },
                {
                    "q": "Làm sao để kiếm nhiều coins?",
                    "a": """
                    - Học từ vựng mới (1 coin/từ)
                    - Hoàn thành daily/weekly quests
                    - Duy trì streak và đạt milestones
                    - Thắng PvP challenges
                    - Đạt achievements
                    """
                },
                {
                    "q": "Achievements và Milestones khác nhau như thế nào?",
                    "a": "Milestones là rewards cho streak (7, 14, 30 ngày...). Achievements là thành tựu dài hạn (học 1000 từ, hoàn thành 100 bài nghe...)."
                },
                {
                    "q": "Tôi có thể thách đấu bất kỳ ai không?",
                    "a": "Bạn có thể tạo challenge cho bất kỳ user nào, nhưng họ phải chấp nhận. Bạn cũng có thể chấp nhận challenges từ người khác."
                }
            ]
        },
        {
            "category": "📊 Analytics & Progress",
            "questions": [
                {
                    "q": "Tôi có thể xem tiến độ chi tiết không?",
                    "a": "Có, Premium users có thể xem Analytics dashboard với charts chi tiết. Free users có thể xem basic stats trên Dashboard và Hồ Sơ."
                },
                {
                    "q": "Làm sao để export dữ liệu học tập?",
                    "a": "Premium users: vào Analytics > Export, chọn CSV hoặc PDF. Hoặc vào Kho Từ Vựng > Export để tải vocabulary list."
                },
                {
                    "q": "Learning Insights là gì?",
                    "a": "AI tự động phân tích điểm mạnh/yếu của bạn và đưa ra recommendations về lộ trình học. Xem trên Dashboard."
                }
            ]
        },
        {
            "category": "🐛 Technical Issues",
            "questions": [
                {
                    "q": "App bị lỗi, tôi phải làm gì?",
                    "a": "Vào 'Góp ý' để báo lỗi chi tiết. Hoặc liên hệ support nếu là Premium user."
                },
                {
                    "q": "Tôi quên mật khẩu thì sao?",
                    "a": "Click 'Quên mật khẩu' trên trang đăng nhập, nhập email để nhận link reset password."
                },
                {
                    "q": "Tại sao audio không phát được?",
                    "a": "Kiểm tra volume, cho phép browser access microphone/speaker. Thử refresh page hoặc đổi browser."
                },
                {
                    "q": "Tôi không thấy tính năng X?",
                    "a": "Một số tính năng chỉ dành cho Premium users. Kiểm tra lại plan của bạn. Nếu vẫn không thấy, báo lỗi qua 'Góp ý'."
                }
            ]
        },
        {
            "category": "💡 Tips & Best Practices",
            "questions": [
                {
                    "q": "Lộ trình học tối ưu là gì?",
                    "a": """
                    **Người mới:**
                    1. Kiểm tra đầu vào
                    2. Học từ vựng (10-20 từ/ngày) + SRS
                    3. Ngữ pháp A1
                    4. Luyện nghe cơ bản
                    5. Duy trì streak
                    
                    **Có nền tảng:**
                    - Tập trung vào Speaking & Writing
                    - Làm mock tests định kỳ
                    - Tham gia PvP
                    - Học từ vựng nâng cao
                    """
                },
                {
                    "q": "Tôi nên dành bao nhiêu thời gian học mỗi ngày?",
                    "a": "Khuyến nghị: ít nhất 15-30 phút/ngày để duy trì streak và tiến bộ. 1-2 giờ/ngày cho tiến bộ nhanh."
                },
                {
                    "q": "Làm sao để không chán khi học?",
                    "a": """
                    - Đa dạng hoạt động: không chỉ học từ vựng
                    - Tham gia PvP và quests
                    - Đặt mục tiêu nhỏ và đạt achievements
                    - Sử dụng items từ shop để customize profile
                    - Theo dõi tiến độ để thấy sự cải thiện
                    """
                },
                {
                    "q": "Tôi có nên học nhiều chủ đề cùng lúc không?",
                    "a": "Nên học 2-3 chủ đề cùng lúc để đa dạng, nhưng đừng quá nhiều để tránh loãng kiến thức."
                }
            ]
        }
    ]
    
    # Display Q&A
    for category in faq_categories:
        with st.expander(category["category"], expanded=False):
            for item in category["questions"]:
                st.markdown(f"**Q: {item['q']}**")
                st.markdown(f"A: {item['a']}")
                st.divider()

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>📚 <strong>English Master</strong> - Học Tiếng Anh Từ Zero</p>
    <p>Nếu bạn có câu hỏi khác, vui lòng vào <strong>Góp ý</strong> để liên hệ với chúng tôi.</p>
</div>
""", unsafe_allow_html=True)
