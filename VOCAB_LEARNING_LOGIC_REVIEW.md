# Rà Soát Logic Học Từ Vựng - Trang 06_On_Tap.py

## 📋 Tổng Quan

Trang "Học & Ôn Tập" (`pages/06_On_Tap.py`) cho phép người dùng học từ vựng mới và ôn tập từ đã học thông qua hệ thống SRS (Spaced Repetition System).

---

## 🔄 Flow Hoạt Động

### 1. **Cấu Hình Nội Dung Học** (`render_learning_view`)

```python
# Bước 1: Người dùng chọn trình độ (A1-A2, B1-B2, C1-C2)
target_level = st.selectbox("1. Chọn trình độ:", options=all_levels)

# Bước 2: Chọn số từ mới mỗi ngày
daily_limit = st.number_input("2. Số từ mới mỗi ngày:", min_value=5, max_value=max_words)
# - Premium users (Basic/Premium/Pro): max_words = 999 (unlimited)
# - Free users: max_words = 20

# Bước 3: Chọn chủ đề (tùy chọn)
selected_topics = st.multiselect("3. Chọn chủ đề (Tùy chọn):", options=topic_options)
```

### 2. **Lấy Từ Mới** (New Words)

**Logic:**
- Nếu có chọn chủ đề (`selected_topics`):
  1. Lấy danh sách `vocab_id` đã học từ `UserVocabulary`
  2. Lấy tất cả từ vựng từ `vocab_df` (đã filter theo level) và filter theo topics
  3. Loại bỏ các từ đã học (not in learned_ids)
  4. Giới hạn số lượng theo `daily_limit`

- Nếu không chọn chủ đề:
  - Gọi `get_daily_learning_batch(uid, target_level, daily_limit, "General")`
  - Hàm này:
    - Lấy danh sách `vocab_id` đã học
    - Query từ `Vocabulary` table với level = `target_level`
    - Loại bỏ các từ đã học (not in learned_ids)
    - Limit theo `daily_limit`
    - Return danh sách từ mới

**Kết quả:** `new_words_df` - DataFrame với `type='new'`

### 3. **Lấy Từ Cần Ôn Tập** (Review Words - SRS)

**Logic:**
- Gọi `get_due_vocabulary(uid)`
- Hàm này:
  - Query `UserVocabulary` table với `due_date <= now_utc`
  - Join với `Vocabulary` table để lấy chi tiết từ
  - Return danh sách từ cần ôn tập (theo SRS algorithm)

**Kết quả:** `review_df` - DataFrame với `type='review'`, có thêm column `vocab_id`

### 4. **Gộp và Hiển Thị**

```python
combined_view = pd.concat([new_words_df, review_df]).drop_duplicates(subset=['word'])
```

- Gộp 2 DataFrame lại
- Loại bỏ duplicate theo `word` (nếu từ vừa mới vừa cần review, chỉ giữ 1 bản)
- Hiển thị danh sách từ vựng với audio TTS

### 5. **Kiểm Tra Từ Vựng** (Quiz Mode)

**Chế độ kiểm tra:**
- **Kiểm tra nghĩa**: Hiển thị từ tiếng Anh, yêu cầu nhập nghĩa tiếng Việt
- **Kiểm tra từ**: Hiển thị nghĩa tiếng Việt, yêu cầu nhập từ tiếng Anh

**Cách chấm điểm:**
```python
# Normalize text để so sánh (case-insensitive, strip whitespace)
u_ans_normalized = normalize_meaning_text(u_ans.strip().lower())
correct_normalized = normalize_meaning_text(correct_meaning.strip().lower())
is_right = (u_ans_normalized == correct_normalized)
```

### 6. **Lưu Kết Quả** (`score_quiz`)

#### 6.1. Xử Lý Từ Review (`type='review'`)

```python
if word_type == 'review':
    vid = row.get('vocab_id')
    if vid:
        update_srs_stats(uid, vid, quality)
        # quality = 5 nếu đúng, 1 nếu sai
```

**`update_srs_stats` làm gì:**
- Lấy thông tin hiện tại từ `UserVocabulary` (streak, interval, ease_factor)
- Tính toán lịch review mới dựa trên SM-2 algorithm:
  - Quality >= 3: Tăng streak, tính interval mới, cập nhật ease_factor
  - Quality < 3: Reset streak về 0, interval = 1
- Cập nhật `due_date`, `interval`, `ease_factor`, `streak`, `status`, `last_reviewed_at`
- Thưởng 1 coin nếu quality >= 3 (trong hàm `update_srs_stats`)

#### 6.2. Xử Lý Từ Mới (`type='new'`)

```python
elif word_type == 'new':
    vocab_id = row.get('id')
    if vocab_id:
        add_word_to_srs(uid, vocab_id)  # LUÔN thêm vào SRS (kể cả khi sai)
```

**`add_word_to_srs` làm gì:**
- Kiểm tra xem từ đã có trong `UserVocabulary` chưa (nếu có, return True)
- Nếu chưa có:
  - Insert vào `UserVocabulary` với:
    - `status = "learning"`
    - `streak = 0`
    - `interval = 0`
    - `ease_factor = 2.5`
    - `due_date = now_utc`
    - `last_reviewed_at = now_utc`
  - Thưởng 1 coin (trong hàm `add_word_to_srs`)
  - Check achievements
  - Log security monitor

**⚠️ QUAN TRỌNG:** 
- Từ mới **LUÔN** được thêm vào SRS (kể cả khi trả lời sai)
- Mục đích: Ẩn từ khỏi danh sách học mới, đưa vào hệ thống SRS để ôn tập sau

#### 6.3. Thưởng Coins

```python
coin_reward = correct_count * 2  # 2 coins mỗi câu đúng
if coin_reward > 0:
    coin_success = add_coins(uid, coin_reward)
    # add_coins sử dụng RPC 'increment_coins' để cộng coin an toàn
```

**Tổng coins thưởng:**
- Quiz reward: `correct_count * 2` coins
- Từ mới: `1 coin/từ` (trong `add_word_to_srs`)
- Từ review (quality >= 3): `1 coin/từ` (trong `update_srs_stats`)

### 7. **Tracking Daily Goal** (`words_today`)

**Cách tính `words_today`:**
```python
# Trong get_user_stats hoặc get_dashboard_stats RPC
words_today = COUNT(*) FROM UserVocabulary 
WHERE user_id = uid AND created_at >= start_of_day_utc
```

**Logic:**
- `words_today` = Số từ được thêm vào `UserVocabulary` trong ngày (theo timezone VN)
- Khi `add_word_to_srs` được gọi, từ được insert với `created_at = now_utc`
- Nếu `created_at >= start_of_day_utc` (giờ 0:00 VN), từ sẽ được đếm vào `words_today`

**⚠️ LƯU Ý:**
- Từ mới được thêm vào SRS **LUÔN** (kể cả khi sai), nên `words_today` sẽ tăng
- Từ review **KHÔNG** tăng `words_today` (vì `created_at` không thay đổi khi update)

---

## 🔍 Điểm Quan Trọng Cần Lưu Ý

### ✅ Đã Sửa (Trong Commit Mới Nhất)

1. **Từ mới luôn được lưu vào SRS:**
   - Trước: Chỉ lưu khi trả lời đúng (`elif word_type == 'new' and is_right`)
   - Sau: Luôn lưu (`elif word_type == 'new'`)

2. **Error handling cho coins:**
   - Check kết quả `add_coins()`
   - Hiển thị warning nếu thất bại

3. **Clear cache sau quiz:**
   - Gọi `st.cache_data.clear()` để stats cập nhật ngay

### ⚠️ Các Vấn Đề Tiềm Ẩn

1. **Duplicate Coins:**
   - Từ mới: Thưởng 1 coin trong `add_word_to_srs` + 2 coins/câu đúng trong quiz
   - Từ review: Thưởng 1 coin nếu quality >= 3 trong `update_srs_stats` + 2 coins/câu đúng trong quiz
   - → Có thể có double reward (nhưng có vẻ là intentional)

2. **Daily Goal Logic:**
   - `words_today` chỉ đếm từ mới (created_at trong ngày)
   - Từ review không tăng `words_today` (đúng logic)
   - Nhưng nếu user làm quiz toàn từ review, `words_today` sẽ không tăng

3. **SRS Status:**
   - Từ mới được thêm với `status = "learning"` và `due_date = now_utc`
   - Điều này có nghĩa là từ sẽ xuất hiện lại trong danh sách review ngay lập tức
   - Có thể cần điều chỉnh `due_date` dựa trên quality (đúng/sai)

---

## 📊 Tóm Tắt Flow Hoàn Chỉnh

```
1. User chọn level + daily_limit + topics (optional)
   ↓
2. Lấy từ mới (chưa học) từ Vocabulary theo level/topics
   ↓
3. Lấy từ cần review (due_date <= now) từ UserVocabulary
   ↓
4. Gộp và hiển thị danh sách (new + review)
   ↓
5. User làm quiz (kiểm tra nghĩa hoặc từ)
   ↓
6. Chấm điểm và lưu kết quả:
   - Từ review: update_srs_stats (tính toán SRS mới)
   - Từ mới: add_word_to_srs (LUÔN thêm vào SRS)
   ↓
7. Thưởng coins:
   - Quiz: 2 coins/câu đúng
   - Từ mới: 1 coin/từ (trong add_word_to_srs)
   - Từ review (quality >= 3): 1 coin/từ (trong update_srs_stats)
   ↓
8. Clear cache để stats cập nhật ngay
   ↓
9. words_today = COUNT(UserVocabulary WHERE created_at >= start_of_day)
```

---

## 💡 Gợi Ý Cải Thiện

1. **Điều chỉnh `due_date` cho từ mới dựa trên quality:**
   ```python
   # Nếu trả lời đúng: due_date = now + 1 day
   # Nếu trả lời sai: due_date = now (review ngay)
   ```

2. **Tách biệt coins reward:**
   - Quiz reward: Riêng biệt
   - SRS reward: Riêng biệt (trong các hàm SRS)
   - Tránh double reward

3. **Tracking chi tiết hơn:**
   - Track số từ học mới hôm nay (new words learned today)
   - Track số từ review hôm nay (reviewed words today)
   - Separate metrics cho dashboard
