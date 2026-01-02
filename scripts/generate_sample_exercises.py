"""
Script để generate 10 mẫu exercise cho mỗi chức năng và lưu vào database.
Dùng để test tính năng caching và xem tốc độ load.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import supabase
from services.exercise_cache_service import VALID_TOPICS, save_exercise
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data templates
SAMPLE_EXERCISES = {
    "dictation": [
        {
            "level": "A1",
            "topic": "Daily Life",
            "exercise_data": {"text": "I go to school every day.", "translation": "Tôi đi học mỗi ngày."}
        },
        {
            "level": "A1",
            "topic": "Daily Life",
            "exercise_data": {"text": "She likes to read books.", "translation": "Cô ấy thích đọc sách."}
        },
        {
            "level": "A1",
            "topic": "Food & Cooking",
            "exercise_data": {"text": "I eat breakfast at seven o'clock.", "translation": "Tôi ăn sáng lúc bảy giờ."}
        },
        {
            "level": "A2",
            "topic": "Travel",
            "exercise_data": {"text": "We are going to visit Paris next month.", "translation": "Chúng tôi sẽ thăm Paris tháng tới."}
        },
        {
            "level": "A2",
            "topic": "Travel",
            "exercise_data": {"text": "The hotel is near the beach.", "translation": "Khách sạn gần bãi biển."}
        },
        {
            "level": "B1",
            "topic": "Business",
            "exercise_data": {"text": "The meeting has been postponed until next week.", "translation": "Cuộc họp đã được hoãn đến tuần tới."}
        },
        {
            "level": "B1",
            "topic": "Work",
            "exercise_data": {"text": "I need to finish this report by Friday.", "translation": "Tôi cần hoàn thành báo cáo này trước thứ Sáu."}
        },
        {
            "level": "B2",
            "topic": "Technology",
            "exercise_data": {"text": "Artificial intelligence is transforming many industries.", "translation": "Trí tuệ nhân tạo đang biến đổi nhiều ngành công nghiệp."}
        },
        {
            "level": "B2",
            "topic": "Education",
            "exercise_data": {"text": "Students should develop critical thinking skills.", "translation": "Học sinh nên phát triển kỹ năng tư duy phản biện."}
        },
        {
            "level": "C1",
            "topic": "Science",
            "exercise_data": {"text": "The research findings challenge conventional wisdom.", "translation": "Những phát hiện nghiên cứu thách thức trí tuệ thông thường."}
        },
    ],
    "comprehension": [
        {
            "level": "A1",
            "topic": "Daily Life",
            "exercise_data": {
                "text": "Tom gets up at 6 o'clock every morning. He brushes his teeth and eats breakfast. Then he goes to school by bus.",
                "question": "What time does Tom get up?",
                "options": ["5 o'clock", "6 o'clock", "7 o'clock", "8 o'clock"],
                "answer": "6 o'clock",
                "explanation": "Đoạn văn nói rõ ràng Tom dậy lúc 6 giờ sáng mỗi ngày."
            }
        },
        {
            "level": "A1",
            "topic": "Daily Life",
            "exercise_data": {
                "text": "Sarah likes to cook. She makes dinner for her family every evening. Her favorite dish is pasta.",
                "question": "What is Sarah's favorite dish?",
                "options": ["Rice", "Pasta", "Bread", "Soup"],
                "answer": "Pasta",
                "explanation": "Đoạn văn nói rằng món ăn yêu thích của Sarah là pasta."
            }
        },
        {
            "level": "A2",
            "topic": "Travel",
            "exercise_data": {
                "text": "Last summer, we visited Japan. We saw beautiful temples and ate delicious food. The people were very friendly.",
                "question": "How were the people in Japan?",
                "options": ["Unfriendly", "Very friendly", "Busy", "Quiet"],
                "answer": "Very friendly",
                "explanation": "Đoạn văn mô tả người dân Nhật Bản rất thân thiện."
            }
        },
        {
            "level": "A2",
            "topic": "Shopping",
            "exercise_data": {
                "text": "I went shopping yesterday. I bought a new shirt and some shoes. The store was having a sale, so everything was cheaper.",
                "question": "Why was everything cheaper?",
                "options": ["It was a special day", "The store was having a sale", "The quality was poor", "The items were old"],
                "answer": "The store was having a sale",
                "explanation": "Đoạn văn giải thích rằng cửa hàng đang giảm giá nên mọi thứ rẻ hơn."
            }
        },
        {
            "level": "B1",
            "topic": "Business",
            "exercise_data": {
                "text": "Our company is expanding. We are opening new offices in three countries. This will create many job opportunities.",
                "question": "What will the expansion create?",
                "options": ["More problems", "Many job opportunities", "Higher costs", "Less work"],
                "answer": "Many job opportunities",
                "explanation": "Đoạn văn nói rằng việc mở rộng sẽ tạo ra nhiều cơ hội việc làm."
            }
        },
        {
            "level": "B1",
            "topic": "Health",
            "exercise_data": {
                "text": "Exercise is important for our health. Regular physical activity can help prevent diseases and improve mental well-being.",
                "question": "What can regular exercise help prevent?",
                "options": ["Diseases", "Sleep", "Work", "Food"],
                "answer": "Diseases",
                "explanation": "Đoạn văn nói rằng hoạt động thể chất thường xuyên có thể giúp ngăn ngừa bệnh tật."
            }
        },
        {
            "level": "B2",
            "topic": "Technology",
            "exercise_data": {
                "text": "Cloud computing allows businesses to store data remotely. This reduces the need for physical servers and saves costs.",
                "question": "What does cloud computing reduce the need for?",
                "options": ["Internet", "Physical servers", "Employees", "Software"],
                "answer": "Physical servers",
                "explanation": "Đoạn văn giải thích rằng điện toán đám mây giảm nhu cầu về máy chủ vật lý."
            }
        },
        {
            "level": "B2",
            "topic": "Education",
            "exercise_data": {
                "text": "Online learning has become more popular. Students can study from anywhere and access resources 24/7. However, it requires self-discipline.",
                "question": "What does online learning require?",
                "options": ["More money", "Self-discipline", "Physical presence", "Old technology"],
                "answer": "Self-discipline",
                "explanation": "Đoạn văn đề cập rằng học trực tuyến đòi hỏi tính tự giác."
            }
        },
        {
            "level": "C1",
            "topic": "Science",
            "exercise_data": {
                "text": "Quantum computing represents a paradigm shift in computational power. It leverages quantum mechanical phenomena to process information in fundamentally different ways.",
                "question": "What does quantum computing leverage?",
                "options": ["Traditional algorithms", "Quantum mechanical phenomena", "Simple calculations", "Old technology"],
                "answer": "Quantum mechanical phenomena",
                "explanation": "Đoạn văn giải thích rằng máy tính lượng tử sử dụng các hiện tượng cơ học lượng tử."
            }
        },
        {
            "level": "C1",
            "topic": "Environment",
            "exercise_data": {
                "text": "Climate change mitigation requires coordinated global action. Countries must reduce greenhouse gas emissions and transition to renewable energy sources.",
                "question": "What must countries reduce?",
                "options": ["Population", "Greenhouse gas emissions", "Education", "Healthcare"],
                "answer": "Greenhouse gas emissions",
                "explanation": "Đoạn văn nói rằng các quốc gia phải giảm lượng khí thải nhà kính."
            }
        },
    ],
    "reading_question": [
        {
            "level": "A1",
            "topic": "Daily Life",
            "exercise_data": {
                "english_content": "My name is Anna. I am a student. I live in a small house with my family. I have two brothers and one sister. We like to play together.",
                "vietnamese_content": "Tên tôi là Anna. Tôi là học sinh. Tôi sống trong một ngôi nhà nhỏ với gia đình. Tôi có hai anh trai và một chị gái. Chúng tôi thích chơi cùng nhau.",
                "summary": "Anna introduces herself and her family.",
                "vocabulary": [
                    {"word": "student", "type": "noun", "meaning": "học sinh", "context": "I am a student."}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "How many brothers does Anna have?", "options": ["One", "Two", "Three", "Four"], "answer": "Two", "explanation": "Anna có hai anh trai."}
                ]
            }
        },
        {
            "level": "A2",
            "topic": "Travel",
            "exercise_data": {
                "english_content": "Last weekend, I visited the mountains. The weather was perfect. I took many photos and went hiking. It was a wonderful experience.",
                "vietnamese_content": "Cuối tuần trước, tôi đã thăm núi. Thời tiết rất đẹp. Tôi chụp nhiều ảnh và đi bộ đường dài. Đó là một trải nghiệm tuyệt vời.",
                "summary": "A weekend trip to the mountains with perfect weather.",
                "vocabulary": [
                    {"word": "hiking", "type": "noun", "meaning": "đi bộ đường dài", "context": "I went hiking."}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "What did the author do last weekend?", "options": ["Visited the beach", "Visited the mountains", "Stayed home", "Went shopping"], "answer": "Visited the mountains", "explanation": "Tác giả đã thăm núi cuối tuần trước."}
                ]
            }
        },
        {
            "level": "B1",
            "topic": "Business",
            "exercise_data": {
                "english_content": "Remote work has changed how businesses operate. Companies now hire talent from anywhere in the world. This increases diversity and brings new perspectives.",
                "vietnamese_content": "Làm việc từ xa đã thay đổi cách các doanh nghiệp hoạt động. Các công ty giờ đây tuyển dụng nhân tài từ khắp nơi trên thế giới. Điều này tăng tính đa dạng và mang đến những góc nhìn mới.",
                "summary": "Remote work enables global hiring and diversity.",
                "vocabulary": [
                    {"word": "remote", "type": "adjective", "meaning": "từ xa", "context": "Remote work has changed..."}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "What does remote work increase?", "options": ["Costs", "Diversity", "Problems", "Hours"], "answer": "Diversity", "explanation": "Làm việc từ xa tăng tính đa dạng."}
                ]
            }
        },
        {
            "level": "B2",
            "topic": "Technology",
            "exercise_data": {
                "english_content": "Artificial intelligence is revolutionizing healthcare. AI can analyze medical images faster than humans. It helps doctors make more accurate diagnoses.",
                "vietnamese_content": "Trí tuệ nhân tạo đang cách mạng hóa chăm sóc sức khỏe. AI có thể phân tích hình ảnh y tế nhanh hơn con người. Nó giúp bác sĩ chẩn đoán chính xác hơn.",
                "summary": "AI improves healthcare through faster image analysis.",
                "vocabulary": [
                    {"word": "diagnoses", "type": "noun", "meaning": "chẩn đoán", "context": "make more accurate diagnoses"}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "What can AI analyze faster than humans?", "options": ["Books", "Medical images", "Music", "Food"], "answer": "Medical images", "explanation": "AI có thể phân tích hình ảnh y tế nhanh hơn con người."}
                ]
            }
        },
        {
            "level": "C1",
            "topic": "Science",
            "exercise_data": {
                "english_content": "The discovery of exoplanets has expanded our understanding of the universe. Scientists have found thousands of planets orbiting distant stars, some potentially habitable.",
                "vietnamese_content": "Việc phát hiện các hành tinh ngoài hệ mặt trời đã mở rộng hiểu biết của chúng ta về vũ trụ. Các nhà khoa học đã tìm thấy hàng nghìn hành tinh quay quanh các ngôi sao xa xôi, một số có thể có sự sống.",
                "summary": "Exoplanet discoveries reveal potentially habitable worlds.",
                "vocabulary": [
                    {"word": "exoplanets", "type": "noun", "meaning": "hành tinh ngoài hệ mặt trời", "context": "The discovery of exoplanets"}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "What have scientists found orbiting distant stars?", "options": ["Asteroids", "Thousands of planets", "Moons", "Comets"], "answer": "Thousands of planets", "explanation": "Các nhà khoa học đã tìm thấy hàng nghìn hành tinh."}
                ]
            }
        },
        # Add 5 more samples
        {
            "level": "A1",
            "topic": "Food & Cooking",
            "exercise_data": {
                "english_content": "I like to cook pasta. First, I boil water. Then I add the pasta. After ten minutes, I drain the water and add sauce.",
                "vietnamese_content": "Tôi thích nấu mì ống. Đầu tiên, tôi đun sôi nước. Sau đó tôi cho mì vào. Sau mười phút, tôi đổ nước và thêm nước sốt.",
                "summary": "Simple steps to cook pasta.",
                "vocabulary": [
                    {"word": "drain", "type": "verb", "meaning": "đổ, rót", "context": "I drain the water"}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "What do you add after draining the water?", "options": ["Salt", "Sauce", "Oil", "Sugar"], "answer": "Sauce", "explanation": "Sau khi đổ nước, bạn thêm nước sốt."}
                ]
            }
        },
        {
            "level": "A2",
            "topic": "Sports & Fitness",
            "exercise_data": {
                "english_content": "Running is good for your health. It strengthens your heart and improves your mood. You should start slowly and increase gradually.",
                "vietnamese_content": "Chạy bộ tốt cho sức khỏe của bạn. Nó tăng cường tim mạch và cải thiện tâm trạng. Bạn nên bắt đầu chậm và tăng dần.",
                "summary": "Benefits of running and how to start.",
                "vocabulary": [
                    {"word": "gradually", "type": "adverb", "meaning": "dần dần", "context": "increase gradually"}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "What does running strengthen?", "options": ["Your brain", "Your heart", "Your bones", "Your skin"], "answer": "Your heart", "explanation": "Chạy bộ tăng cường tim mạch."}
                ]
            }
        },
        {
            "level": "B1",
            "topic": "Environment",
            "exercise_data": {
                "english_content": "Recycling helps protect the environment. When we recycle, we reduce waste and save energy. Everyone can contribute by separating their trash.",
                "vietnamese_content": "Tái chế giúp bảo vệ môi trường. Khi chúng ta tái chế, chúng ta giảm rác thải và tiết kiệm năng lượng. Mọi người có thể đóng góp bằng cách phân loại rác.",
                "summary": "How recycling protects the environment.",
                "vocabulary": [
                    {"word": "recycling", "type": "noun", "meaning": "tái chế", "context": "Recycling helps protect"}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "How can everyone contribute to recycling?", "options": ["By buying more", "By separating their trash", "By throwing away more", "By using more energy"], "answer": "By separating their trash", "explanation": "Mọi người có thể đóng góp bằng cách phân loại rác."}
                ]
            }
        },
        {
            "level": "B2",
            "topic": "Culture",
            "exercise_data": {
                "english_content": "Festivals celebrate cultural heritage. They bring communities together and preserve traditions. Many festivals have been celebrated for centuries.",
                "vietnamese_content": "Lễ hội tôn vinh di sản văn hóa. Chúng kết nối cộng đồng và bảo tồn truyền thống. Nhiều lễ hội đã được tổ chức trong nhiều thế kỷ.",
                "summary": "The role of festivals in preserving culture.",
                "vocabulary": [
                    {"word": "heritage", "type": "noun", "meaning": "di sản", "context": "cultural heritage"}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "What do festivals preserve?", "options": ["Money", "Traditions", "Buildings", "Food"], "answer": "Traditions", "explanation": "Lễ hội bảo tồn truyền thống."}
                ]
            }
        },
        {
            "level": "C1",
            "topic": "History",
            "exercise_data": {
                "english_content": "The Renaissance marked a cultural transformation in Europe. It emphasized humanism, art, and scientific inquiry, laying foundations for modern thought.",
                "vietnamese_content": "Thời Phục hưng đánh dấu một sự chuyển đổi văn hóa ở châu Âu. Nó nhấn mạnh chủ nghĩa nhân văn, nghệ thuật và nghiên cứu khoa học, đặt nền móng cho tư duy hiện đại.",
                "summary": "The Renaissance as a cultural and intellectual movement.",
                "vocabulary": [
                    {"word": "Renaissance", "type": "noun", "meaning": "thời Phục hưng", "context": "The Renaissance marked"}
                ],
                "grammar": [],
                "quiz": [
                    {"question": "What did the Renaissance emphasize?", "options": ["War", "Humanism, art, and scientific inquiry", "Trade", "Religion"], "answer": "Humanism, art, and scientific inquiry", "explanation": "Thời Phục hưng nhấn mạnh chủ nghĩa nhân văn, nghệ thuật và nghiên cứu khoa học."}
                ]
            }
        },
    ],
    "grammar_question": [
        {
            "level": "A1",
            "topic": None,
            "exercise_data": {
                "question": "I ___ to school every day.",
                "options": ["go", "goes", "going", "went"],
                "answer": "go",
                "explanation": "Với chủ ngữ 'I', động từ ở dạng nguyên thể (go).",
                "lesson_code": "A1_U1"
            }
        },
        {
            "level": "A1",
            "topic": None,
            "exercise_data": {
                "question": "She ___ English very well.",
                "options": ["speak", "speaks", "speaking", "spoke"],
                "answer": "speaks",
                "explanation": "Với chủ ngữ số ít 'She', động từ phải thêm 's' (speaks).",
                "lesson_code": "A1_U1"
            }
        },
        {
            "level": "A2",
            "topic": None,
            "exercise_data": {
                "question": "I ___ my homework yesterday.",
                "options": ["do", "did", "does", "doing"],
                "answer": "did",
                "explanation": "Với 'yesterday', ta dùng thì quá khứ đơn. 'Do' → 'did'.",
                "lesson_code": "A2_U1"
            }
        },
        {
            "level": "A2",
            "topic": None,
            "exercise_data": {
                "question": "They ___ playing soccer now.",
                "options": ["is", "are", "am", "be"],
                "answer": "are",
                "explanation": "Với chủ ngữ số nhiều 'They' và 'now', ta dùng 'are' + V-ing.",
                "lesson_code": "A2_U2"
            }
        },
        {
            "level": "B1",
            "topic": None,
            "exercise_data": {
                "question": "If it ___ tomorrow, we will stay home.",
                "options": ["rain", "rains", "will rain", "rained"],
                "answer": "rains",
                "explanation": "Câu điều kiện loại 1: If + S + V(s/es), S + will + V.",
                "lesson_code": "B1_U1"
            }
        },
        {
            "level": "B1",
            "topic": None,
            "exercise_data": {
                "question": "She has ___ this book three times.",
                "options": ["read", "reads", "reading", "red"],
                "answer": "read",
                "explanation": "Với 'has', ta dùng past participle. 'Read' (quá khứ) = 'read' (phát âm khác).",
                "lesson_code": "B1_U2"
            }
        },
        {
            "level": "B2",
            "topic": None,
            "exercise_data": {
                "question": "The report ___ by the manager yesterday.",
                "options": ["was written", "is written", "writes", "wrote"],
                "answer": "was written",
                "explanation": "Câu bị động quá khứ: was/were + past participle. 'Yesterday' → quá khứ.",
                "lesson_code": "B2_U1"
            }
        },
        {
            "level": "B2",
            "topic": None,
            "exercise_data": {
                "question": "He suggested ___ early to avoid traffic.",
                "options": ["leaving", "to leave", "leave", "left"],
                "answer": "leaving",
                "explanation": "Sau 'suggest', ta dùng V-ing, không dùng 'to V'.",
                "lesson_code": "B2_U2"
            }
        },
        {
            "level": "C1",
            "topic": None,
            "exercise_data": {
                "question": "Had I known earlier, I ___ differently.",
                "options": ["would act", "would have acted", "acted", "will act"],
                "answer": "would have acted",
                "explanation": "Câu điều kiện loại 3: Had + S + V3, S + would have + V3.",
                "lesson_code": "C1_U1"
            }
        },
        {
            "level": "C1",
            "topic": None,
            "exercise_data": {
                "question": "Not only ___ late, but he also forgot the documents.",
                "options": ["he was", "was he", "he is", "is he"],
                "answer": "was he",
                "explanation": "Với 'Not only' ở đầu câu, ta đảo ngữ: Not only + V + S.",
                "lesson_code": "C1_U2"
            }
        },
    ],
    "podcast_script": [
        {
            "level": "A2",
            "topic": None,  # Podcast topics are free-text
            "exercise_data": {
                "script": "Welcome to today's podcast. We're talking about healthy eating. Eating fruits and vegetables is important. They give us vitamins and energy. Try to eat five servings every day.",
                "pod_topic": "Healthy Eating",
                "pod_duration": "Ngắn (2-3 phút)",
                "target_words": ["healthy", "vegetables", "vitamins", "energy", "servings"]
            },
            "metadata": {"target_words": ["healthy", "vegetables", "vitamins", "energy", "servings"]}
        },
        {
            "level": "B1",
            "topic": None,
            "exercise_data": {
                "script": "Hello and welcome. Today we explore the world of remote work. Many companies now allow employees to work from home. This offers flexibility and can improve work-life balance. However, it requires good time management and communication skills.",
                "pod_topic": "Remote Work",
                "pod_duration": "Trung bình (3-5 phút)",
                "target_words": ["remote", "flexibility", "balance", "management", "communication"]
            },
            "metadata": {"target_words": ["remote", "flexibility", "balance", "management", "communication"]}
        },
        {
            "level": "B1",
            "topic": None,
            "exercise_data": {
                "script": "In this episode, we discuss climate change. Global temperatures are rising. This affects weather patterns worldwide. We all need to take action to reduce our carbon footprint.",
                "pod_topic": "Climate Change",
                "pod_duration": "Ngắn (2-3 phút)",
                "target_words": ["climate", "temperatures", "patterns", "footprint"]
            },
            "metadata": {"target_words": ["climate", "temperatures", "patterns", "footprint"]}
        },
        {
            "level": "B2",
            "topic": None,
            "exercise_data": {
                "script": "Welcome to our podcast about artificial intelligence. AI is transforming industries from healthcare to finance. Machine learning algorithms can analyze vast amounts of data. This enables better decision-making and innovation.",
                "pod_topic": "Artificial Intelligence",
                "pod_duration": "Trung bình (3-5 phút)",
                "target_words": ["artificial", "intelligence", "algorithms", "innovation"]
            },
            "metadata": {"target_words": ["artificial", "intelligence", "algorithms", "innovation"]}
        },
        {
            "level": "B2",
            "topic": None,
            "exercise_data": {
                "script": "Today we talk about space exploration. Scientists are searching for life on other planets. The Mars missions have provided valuable data. Future missions might discover signs of ancient life.",
                "pod_topic": "Space Exploration",
                "pod_duration": "Trung bình (3-5 phút)",
                "target_words": ["exploration", "planets", "missions", "ancient"]
            },
            "metadata": {"target_words": ["exploration", "planets", "missions", "ancient"]}
        },
        {
            "level": "C1",
            "topic": None,
            "exercise_data": {
                "script": "In this episode, we examine quantum computing. Quantum computers use quantum bits or qubits. They can solve complex problems exponentially faster than classical computers. This technology could revolutionize cryptography and drug discovery.",
                "pod_topic": "Quantum Computing",
                "pod_duration": "Trung bình (3-5 phút)",
                "target_words": ["quantum", "qubits", "exponentially", "cryptography"]
            },
            "metadata": {"target_words": ["quantum", "qubits", "exponentially", "cryptography"]}
        },
        {
            "level": "A2",
            "topic": None,
            "exercise_data": {
                "script": "Hello everyone. Let's talk about travel tips. When traveling, always keep important documents safe. Learn a few words of the local language. Respect the culture and customs of the places you visit.",
                "pod_topic": "Travel Tips",
                "pod_duration": "Ngắn (2-3 phút)",
                "target_words": ["documents", "language", "culture", "customs"]
            },
            "metadata": {"target_words": ["documents", "language", "culture", "customs"]}
        },
        {
            "level": "B1",
            "topic": None,
            "exercise_data": {
                "script": "Welcome. Today's topic is digital privacy. We share a lot of information online. It's important to use strong passwords. Be careful about what you post on social media. Protect your personal data.",
                "pod_topic": "Digital Privacy",
                "pod_duration": "Trung bình (3-5 phút)",
                "target_words": ["privacy", "passwords", "media", "data"]
            },
            "metadata": {"target_words": ["privacy", "passwords", "media", "data"]}
        },
        {
            "level": "B2",
            "topic": None,
            "exercise_data": {
                "script": "In this episode, we explore renewable energy. Solar and wind power are becoming more affordable. They help reduce our dependence on fossil fuels. Investing in renewable energy creates jobs and protects the environment.",
                "pod_topic": "Renewable Energy",
                "pod_duration": "Trung bình (3-5 phút)",
                "target_words": ["renewable", "affordable", "dependence", "fossil"]
            },
            "metadata": {"target_words": ["renewable", "affordable", "dependence", "fossil"]}
        },
        {
            "level": "C1",
            "topic": None,
            "exercise_data": {
                "script": "Today we discuss economic globalization. International trade has connected markets worldwide. This creates opportunities but also challenges. Countries must balance economic growth with environmental protection and social equity.",
                "pod_topic": "Economic Globalization",
                "pod_duration": "Dài (5-7 phút)",
                "target_words": ["globalization", "opportunities", "equity"]
            },
            "metadata": {"target_words": ["globalization", "opportunities", "equity"]}
        },
    ],
}

def generate_samples():
    """Generate and save sample exercises to database."""
    if not supabase:
        logger.error("Supabase client not initialized")
        return
    
    total_inserted = 0
    total_errors = 0
    
    for exercise_type, exercises in SAMPLE_EXERCISES.items():
        logger.info(f"\n=== Generating {len(exercises)} samples for {exercise_type} ===")
        
        for i, exercise in enumerate(exercises, 1):
            try:
                exercise_id = save_exercise(
                    exercise_type=exercise_type,
                    level=exercise["level"],
                    topic=exercise.get("topic"),
                    exercise_data=exercise["exercise_data"],
                    user_id=None,  # System-generated samples
                    metadata=exercise.get("metadata")
                )
                
                if exercise_id:
                    total_inserted += 1
                    logger.info(f"  [{i}/{len(exercises)}] ✓ Saved {exercise_type} exercise (ID: {exercise_id}, Level: {exercise['level']}, Topic: {exercise.get('topic', 'N/A')})")
                else:
                    total_errors += 1
                    logger.error(f"  [{i}/{len(exercises)}] ✗ Failed to save {exercise_type} exercise")
                    
            except Exception as e:
                total_errors += 1
                logger.error(f"  [{i}/{len(exercises)}] ✗ Error saving {exercise_type} exercise: {e}")
    
    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Total inserted: {total_inserted}")
    logger.info(f"Total errors: {total_errors}")
    logger.info(f"Success rate: {(total_inserted/(total_inserted+total_errors)*100):.1f}%")

if __name__ == "__main__":
    print("=" * 60)
    print("Sample Exercise Generator")
    print("=" * 60)
    print("\nThis script will generate 10 sample exercises for each type:")
    print("- dictation")
    print("- comprehension")
    print("- reading_question")
    print("- grammar_question")
    print("- podcast_script")
    print("\nTotal: 50 sample exercises")
    print("\nStarting generation...\n")
    
    generate_samples()
    
    print("\n" + "=" * 60)
    print("Generation complete!")
    print("=" * 60)
