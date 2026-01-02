"""Helper functions for admin shop management"""
import streamlit as st
from core.database import supabase

def get_all_shop_items():
    """Lấy tất cả shop items"""
    try:
        if not supabase:
            return []
        result = supabase.table("ShopItems").select("*").order("id").execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Lỗi lấy danh sách vật phẩm: {e}")
        return []

def create_shop_item(name, description, icon, cost, item_type, value=None):
    """Tạo vật phẩm mới"""
    try:
        if not supabase:
            return False, "Không có kết nối database"
        
        item_data = {
            "name": name,
            "description": description,
            "icon": icon,
            "cost": int(cost),
            "type": item_type
        }
        if value is not None:
            item_data["value"] = value
        
        result = supabase.table("ShopItems").insert(item_data).execute()
        return True, "Tạo vật phẩm thành công!"
    except Exception as e:
        return False, f"Lỗi tạo vật phẩm: {e}"

def update_shop_item(item_id, name=None, description=None, icon=None, cost=None, item_type=None, value=None):
    """Cập nhật vật phẩm"""
    try:
        if not supabase:
            return False, "Không có kết nối database"
        
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if icon is not None:
            update_data["icon"] = icon
        if cost is not None:
            update_data["cost"] = int(cost)
        if item_type is not None:
            update_data["type"] = item_type
        if value is not None:
            update_data["value"] = value
        
        if not update_data:
            return False, "Không có dữ liệu để cập nhật"
        
        result = supabase.table("ShopItems").update(update_data).eq("id", item_id).execute()
        return True, "Cập nhật vật phẩm thành công!"
    except Exception as e:
        return False, f"Lỗi cập nhật vật phẩm: {e}"

def delete_shop_item(item_id):
    """Xóa vật phẩm"""
    try:
        if not supabase:
            return False, "Không có kết nối database"
        
        # Check if item is in any user inventory
        inventory_check = supabase.table("UserInventory").select("id").eq("item_id", item_id).limit(1).execute()
        if inventory_check.data:
            return False, "Không thể xóa vật phẩm này vì đã có người dùng sở hữu!"
        
        result = supabase.table("ShopItems").delete().eq("id", item_id).execute()
        return True, "Xóa vật phẩm thành công!"
    except Exception as e:
        return False, f"Lỗi xóa vật phẩm: {e}"

