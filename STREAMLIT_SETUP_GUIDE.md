# Hướng Dẫn Cấu Hình Streamlit

## ✅ Deploy GitHub đã hoàn thành!

Code đã được push lên: https://github.com/chanhphangemini-tech/english-master

---

## Bước 1: Cấu hình trên Streamlit Cloud

### 1.1. Đăng nhập Streamlit Cloud
- Vào https://share.streamlit.io
- Đăng nhập bằng GitHub account

### 1.2. Tạo App mới
1. Click **"New app"**
2. **Connect repository:**
   - Repository: `chanhphangemini-tech/english-master`
   - Branch: `main`
   - Main file path: `home.py`

3. Click **"Advanced settings"** → **"Secrets"**

### 1.3. Thêm Secrets

Thêm các secrets sau vào Streamlit Secrets:

```toml
[supabase]
url = "https://your-project-id.supabase.co"
key = "your_supabase_anon_key_here"

[google_credentials]
google_api_key = "your_gemini_api_key_here"
```

**Lưu ý:**
- App sử dụng `st.secrets` (ưu tiên) hoặc environment variables làm fallback
- Format phải đúng như trên (TOML format)
- `key` là **anon public key** (không phải service_role key)

---

## Bước 2: Lấy thông tin Supabase

### 2.1. Lấy Supabase URL và Key
1. Vào https://supabase.com → Chọn project của bạn
2. Settings → **API**
3. Copy:
   - **Project URL** → `url` trong secrets
   - **anon public** key → `key` trong secrets

### 2.2. Kiểm tra Storage Bucket
1. Vào **Storage** trong Supabase Dashboard
2. Kiểm tra bucket `tts-audio` đã tồn tại chưa
3. Nếu chưa có, tạo bucket:
   - Name: `tts-audio`
   - Public bucket: **ON**
   - Policies: Public read access

Hoặc chạy script (local):
```bash
python create_tts_bucket.py
```

---

## Bước 3: Lấy Gemini API Key

1. Vào https://aistudio.google.com/app/apikey
2. Tạo API key mới (hoặc dùng key có sẵn)
3. Copy key → `google_api_key` trong secrets

---

## Bước 4: Deploy trên Streamlit Cloud

1. Sau khi thêm secrets, click **"Deploy!"**
2. Đợi app build và deploy (khoảng 2-5 phút)
3. App sẽ có URL: `https://your-app-name.streamlit.app`

---

## Bước 5: Kiểm tra

Sau khi deploy xong, kiểm tra:
- ✅ App load được không
- ✅ Có thể đăng nhập không
- ✅ Database kết nối được không
- ✅ AI generate được content không
- ✅ Audio TTS hoạt động không

---

## Cấu hình Local (Nếu chạy local)

### Tạo file `.streamlit/secrets.toml`:

Có file template sẵn: `.streamlit/secrets.toml.template`

Copy và điền thông tin:
```bash
# Windows PowerShell
Copy-Item .streamlit\secrets.toml.template .streamlit\secrets.toml
```

Sau đó sửa file `.streamlit/secrets.toml`:
```toml
[supabase]
url = "https://your-project-id.supabase.co"
key = "your_supabase_anon_key_here"

[google_credentials]
google_api_key = "your_gemini_api_key_here"
```

**Lưu ý:** 
- File `secrets.toml` đã có trong `.gitignore`, không được commit lên GitHub
- Dùng **anon key** (không phải service_role key) cho `key`

### Chạy app local:
```bash
pip install -r requirements.txt
streamlit run home.py
```

---

## Troubleshooting

### Lỗi "No API key found"
- Kiểm tra secrets đã được thêm đúng format chưa
- Kiểm tra key name: `google_api_key` (không phải `GEMINI_API_KEY`)

### Lỗi kết nối Supabase
- Kiểm tra URL và key đúng chưa
- Kiểm tra network/firewall
- Kiểm tra RLS policies trong Supabase

### Lỗi Storage/Audio
- Kiểm tra bucket `tts-audio` đã tạo chưa
- Kiểm tra bucket policies (public read)
- Kiểm tra file paths

### App không load
- Kiểm tra logs trong Streamlit Cloud
- Kiểm tra dependencies trong `requirements.txt`
- Kiểm tra main file path: `home.py`

---

## Security Notes

⚠️ **QUAN TRỌNG:**
- Không commit file `.streamlit/secrets.toml` lên GitHub
- Không commit file `.env` lên GitHub
- API keys phải được bảo mật
- Supabase service_role key chỉ dùng server-side (nếu cần)

---

---

## Cấu hình Theme (Quan trọng!)

**Streamlit Cloud:** Vào Settings → Theme → Chọn **"Light"** (KHÔNG chọn "Use system setting")

Hoặc thêm vào file `.streamlit/config.toml` (nếu chạy local):
```toml
[theme]
base = "light"
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

**Lưu ý:** Ép Streamlit luôn dùng Light theme để tránh lỗi hiển thị khi hệ thống đang dùng Dark theme.

---

## Tham khảo

- Streamlit Secrets: https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
- Streamlit Theme: https://docs.streamlit.io/develop/api-reference/configuration/theming
- Supabase Setup: https://supabase.com/docs
- Gemini API: https://ai.google.dev/
