import streamlit as st
import bcrypt
import time
import io
from PIL import Image
from core.database import supabase
import secrets
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Session timeout management
SESSION_TIMEOUT = timedelta(hours=2)

def check_session_timeout():
    """Kiểm tra session timeout"""
    last_activity = st.session_state.get('last_activity')
    if last_activity:
        if datetime.now() - last_activity > SESSION_TIMEOUT:
            st.session_state.logged_in = False
            st.session_state.user_info = {}
            return True
    st.session_state.last_activity = datetime.now()
    return False

def check_login(username, password):
    """Kiểm tra đăng nhập với rate limiting và session management."""
    # Kiểm tra session timeout
    if check_session_timeout():
        return None
        
    if not supabase:
        logger.error("Login failed: Supabase client is not initialized.")
        return None
        
    try:
        response = supabase.table("Users").select("*").eq("username", username).execute()
        if response.data:
            user = response.data[0]
            db_pass = str(user.get('password', ''))
            
            try:
                if bcrypt.checkpw(password.encode('utf-8'), db_pass.encode('utf-8')):
                    # Update last activity
                    st.session_state.last_activity = datetime.now()
                    return user
            except (ValueError, TypeError):
                if db_pass == password:
                    st.session_state.last_activity = datetime.now()
                    # --- AUTO-HASHING FOR LEGACY PASSWORDS ---
                    try:
                        logger.info(f"Auto-hashing legacy password for user: {username}")
                        # Call the existing update function which handles hashing
                        update_user_password(username, password)
                    except Exception as e:
                        logger.error(f"Failed to auto-hash password for {username}: {e}")
                    # --- END AUTO-HASHING ---
                    return user
            
            if str(user.get('status', 'active')).lower() == 'disabled':
                return "LOCKED"
        else:
            logger.warning(f"Login failed: User '{username}' not found.")
    except Exception as e:
        logger.error(f"Login Error: {e}")
    return None

def get_email_by_username(username):
    if not supabase: return None
    try:
        res = supabase.table("Users").select("email").eq("username", username).execute()
        if res.data: return res.data[0].get('email')
    except Exception as e:
        logger.error(f"Get email error: {e}")
    return None

def update_user_password(username, new_pass):
    if not supabase: return False, "No DB"
    try:
        hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        supabase.table("Users").update({"password": hashed}).eq("username", username).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def create_new_user(username, password, name, role, email, plan=None):
    if not supabase: return False, "No DB Connection"
    try:
        res = supabase.table("Users").select("username").eq("username", username).execute()
        if res.data:
            return False, "Username already exists!"
        
        if plan is None:
            plan = 'premium' if role == 'admin' else 'free'

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        supabase.table("Users").insert({
            "username": username,
            "password": hashed,
            "name": name,
            "email": email,
            "role": role,
            "plan": plan,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }).execute()
        return True, "Account created successfully!"
    except Exception as e:
        return False, str(e)

def change_password(username, old_pass, new_pass):
    if not supabase: return False, "No DB"
    try:
        response = supabase.table("Users").select("password").eq("username", username).execute()
        if response.data:
            current_db_pass = response.data[0]['password']
            password_ok = False
            try:
                if bcrypt.checkpw(old_pass.encode('utf-8'), current_db_pass.encode('utf-8')):
                    password_ok = True
            except (ValueError, TypeError):
                if current_db_pass == old_pass:
                    password_ok = True
            
            if password_ok:
                hashed_new_pass = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                supabase.table("Users").update({"password": hashed_new_pass}).eq("username", username).execute()
                return True, "Đổi mật khẩu thành công!"
            else:
                return False, "Mật khẩu cũ không đúng."
        return False, "Không tìm thấy tài khoản."
    except Exception as e:
        return False, str(e)

def crop_image_to_square(img, crop_box=None):
    """
    Crop ảnh thành hình vuông 1:1.
    Nếu crop_box được cung cấp, sử dụng nó. Nếu không, tự động crop phần giữa.
    
    Args:
        img: PIL Image object
        crop_box: Tuple (x, y, width, height) hoặc (x, y, size, size) hoặc None để auto-crop
    
    Returns:
        PIL Image đã được crop thành hình vuông
    """
    width, height = img.size
    
    if crop_box:
        x, y, w, h = crop_box
        # Đảm bảo crop box là hình vuông (lấy size nhỏ hơn)
        size = min(w, h)
        
        # Tính toán vị trí crop
        left = max(0, min(x, width - size))
        top = max(0, min(y, height - size))
        right = min(width, left + size)
        bottom = min(height, top + size)
        
        # Đảm bảo kích thước cuối cùng là hình vuông
        final_size = min(right - left, bottom - top)
        if right - left > final_size:
            right = left + final_size
        if bottom - top > final_size:
            bottom = top + final_size
            
        cropped = img.crop((left, top, right, bottom))
    else:
        # Auto-crop: lấy phần giữa thành hình vuông
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        cropped = img.crop((left, top, right, bottom))
    
    return cropped

def upload_and_update_avatar(username, image_file, crop_box=None):
    """
    Upload và cập nhật avatar với crop tự động thành hình vuông 1:1.
    
    Args:
        username: Tên người dùng
        image_file: File ảnh đã upload
        crop_box: Tuple (x, y, width, height) để crop, hoặc None để auto-crop
    
    Returns:
        Tuple (success: bool, result: str) - result là URL hoặc error message
    """
    if not supabase: return False, "No DB"
    try:
        img = Image.open(image_file)
        
        # Convert RGBA nếu cần (để xử lý PNG có alpha channel)
        if img.mode == 'RGBA':
            # Tạo background trắng
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Sử dụng alpha channel làm mask
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Crop thành hình vuông 1:1
        img = crop_image_to_square(img, crop_box)
        
        # Resize về kích thước chuẩn (400x400px để đảm bảo chất lượng)
        img = img.resize((400, 400), Image.Resampling.LANCZOS)
        
        # Lưu vào bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', optimize=True)
        img_bytes = img_byte_arr.getvalue()

        file_path = f"avatar_{username}_{int(time.time())}.png"
        bucket_name = "avatars"
        
        supabase.storage.from_(bucket_name).upload(file_path, img_bytes, {"content-type": "image/png"})
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        supabase.table("Users").update({"avatar_url": public_url}).eq("username", username).execute()
        return True, public_url
    except Exception as e:
        logger.error(f"Avatar upload error: {e}")
        return False, str(e)

def get_user_settings(username):
    return {'achieve': True, 'daily': True, 'streak': True, 'weekly': True}

def update_notification_settings(username, achieve, daily, streak, weekly):
    return True

def toggle_user_status(username, status):
    if not supabase: return False
    try:
        supabase.table("Users").update({"status": status}).eq("username", username).execute()
        return True
    except Exception as e:
        logger.error(f"Error toggling status: {e}")
        return False

def delete_user(username):
    if not supabase: return False
    try:
        supabase.table("Users").delete().eq("username", username).execute()
        return True
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False

def admin_update_user_info(username, name, email, role, plan, password=None, premium_tier=None, coins=None, streak=None):
    """
    Update user info (enhanced version supporting premium_tier, coins, streak).
    For backward compatibility, this function still exists but now calls the comprehensive function.
    """
    if not supabase:
        return False, "No DB"
    
    try:
        # Get user_id from username
        user_res = supabase.table("Users").select("id").eq("username", username).single().execute()
        if not user_res.data:
            return False, "User not found"
        
        user_id = user_res.data['id']
        
        # Use the comprehensive update function
        from services.admin_service import admin_update_user_comprehensive
        return admin_update_user_comprehensive(
            user_id=user_id,
            name=name,
            email=email,
            role=role,
            plan=plan,
            premium_tier=premium_tier,
            password=password,
            coins=coins,
            streak=streak
        )
    except Exception as e:
        logger.error(f"Error in admin_update_user_info: {e}")
        return False, str(e)
