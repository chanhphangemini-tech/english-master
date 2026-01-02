"""Helper functions for admin feedback management - moved from 14_Gop_Y.py"""
import streamlit as st
import pandas as pd
from datetime import datetime
from core.data import supabase

def get_all_feedback():
    """Lấy tất cả feedback (admin only)"""
    try:
        if not supabase:
            return pd.DataFrame()
        
        result = supabase.table("feedback").select("*").order("created_at", desc=True).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            # Map English types back to Vietnamese for display
            type_display_map = {
                "bug": "🐞 Báo lỗi",
                "feature": "💡 Đề xuất tính năng",
                "compliment": "❤️ Lời khen",
                "other": "Khác"
            }
            if 'type' in df.columns:
                df['type'] = df['type'].map(type_display_map).fillna(df['type'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi lấy dữ liệu: {e}")
        return pd.DataFrame()

def get_all_users_list():
    """Lấy danh sách tất cả users"""
    try:
        if not supabase:
            return []
        result = supabase.table("Users").select("id, username, name, email, plan, coins").order("username").execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Lỗi lấy danh sách users: {e}")
        return []

def get_user_subscription(user_id):
    """Lấy thông tin subscription của user"""
    try:
        if not supabase:
            return None
        result = supabase.table("Subscriptions").select("*").eq("user_id", user_id).eq("status", "active").order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None

def update_user_premium(user_id, plan_type, end_date, coins=None):
    """Cập nhật premium và coin cho user"""
    try:
        if not supabase:
            return False
        
        # Update user plan
        update_data = {"plan": plan_type}
        if coins is not None:
            update_data["coins"] = coins
        
        supabase.table("Users").update(update_data).eq("id", user_id).execute()
        
        # Update or create subscription
        existing = get_user_subscription(user_id)
        
        # Prepare subscription data (try without updated_at first if it fails)
        sub_update_data = {
            "plan_type": plan_type,
            "end_date": end_date,
            "status": "active"
        }
        
        sub_insert_data = {
            "user_id": user_id,
            "plan_type": plan_type,
            "start_date": datetime.now().isoformat(),
            "end_date": end_date,
            "status": "active"
        }
        
        # Try with updated_at first, if fails try without
        try:
            if existing:
                sub_update_data["updated_at"] = datetime.now().isoformat()
                supabase.table("Subscriptions").update(sub_update_data).eq("id", existing["id"]).execute()
            else:
                sub_insert_data["updated_at"] = datetime.now().isoformat()
                supabase.table("Subscriptions").insert(sub_insert_data).execute()
        except Exception as sub_error:
            # If error mentions updated_at, try without it
            error_str = str(sub_error).lower()
            if "updated_at" in error_str:
                try:
                    # Remove updated_at and try again
                    if existing:
                        sub_update_data.pop("updated_at", None)
                        supabase.table("Subscriptions").update(sub_update_data).eq("id", existing["id"]).execute()
                    else:
                        sub_insert_data.pop("updated_at", None)
                        supabase.table("Subscriptions").insert(sub_insert_data).execute()
                except Exception as retry_error:
                    st.error(f"Lỗi cập nhật subscription: {retry_error}")
                    return False
            else:
                raise sub_error
        
        # Clear cache for get_user_stats to show updated coin immediately
        try:
            # Clear all cached data (Streamlit method)
            st.cache_data.clear()
        except Exception:
            pass  # Ignore cache clearing errors
        
        return True
    except Exception as e:
        st.error(f"Lỗi cập nhật: {e}")
        return False

def get_all_feature_flags():
    """Lấy tất cả feature flags"""
    try:
        if not supabase:
            return pd.DataFrame()
        result = supabase.table("featureflags").select("*").order("feature_key").execute()
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi lấy feature flags: {e}")
        return pd.DataFrame()

def update_feature_flag(feature_key, is_enabled, maintenance_message=None):
    """Cập nhật feature flag"""
    try:
        if not supabase:
            return False
        update_data = {"is_enabled": is_enabled}
        if maintenance_message:
            update_data["maintenance_message"] = maintenance_message
        result = supabase.table("featureflags").update(update_data).eq("feature_key", feature_key).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Lỗi cập nhật: {e}")
        return False

