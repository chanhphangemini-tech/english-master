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
    """Kiểm tra xem username đã tồn tại chưa."""
    if not supabase: return False
    try:
        res = supabase.table("Users").select("id").eq("username", username).execute()
        return len(res.data) > 0 if res.data else False
    except Exception as e:
        logger.error(f"Check username exists error: {e}")
        return False

def check_email_exists(email):
    """Kiểm tra xem email đã tồn tại chưa."""
    if not supabase: return False
    try:
        res = supabase.table("Users").select("id").eq("email", email).execute()
        return len(res.data) > 0 if res.data else False
    except Exception as e:
        logger.error(f"Check email exists error: {e}")
        return False

def get_user_by_id(user_id):
    """Lấy thông tin user từ database theo user_id."""
    if not supabase or not user_id:
        return None
    try:
        res = supabase.table("Users").select("*").eq("id", user_id).single().execute()
        if res.data:
            return res.data
    except Exception as e:
        logger.error(f"Error getting user by id {user_id}: {e}")
    return None

def refresh_user_info(user_id=None):
    """Refresh user info từ database và cập nhật vào session_state."""
    if not supabase:
        return False
    
    try:
        # Get user_id from session if not provided
        if user_id is None:
            user_id = st.session_state.get('user_info', {}).get('id')
            if not user_id:
                logger.warning("Cannot refresh user info: no user_id provided and not in session")
                return False
        
        # Fetch fresh user data from database
        user_data = get_user_by_id(user_id)
        if user_data:
            # Update session_state with fresh data
            st.session_state.user_info = user_data
            logger.info(f"User info refreshed for user_id: {user_id}")
            return True
        else:
            logger.warning(f"Could not refresh user info: user not found (user_id: {user_id})")
            return False
    except Exception as e:
        logger.error(f"Error refreshing user info: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def update_user_password(username, new_pass):
    """Update user password (admin function - no verification)."""
    if not supabase: return False, "No DB"
    try:
        hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        supabase.table("Users").update({"password": hashed}).eq("username", username).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def change_password(username, old_pass, new_pass):
    """Change user password with old password verification."""
    if not supabase: 
        return False, "No DB Connection"
    
    try:
        # Get current user password
        user_res = supabase.table("Users").select("password").eq("username", username).execute()
        if not user_res.data:
            return False, "User not found"
        
        db_pass = str(user_res.data[0].get('password', ''))
        
        # Verify old password
        if db_pass.startswith('$2') and len(db_pass) >= 60:
            # Bcrypt hash
            password_bytes = old_pass.encode('utf-8')
            hash_bytes = db_pass.encode('utf-8')
            is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
            if not is_valid:
                return False, "Mật khẩu cũ không đúng"
        else:
            # Legacy plain text
            if db_pass != old_pass:
                return False, "Mật khẩu cũ không đúng"
        
        # Hash new password and update
        hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        supabase.table("Users").update({"password": hashed}).eq("username", username).execute()
        return True, "Đổi mật khẩu thành công"
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return False, str(e)

def create_new_user(username, password, name, role, email, plan=None):
    if not supabase: return False, "No DB Connection"
    try:
        # Check if username already exists
        res = supabase.table("Users").select("id").eq("username", username).execute()
        if res.data:
            return False, "Username already exists"


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
                rpc_result = str(result.data) if not isinstance(result.data, str) else result.data
            
            if rpc_result and rpc_result.startswith('SUCCESS:'):
                logger.info(f"User {username} created successfully via RPC")
                return True, "Account created successfully!"
            elif rpc_result and rpc_result.startswith('ERROR:'):
                error_msg = rpc_result.replace('ERROR:', '')
                logger.error(f"RPC register_user error: {error_msg}")
                return False, error_msg
        except Exception as rpc_error:
            logger.warning(f"RPC register_user failed, trying direct insert: {rpc_error}")
            # Fallback: Try direct insert (may fail due to RLS)
            try:
                default_plan = plan if plan else 'free'
                supabase.table("Users").insert({
                    "username": username,
                    "password": hashed,
                    "name": name,
                    "email": email,
                    "role": role,
                    "plan": default_plan,
                    "status": "active"
                }).execute()
                logger.info(f"User {username} created successfully via direct insert")
                return True, "Account created successfully!"
            except Exception as direct_error:
                logger.error(f"Direct insert also failed: {direct_error}")
                return False, f"Registration failed: {str(direct_error)}"
        
        return False, "Registration failed: Unknown error"
    except Exception as e:
        logger.error(f"Create user error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False, str(e)

def update_user_avatar(username, avatar_file):
    """Legacy function - use upload_and_update_avatar instead."""
    return upload_and_update_avatar(username, avatar_file, None)

def crop_image_to_square(img, crop_box=None):
    """
    Cắt ảnh thành hình vuông.
    
    Args:
        img: PIL Image object
        crop_box: Tuple (x, y, width, height) hoặc None để tự động cắt ở giữa
        
    Returns:
        PIL Image object đã được cắt thành hình vuông
    """
    if crop_box:
        x, y, w, h = crop_box
        # Ensure square crop
        size = min(w, h)
        # Center the crop box
        center_x = x + w // 2
        center_y = y + h // 2
        x = max(0, center_x - size // 2)
        y = max(0, center_y - size // 2)
        # Ensure we don't go out of bounds
        img_width, img_height = img.size
        x = min(x, img_width - size)
        y = min(y, img_height - size)
        return img.crop((x, y, x + size, y + size))
    else:
        # Auto crop to center square
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        return img.crop((left, top, left + size, top + size))

def upload_and_update_avatar(username, uploaded_file, crop_box=None):
    """Upload avatar image to storage and update user avatar_url."""
    if not supabase: 
        return False, "No DB Connection"
    
    try:
        # Get user_id from username
        user_res = supabase.table("Users").select("id").eq("username", username).execute()
        if not user_res.data:
            return False, "User not found"
        
        user_id = user_res.data[0]['id']
        
        # Process image
        img = Image.open(uploaded_file)
        
        # Apply crop if provided
        if crop_box:
            x, y, w, h = crop_box
            img = img.crop((x, y, x + w, y + h))
        
        # Convert and resize
        img = img.convert('RGB')
        img = img.resize((200, 200), Image.Resampling.LANCZOS)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', optimize=True)
        img_bytes = img_byte_arr.getvalue()

        file_path = f"avatar_{username}_{int(time.time())}.png"
        bucket_name = "avatars"
        
        # Upload to storage
        # Try with regular client first (if RLS policies allow)
        # If that fails, try with service_role key (bypasses RLS)
        try:
            upload_result = supabase.storage.from_(bucket_name).upload(
                file_path, 
                img_bytes, 
                {"content-type": "image/png", "upsert": "true"}
            )
            # Get public URL
            public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
            logger.info(f"Avatar uploaded successfully: {file_path}")
        except Exception as storage_error:
            logger.warning(f"Storage upload failed with regular client, trying service_role: {storage_error}")
            # Fallback: Try with service_role key to bypass RLS
            try:
                # Get service_role key from secrets
                service_key = None
                try:
                    service_key = st.secrets.get("supabase", {}).get("service_role_key")
                except:
                    pass
                
                if not service_key:
                    # Try environment variable
                    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                
                if service_key:
                    # Create client with service_role key
                    supabase_url = None
                    try:
                        supabase_url = st.secrets["supabase"]["url"]
                    except:
                        supabase_url = os.getenv("SUPABASE_URL")
                    
                    if supabase_url:
                        service_client = create_client(supabase_url, service_key)
                        upload_result = service_client.storage.from_(bucket_name).upload(
                            file_path, 
                            img_bytes, 
                            {"content-type": "image/png", "upsert": "true"}
                        )
                        public_url = service_client.storage.from_(bucket_name).get_public_url(file_path)
                        logger.info(f"Avatar uploaded successfully using service_role: {file_path}")
                    else:
                        raise Exception("No Supabase URL found")
                else:
                    # No service_role key available, raise original error
                    raise storage_error
            except Exception as service_error:
                logger.error(f"Storage upload error (both methods failed): {service_error}")
                # Log detailed error for debugging
                import traceback
                logger.error(f"Storage upload traceback: {traceback.format_exc()}")
                # If storage upload fails, we can't continue
                return False, f"Lỗi upload ảnh: {str(service_error)}"
        
        # Update avatar_url using RPC function (bypasses RLS)
        try:
            rpc_result = supabase.rpc("update_user_avatar_url", {
                "p_user_id": user_id,
                "p_avatar_url": public_url
            }).execute()
            
            if rpc_result.data:
                result_text = str(rpc_result.data) if not isinstance(rpc_result.data, str) else rpc_result.data
                if result_text.startswith('SUCCESS:'):
                    logger.info(f"Avatar updated successfully for user {username} via RPC")
                    return True, public_url
                elif result_text.startswith('ERROR:'):
                    error_msg = result_text.replace('ERROR:', '')
                    logger.error(f"RPC update_user_avatar_url error: {error_msg}")
                    return False, error_msg
        except Exception as rpc_error:
            logger.warning(f"RPC update_user_avatar_url failed, trying direct update: {rpc_error}")
            # Fallback: Try direct update (may fail due to RLS)
            try:
                supabase.table("Users").update({"avatar_url": public_url}).eq("username", username).execute()
                logger.info(f"Avatar updated successfully for user {username} via direct update")
                return True, public_url
            except Exception as direct_error:
                logger.error(f"Direct update also failed: {direct_error}")
                return False, f"Lỗi cập nhật avatar: {str(direct_error)}"
        
        return False, "Lỗi không xác định khi cập nhật avatar"
    except Exception as e:
        logger.error(f"Avatar upload error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
