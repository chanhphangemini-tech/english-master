# Pre-Deployment Checklist

## BẮT BUỘC - Phải chạy trước mỗi lần deploy

### 1. Syntax Check
```bash
python scripts/validate_deployment.py
```
Phải không có ERROR mới được deploy.

### 2. Kiểm tra Import
- Tất cả imports phải tồn tại
- Không được import từ module không tồn tại
- Kiểm tra circular imports

### 3. Kiểm tra Type Conversion
- `vocab_id` phải được convert sang `int()` trước khi query database
- `user_id` phải được convert sang `int()` 
- Kiểm tra tất cả các chỗ dùng `row.get('id')` hoặc `row.get('vocab_id')`

### 4. Kiểm tra Common Patterns

#### Pattern 1: vocab_id từ DataFrame
```python
# SAI:
vocab_id = row.get('id')
add_word_to_srs(uid, vocab_id)  # vocab_id có thể là float!

# ĐÚNG:
vocab_id = row.get('id')
if vocab_id:
    vocab_id = int(float(vocab_id))  # Convert float -> int
    add_word_to_srs(uid, vocab_id)
```

#### Pattern 2: None check
```python
# SAI:
if vocab_id:  # vocab_id = 0 sẽ bị skip!
    add_word_to_srs(uid, vocab_id)

# ĐÚNG:
if vocab_id is not None:
    vocab_id = int(vocab_id)
    add_word_to_srs(uid, vocab_id)
```

#### Pattern 3: DataFrame operations
```python
# SAI:
vocab_df = pd.DataFrame(load_vocab_data(level))
if not vocab_df.empty:  # Nếu data là [], DataFrame vẫn không empty!

# ĐÚNG:
vocab_data = load_vocab_data(level)
vocab_df = pd.DataFrame(vocab_data) if vocab_data else pd.DataFrame()
if not vocab_df.empty and len(vocab_data) > 0:
    # Process
```

### 5. Kiểm tra Functions
- Tất cả functions được gọi phải tồn tại
- Kiểm tra signature (parameters)
- Kiểm tra return type

### 6. Kiểm tra Database Queries
- Tất cả `vocab_id` trong queries phải là int
- Tất cả `user_id` trong queries phải là int
- Kiểm tra RLS policies (nếu có lỗi RLS, cần RPC function)

### 7. Testing
- Test với data thực tế (nếu có thể)
- Test edge cases (empty data, None values, etc.)
- Test error handling

### 8. Git Check
```bash
git status  # Kiểm tra không có file thừa
git diff    # Review changes trước khi commit
```

### 9. Deploy Checklist
- [ ] Syntax check passed
- [ ] Import check passed
- [ ] Type conversion checked
- [ ] Common patterns checked
- [ ] Functions exist
- [ ] Database queries checked
- [ ] Git status clean
- [ ] Changes reviewed
- [ ] Ready to deploy

## Files thường có lỗi

1. `pages/06_On_Tap.py` - vocab_id type, DataFrame operations
2. `services/vocab_service.py` - vocab_id type trong functions
3. `core/auth.py` - imports, function definitions
4. `pages/12_Cai_Dat.py` - imports, logger
5. `views/settings_view.py` - imports

## Common Errors

1. **TypeError: vocab_id must be int, got float**
   - Fix: Convert `int(float(vocab_id))`

2. **ImportError: cannot import name 'X' from 'Y'**
   - Fix: Kiểm tra function có tồn tại trong module Y không

3. **AttributeError: 'NoneType' object has no attribute 'data'**
   - Fix: Check `if result and result.data:` trước khi dùng

4. **400 Bad Request từ Supabase**
   - Fix: Kiểm tra type của parameters (int vs float)

5. **DataFrame operations fail**
   - Fix: Kiểm tra data không rỗng và DataFrame được tạo đúng
