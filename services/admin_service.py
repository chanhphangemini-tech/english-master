import streamlit as st
from core.database import supabase
from datetime import datetime, timezone
from core.timezone_utils import get_vn_start_of_day_utc
import bcrypt
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

def get_all_users():
    """Lấy toàn bộ user (cho Admin)."""
    if not supabase: 
        st.error("Lỗi kết nối đến cơ sở dữ liệu.")
        return []
    try:
        response = supabase.table("Users").select("*").order("created_at", desc=True).execute()
        if response.data:
            return response.data
    except Exception as e:
        st.error(f"Lỗi khi tải danh sách người dùng: {e}")
    return []

def get_system_analytics():
    """Lấy số liệu thống kê toàn hệ thống cho Admin Dashboard."""
    stats = {
        "total_users": 0, "total_vocab": 0, "total_reviews": 0, "active_users_today": 0,
        "total_coins": 0, "total_pvp": 0, "completed_pvp": 0, "total_bet": 0
    }
    if not supabase: return stats
    try:
        # Count Users
        stats["total_users"] = supabase.table("Users").select("id", count="exact").execute().count
        # Count Vocab
        stats["total_vocab"] = supabase.table("Vocabulary").select("id", count="exact").execute().count
        # Count Reviews (UserVocabulary items that are being learned)
        stats["total_reviews"] = supabase.table("UserVocabulary").select("id", count="exact").execute().count
        # Active Users
        # Use VN timezone for "today" calculation
        start_of_day_utc = get_vn_start_of_day_utc()
        stats["active_users_today"] = supabase.table("ActivityLog").select("id", count="exact").gte("created_at", start_of_day_utc).execute().count
        
        # Advanced stats via RPC (optional - has fallback)
        try:
            res = supabase.rpc("get_admin_stats").execute()
            if res.data:
                if isinstance(res.data, dict):
                    stats.update(res.data)
                elif isinstance(res.data, list) and len(res.data) > 0:
                    stats.update(res.data[0])
        except Exception as rpc_error:
            error_msg = str(rpc_error)
            # RPC is optional, so just log warning
            if 'does not exist' in error_msg.lower() or 'function' in error_msg.lower():
                print(f"INFO: RPC function 'get_admin_stats' not found. Using basic stats only.")
            else:
                print(f"Analytics RPC error: {rpc_error}")
    except Exception as e:
        print(f"Analytics error: {e}")
    return stats

# ==================== ENHANCED ADMIN USER MANAGEMENT FUNCTIONS ====================

def admin_get_user_full_info(user_id: int) -> Dict:
    """
    Get comprehensive user info including:
    - Basic info (name, email, username, role, plan, tier)
    - Stats (coins, streak, words_learned)
    - Subscription info (end_date, status)
    - AI usage (current usage, limits, top-up balance)
    
    Returns: dict with all user info
    """
    if not supabase:
        return {}
    
    try:
        # Get user basic info
        user_res = supabase.table("Users").select("*").eq("id", user_id).single().execute()
        if not user_res.data:
            return {}
        
        user_info = user_res.data
        
        # Get subscription info
        subscription = None
        try:
            sub_res = supabase.table("Subscriptions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            if sub_res.data:
                subscription = sub_res.data[0]
        except:
            pass
        
        # Get AI usage info (if premium)
        ai_usage_info = None
        if user_info.get('plan') == 'premium':
            try:
                from services.premium_usage_service import get_premium_ai_usage_monthly
                ai_usage_info = get_premium_ai_usage_monthly(user_id)
            except:
                pass
        
        # Get top-up balance
        topup_balance = 0
        try:
            from services.premium_usage_service import get_topup_balance
            topup_balance = get_topup_balance(user_id)
        except:
            pass
        
        # Get vocabulary stats
        vocab_count = 0
        try:
            vocab_res = supabase.table("UserVocabulary")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .execute()
            vocab_count = vocab_res.count or 0
        except:
            pass
        
        return {
            "basic_info": {
                "id": user_info.get('id'),
                "username": user_info.get('username'),
                "name": user_info.get('name'),
                "email": user_info.get('email'),
                "role": user_info.get('role'),
                "plan": user_info.get('plan'),
                "premium_tier": user_info.get('premium_tier'),
                "status": user_info.get('status'),
                "current_level": user_info.get('current_level'),
                "created_at": user_info.get('created_at')
            },
            "stats": {
                "coins": user_info.get('coins', 0),
                "streak": user_info.get('current_streak', 0),
                "words_learned": vocab_count,
                "daily_goal": user_info.get('daily_goal', 10)
            },
            "subscription": subscription,
            "ai_usage": ai_usage_info,
            "topup_balance": topup_balance
        }
    except Exception as e:
        logger.error(f"Error getting user full info: {e}")
        return {}

def admin_update_user_comprehensive(
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    plan: Optional[str] = None,
    premium_tier: Optional[str] = None,
    password: Optional[str] = None,
    coins: Optional[int] = None,
    streak: Optional[int] = None,
    status: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Comprehensive user update function.
    Updates all provided fields and logs actions.
    
    Args:
        user_id: User ID to update
        name: New name (optional)
        email: New email (optional)
        role: New role - 'user', 'admin', 'moderator' (optional)
        plan: New plan - 'free', 'premium' (optional)
        premium_tier: New tier - 'basic', 'premium', 'pro' (optional, only if plan='premium')
        password: New password (optional, will be hashed)
        coins: New coins amount (optional)
        streak: New streak value (optional)
        status: New status - 'active', 'disabled' (optional)
    
    Returns:
        Tuple (success: bool, message: str)
    """
    if not supabase:
        return False, "No database connection"
    
    try:
        # Get current user info
        current_user_res = supabase.table("Users").select("*").eq("id", user_id).single().execute()
        if not current_user_res.data:
            return False, "User not found"
        
        current_user = current_user_res.data
        
        # Get admin_id for logging
        admin_id = None
        try:
            admin_id = st.session_state.user_info.get('id')
        except:
            pass
        
        # Build update dict
        update_data = {}
        changes_log = []
        
        if name is not None and name != current_user.get('name'):
            update_data['name'] = name
            changes_log.append(f"name: '{current_user.get('name')}' → '{name}'")
        
        if email is not None and email != current_user.get('email'):
            # Validate email
            if '@' not in email:
                return False, "Email không hợp lệ"
            update_data['email'] = email
            changes_log.append(f"email: '{current_user.get('email')}' → '{email}'")
        
        if role is not None and role != current_user.get('role'):
            # Validate role
            valid_roles = ['user', 'admin', 'moderator']
            if role not in valid_roles:
                return False, f"Role không hợp lệ. Phải là một trong: {valid_roles}"
            update_data['role'] = role
            changes_log.append(f"role: '{current_user.get('role')}' → '{role}'")
        
        if plan is not None and plan != current_user.get('plan'):
            # Validate plan (updated to include all subscription tiers)
            valid_plans = ['free', 'basic', 'premium', 'pro']
            if plan not in valid_plans:
                return False, f"Plan không hợp lệ. Phải là một trong: {valid_plans}"
            update_data['plan'] = plan
            changes_log.append(f"plan: '{current_user.get('plan')}' → '{plan}'")
            
            # Auto-set tier when changing plan
            if plan == 'free':
                update_data['premium_tier'] = None
                changes_log.append("premium_tier: removed (free plan)")
            elif plan in ('basic', 'premium', 'pro') and premium_tier is None:
                # Default tier to match plan if not specified
                update_data['premium_tier'] = plan
                changes_log.append(f"premium_tier: set to '{plan}' (default)")
        
        if premium_tier is not None:
            # Validate tier
            valid_tiers = ['basic', 'premium', 'pro']
            if premium_tier not in valid_tiers:
                return False, f"Premium tier không hợp lệ. Phải là một trong: {valid_tiers}"
            
            # Only allow tier if plan is a premium tier (basic, premium, or pro)
            final_plan = plan if plan is not None else current_user.get('plan')
            if final_plan not in ('basic', 'premium', 'pro'):
                return False, "Premium tier chỉ có thể set khi plan là basic, premium, hoặc pro"
            
            if premium_tier != current_user.get('premium_tier'):
                update_data['premium_tier'] = premium_tier
                changes_log.append(f"premium_tier: '{current_user.get('premium_tier')}' → '{premium_tier}'")
        
        if password:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            update_data['password'] = hashed
            changes_log.append("password: updated")
        
        if coins is not None:
            coins_int = int(coins)
            current_coins = current_user.get('coins', 0) or 0
            if coins_int != current_coins:
                update_data['coins'] = coins_int
                changes_log.append(f"coins: {current_coins} → {coins_int}")
        
        if streak is not None:
            streak_int = int(streak)
            current_streak = current_user.get('current_streak', 0) or 0
            if streak_int != current_streak:
                update_data['current_streak'] = streak_int
                changes_log.append(f"streak: {current_streak} → {streak_int}")
        
        if status is not None and status != current_user.get('status'):
            # Validate status
            valid_statuses = ['active', 'disabled']
            if status not in valid_statuses:
                return False, f"Status không hợp lệ. Phải là một trong: {valid_statuses}"
            update_data['status'] = status
            changes_log.append(f"status: '{current_user.get('status')}' → '{status}'")
        
        # Execute update if there are changes
        if update_data:
            # Try RPC function first (bypasses RLS)
            try:
                rpc_result = supabase.rpc("admin_update_user", {
                    "p_user_id": user_id,
                    "p_name": update_data.get('name'),
                    "p_email": update_data.get('email'),
                    "p_role": update_data.get('role'),
                    "p_plan": update_data.get('plan'),
                    "p_premium_tier": update_data.get('premium_tier'),
                    "p_password": update_data.get('password'),
                    "p_coins": update_data.get('coins'),
                    "p_current_streak": update_data.get('current_streak'),
                    "p_status": update_data.get('status'),
                    "p_admin_user_id": admin_id
                }).execute()
                
                if rpc_result.data:
                    result_text = str(rpc_result.data) if not isinstance(rpc_result.data, str) else rpc_result.data
                    if result_text.startswith('SUCCESS:'):
                        # Log admin action
                        try:
                            from core.security_monitor import SecurityMonitor
                            if admin_id:
                                SecurityMonitor.log_user_action(
                                    admin_id,
                                    'admin_user_update',
                                    success=True,
                                    metadata={
                                        'target_user_id': user_id,
                                        'target_username': current_user.get('username'),
                                        'changes': changes_log,
                                        'updated_fields': list(update_data.keys())
                                    }
                                )
                        except Exception as log_error:
                            logger.warning(f"Error logging admin action: {log_error}")
                        
                        return True, f"✅ Đã cập nhật: {result_text.replace('SUCCESS:', '')}"
                    elif result_text.startswith('ERROR:'):
                        error_msg = result_text.replace('ERROR:', '')
                        logger.error(f"RPC admin_update_user error: {error_msg}")
                        return False, f"Lỗi: {error_msg}"
            except Exception as rpc_error:
                logger.warning(f"RPC admin_update_user failed, trying direct update: {rpc_error}")
                # Fallback to direct update (may fail due to RLS)
                try:
                    supabase.table("Users").update(update_data).eq("id", user_id).execute()
                    
                    # Log admin action
                    try:
                        from core.security_monitor import SecurityMonitor
                        if admin_id:
                            SecurityMonitor.log_user_action(
                                admin_id,
                                'admin_user_update',
                                success=True,
                                metadata={
                                    'target_user_id': user_id,
                                    'target_username': current_user.get('username'),
                                    'changes': changes_log,
                                    'updated_fields': list(update_data.keys())
                                }
                            )
                    except Exception as log_error:
                        logger.warning(f"Error logging admin action: {log_error}")
                    
                    return True, f"✅ Đã cập nhật {len(changes_log)} thay đổi: {', '.join(changes_log)}"
                except Exception as direct_error:
                    logger.error(f"Direct update also failed: {direct_error}")
                    return False, f"Lỗi: Không thể cập nhật user. Có thể do RLS policy. {str(direct_error)}"
            
            return True, f"✅ Đã cập nhật {len(changes_log)} thay đổi: {', '.join(changes_log)}"
        else:
            return True, "ℹ️ Không có thay đổi nào"
    
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return False, f"Lỗi: {str(e)}"

def admin_update_user_role(user_id: int, new_role: str) -> Tuple[bool, str]:
    """
    Update user role (user/admin/moderator).
    
    Returns: (success, message)
    """
    return admin_update_user_comprehensive(user_id, role=new_role)

def admin_update_user_plan_and_tier(user_id: int, new_plan: str, new_tier: Optional[str] = None) -> Tuple[bool, str]:
    """
    Update user plan (free/premium) and tier (basic/premium/pro).
    If plan='free', tier will be set to None.
    If plan='premium' and tier=None, default to 'premium'.
    
    Returns: (success, message)
    """
    return admin_update_user_comprehensive(user_id, plan=new_plan, premium_tier=new_tier)

def admin_update_user_coins(user_id: int, new_coins: int, reason: str = "Admin adjustment") -> Tuple[bool, str]:
    """
    Update user coins directly.
    Logs action to ActivityLog.
    
    Returns: (success, message)
    """
    return admin_update_user_comprehensive(user_id, coins=new_coins)

def admin_update_user_streak(user_id: int, new_streak: int, reason: str = "Admin override") -> Tuple[bool, str]:
    """
    Update user streak (admin override).
    Logs action to ActivityLog.
    
    Returns: (success, message)
    """
    return admin_update_user_comprehensive(user_id, streak=new_streak)

def admin_reset_user_ai_usage(user_id: int, feature_type: Optional[str] = None) -> Tuple[bool, str]:
    """
    Reset AI usage for user.
    If feature_type=None, reset all features for the current month.
    
    Returns: (success, message)
    """
    if not supabase:
        return False, "No database connection"
    
    try:
        # Get admin_id for logging
        admin_id = None
        try:
            admin_id = st.session_state.user_info.get('id')
        except:
            pass
        
        # Check if user is premium
        user_res = supabase.table("Users").select("plan").eq("id", user_id).single().execute()
        if not user_res.data:
            return False, "User not found"
        
        user_plan = user_res.data.get('plan', 'free')
        
        if user_plan == 'premium':
            # Reset monthly usage - delete ActivityLog entries for AI usage this month
            from core.timezone_utils import get_vn_start_of_month_utc
            start_of_month = get_vn_start_of_month_utc()
            
            # Delete ActivityLog entries for AI features this month
            ai_action_types = ['ai_listening', 'ai_speaking', 'ai_reading', 'ai_writing', 'ai_general']
            
            if feature_type:
                # Reset specific feature
                action_type_map = {
                    'listening': 'ai_listening',
                    'speaking': 'ai_speaking',
                    'reading': 'ai_reading',
                    'writing': 'ai_writing'
                }
                action_type = action_type_map.get(feature_type, f'ai_{feature_type}')
                if action_type in ai_action_types:
                    supabase.table("ActivityLog")\
                        .delete()\
                        .eq("user_id", user_id)\
                        .eq("action_type", action_type)\
                        .gte("created_at", start_of_month)\
                        .execute()
                    msg = f"Đã reset AI usage cho feature '{feature_type}'"
                else:
                    return False, f"Feature type không hợp lệ: {feature_type}"
            else:
                # Reset all AI features
                for action_type in ai_action_types:
                    supabase.table("ActivityLog")\
                        .delete()\
                        .eq("user_id", user_id)\
                        .eq("action_type", action_type)\
                        .gte("created_at", start_of_month)\
                        .execute()
                msg = "Đã reset tất cả AI usage cho tháng này"
        else:
            # Free user - reset session state usage (not stored in DB)
            msg = "Free user - AI usage được reset tự động mỗi ngày. Không cần reset thủ công."
        
        # Log admin action
        try:
            from core.security_monitor import SecurityMonitor
            if admin_id:
                SecurityMonitor.log_user_action(
                    admin_id,
                    'admin_reset_ai_usage',
                    success=True,
                    metadata={
                        'target_user_id': user_id,
                        'feature_type': feature_type or 'all',
                        'user_plan': user_plan
                    }
                )
        except:
            pass
        
        return True, msg
    
    except Exception as e:
        logger.error(f"Error resetting AI usage: {e}")
        return False, f"Lỗi: {str(e)}"