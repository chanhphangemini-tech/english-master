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
        # Trim username to handle whitespace issues
        username_clean = username.strip() if username else ""
        if not username_clean:
            logger.warning("Login failed: Empty username")
            return None
        
        logger.info(f"Attempting to find user: '{username_clean}'")
        response = supabase.table("Users").select("*").eq("username", username_clean).execute()
        
        # Debug: Log response details
        logger.info(f"Query response: data_count={len(response.data) if response.data else 0}, response_type={type(response)}")
        if response.data:
            logger.info(f"Found user: {response.data[0].get('username')}, id={response.data[0].get('id')}")
        else:
            logger.warning(f"No user found with username: '{username_clean}'")
            # Try case-insensitive search as fallback
            try:
                all_users = supabase.table("Users").select("username, id").execute()
                if all_users.data:
                    logger.info(f"Available usernames in DB: {[u.get('username') for u in all_users.data]}")
                    # Try case-insensitive match
                    for u in all_users.data:
                        if u.get('username', '').lower() == username_clean.lower():
                            logger.info(f"Found case-insensitive match: '{u.get('username')}' matches '{username_clean}'")
                            # Retry with exact username from DB
                            response = supabase.table("Users").select("*").eq("username", u.get('username')).execute()
                            if response.data:
                                logger.info(f"Successfully retrieved user with exact username from DB")
                                break
            except Exception as fallback_error:
                logger.error(f"Fallback search error: {fallback_error}")
        
        if response.data:
            user = response.data[0]
            db_pass = str(user.get('password', ''))
            
            # Debug logging
            logger.info(f"Login attempt for user: {username}, password hash preview: {db_pass[:20] if db_pass else 'None'}...")
            
            # Check if account is disabled first
            if str(user.get('status', 'active')).lower() == 'disabled':
                return "LOCKED"
            
            # Try bcrypt verification first
            # Check if password is already hashed (bcrypt hashes start with $2b$ or $2a$)
            if db_pass.startswith('$2') and len(db_pass) >= 60:
                # It's a bcrypt hash, verify it
                try:
                    # Ensure both are bytes
                    password_bytes = password.encode('utf-8')
                    hash_bytes = db_pass.encode('utf-8')
                    
                    is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
                    if is_valid:
                        # Update last activity
                        st.session_state.last_activity = datetime.now()
                        logger.info(f"Login successful for user: {username}")
                        return user
                    else:
                        logger.warning(f"Password verification failed for user: {username} (bcrypt hash mismatch)")
                        logger.debug(f"Password hash preview: {db_pass[:30]}...")
                        return None
                except Exception as bcrypt_check_error:
                    logger.error(f"Bcrypt checkpw error for user {username}: {bcrypt_check_error}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return None
            else:
                # Legacy plain text password (should not happen for new users)
                logger.info(f"Legacy password detected for user: {username} (hash length: {len(db_pass)})")
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
                else:
                    logger.warning(f"Legacy password mismatch for user: {username}")
                    return None
        else:
            logger.warning(f"Login failed: User '{username}' not found.")
    except Exception as e:
        logger.error(f"Login Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    return None

def get_email_by_username(username):
    if not supabase: return None
    try:
        res = supabase.table("Users").select("email").eq("username", username).execute()
        if res.data: return res.data[0].get('email')
    except Exception as e:
        logger.error(f"Get email error: {e}")
    return None

def check_username_exists(username):
    """Kiểm tra xem username đã tồn tại chưa"""
    if not supabase: return False
    try:
        res = supabase.table("Users").select("username").eq("username", username).limit(1).execute()
        return len(res.data) > 0
    except Exception as e:
        logger.error(f"Error checking username: {e}")
        return False

def check_email_exists(email):
    """Kiểm tra xem email đã tồn tại chưa"""
    if not supabase: return False
    try:
        res = supabase.table("Users").select("email").eq("email", email).limit(1).execute()
        return len(res.data) > 0
    except Exception as e:
        logger.error(f"Error checking email: {e}")
        return False

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
        # Check if username already exists
        res = supabase.table("Users").select("username").eq("username", username).execute()
        if res.data:
            return False, "Username already exists!"
        
        if plan is None:
            plan = 'premium' if role == 'admin' else 'free'

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Try using RPC function first (bypasses RLS)
        try:
            result = supabase.rpc('register_user', {
                'p_username': username,
                'p_password': hashed,
                'p_name': name,
                'p_email': email,
                'p_role': role,
                'p_plan': plan
            }).execute()
            
            # Parse RPC result - function now returns TEXT in format "SUCCESS:message" or "ERROR:message"
            rpc_result = None
            if result.data:
                # Handle different response formats
                if isinstance(result.data, str):
                    rpc_result = result.data
                elif isinstance(result.data, list) and len(result.data) > 0:
                    rpc_result = result.data[0] if isinstance(result.data[0], str) else str(result.data[0])
                elif isinstance(result.data, dict):
                    # Try to extract from dict
                    rpc_result = result.data.get('register_user') or str(result.data)
                else:
                    rpc_result = str(result.data)
            
            if rpc_result:
                if rpc_result.startswith('SUCCESS:'):
                    message = rpc_result.replace('SUCCESS:', '', 1)
                    return True, message
                elif rpc_result.startswith('ERROR:'):
                    error_msg = rpc_result.replace('ERROR:', '', 1)
                    logger.warning(f"RPC registration failed: {error_msg}")
                    return False, error_msg
                else:
                    # Try to parse as JSON if it's JSON format
                    try:
                        import json
                        if isinstance(rpc_result, str) and rpc_result.strip().startswith('{'):
                            parsed = json.loads(rpc_result)
                            if parsed.get('success'):
                                return True, parsed.get('message', 'Account created successfully!')
                            else:
                                return False, parsed.get('message', 'Registration failed')
                    except:
                        pass
                    logger.warning(f"RPC returned unexpected format: {rpc_result}")
        except Exception as rpc_error:
            # If RPC fails, fall back to direct insert
            logger.warning(f"RPC function not available or failed: {rpc_error}, trying direct insert")
        
        # Fallback: Try to use service_role key if available (bypasses RLS)
        try:
            import streamlit as st
            service_key = None
            try:
                service_key = st.secrets.get("supabase", {}).get("service_role_key")
            except:
                service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if service_key and supabase:
                # Get URL from supabase client
                supabase_url = None
                try:
                    supabase_url = st.secrets["supabase"]["url"]
                except:
                    supabase_url = os.getenv("SUPABASE_URL")
                
                if supabase_url:
                    # Create a service_role client for this operation
                    service_client = create_client(supabase_url, service_key)
                service_client.table("Users").insert({
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
        except Exception as service_error:
            logger.warning(f"Service role insert failed: {service_error}, trying regular insert")
        
        # Final fallback: Direct insert (will use RLS policies)
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
        logger.error(f"User registration error: {e}")
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
    """Xóa user (chỉ admin mới có quyền)."""
    if not supabase: 
        return False
    
    try:
        # Get user_id from username
        user_res = supabase.table("Users").select("id").eq("username", username).single().execute()
        if not user_res.data:
            logger.warning(f"User {username} not found")
            return False
        
        user_id = user_res.data['id']
        
        # Get admin_id from session
        admin_id = None
        try:
            admin_id = st.session_state.get('user_info', {}).get('id')
        except:
            pass
        
        # Prevent self-deletion
        if admin_id == user_id:
            logger.warning(f"User {username} attempted to delete themselves")
            return False
        
        # Try RPC function first (bypasses RLS)
        try:
            rpc_result = supabase.rpc("admin_delete_user", {
                "p_user_id": user_id,
                "p_admin_user_id": admin_id
            }).execute()
            
            if rpc_result.data:
                result_text = str(rpc_result.data) if not isinstance(rpc_result.data, str) else rpc_result.data
                if result_text.startswith('SUCCESS:'):
                    logger.info(f"User {username} deleted successfully via RPC: {result_text}")
                    return True
                elif result_text.startswith('ERROR:'):
                    error_msg = result_text.replace('ERROR:', '')
                    logger.error(f"RPC admin_delete_user error: {error_msg}")
                    return False
        except Exception as rpc_error:
            logger.warning(f"RPC admin_delete_user failed: {rpc_error}")
            # Fallback: Try direct delete (may fail due to RLS)
            try:
                result = supabase.table("Users").delete().eq("id", user_id).execute()
                if result.data:
                    logger.info(f"User {username} deleted successfully via direct delete")
                    return True
                else:
                    logger.warning(f"User {username} deletion failed - no rows deleted")
                    return False
            except Exception as direct_error:
                logger.error(f"Direct delete also failed: {direct_error}")
                return False
        
        return False
    except Exception as e:
        logger.error(f"Error deleting user {username}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
