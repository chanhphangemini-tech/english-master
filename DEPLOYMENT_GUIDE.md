# Deployment Guide - Hướng Dẫn Deploy An Toàn

## ⚠️ QUAN TRỌNG: Luôn chạy validation trước khi deploy!

### Bước 1: Validation (BẮT BUỘC)

```bash
python scripts/validate_deployment.py
```

**Phải không có ERROR mới được deploy!**

### Bước 2: Kiểm tra thủ công

Xem file `scripts/pre_deployment_checklist.md` để kiểm tra các điểm quan trọng:

1. ✅ Syntax check passed
2. ✅ Import check passed  
3. ✅ Type conversion checked (vocab_id, user_id)
4. ✅ Common patterns checked
5. ✅ Functions exist
6. ✅ Database queries checked

### Bước 3: Git workflow

```bash
# 1. Kiểm tra changes
git status
git diff

# 2. Validation
python scripts/validate_deployment.py

# 3. Nếu pass, commit và push
git add .
git commit -m "Your message"
git push origin main
```

### Bước 4: Sau khi deploy

1. Kiểm tra logs trên Streamlit Cloud
2. Test các chức năng chính
3. Nếu có lỗi, rollback ngay

## Common Issues & Solutions

### Lỗi: vocab_id type error
**Triệu chứng:** `400 Bad Request` hoặc `Failed to add word to SRS`

**Nguyên nhân:** vocab_id từ pandas DataFrame là float (488.0) thay vì int

**Giải pháp:**
```python
# SAI:
vocab_id = row.get('id')
add_word_to_srs(uid, vocab_id)

# ĐÚNG:
vocab_id = row.get('id')
if vocab_id:
    vocab_id = int(float(vocab_id))  # Convert float -> int
    add_word_to_srs(uid, vocab_id)
```

### Lỗi: ImportError
**Triệu chứng:** `cannot import name 'X' from 'Y'`

**Giải pháp:**
- Kiểm tra function có tồn tại trong module Y không
- Kiểm tra file Y có syntax error không
- Kiểm tra circular import

### Lỗi: BOM character
**Triệu chứng:** `invalid non-printable character U+FEFF`

**Giải pháp:**
```bash
# Remove BOM từ file
python -c "with open('file.py', 'rb') as f: content = f.read(); content = content.lstrip(b'\xef\xbb\xbf'); open('file.py', 'wb').write(content)"
```

### Lỗi: DataFrame empty check
**Triệu chứng:** Logic sai khi DataFrame rỗng

**Giải pháp:**
```python
# SAI:
vocab_df = pd.DataFrame(load_vocab_data(level))
if not vocab_df.empty:  # Nếu data=[], DataFrame vẫn không empty!

# ĐÚNG:
vocab_data = load_vocab_data(level)
vocab_df = pd.DataFrame(vocab_data) if vocab_data else pd.DataFrame()
if not vocab_df.empty and len(vocab_data) > 0:
    # Process
```

## Validation Script

Script `scripts/validate_deployment.py` sẽ kiểm tra:

1. ✅ Syntax errors
2. ✅ Import errors (một số critical modules)
3. ✅ Common coding patterns
4. ✅ Type conversion issues

## Checklist Template

Trước mỗi lần deploy, copy checklist này:

```
- [ ] Validation script passed (không có ERROR)
- [ ] Đã review code changes
- [ ] Đã test locally (nếu có thể)
- [ ] Đã kiểm tra imports
- [ ] Đã kiểm tra type conversions (vocab_id, user_id)
- [ ] Đã kiểm tra DataFrame operations
- [ ] Git status clean
- [ ] Ready to deploy
```

## Lưu ý

1. **KHÔNG BAO GIỜ** deploy khi validation có ERROR
2. **LUÔN** review code changes trước khi commit
3. **KIỂM TRA** logs sau khi deploy
4. **ROLLBACK** ngay nếu có lỗi nghiêm trọng

## Liên hệ

Nếu có lỗi sau khi deploy, check:
1. Streamlit Cloud logs
2. Supabase logs (nếu có)
3. Browser console (nếu có)
4. Review code changes gần đây nhất
