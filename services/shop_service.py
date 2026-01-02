from core.database import supabase
import streamlit as st

def get_shop_items(user_id=None):
    """Lấy danh sách vật phẩm trong Shop, ẩn các vật phẩm vĩnh viễn đã mua.
    
    Args:
        user_id: User ID để filter các vật phẩm vĩnh viễn đã mua (optional)
    """
    if not supabase: return []
    try:
        res = supabase.table("ShopItems").select("*").order("cost").execute()
        items = res.data if res.data else []
        
        # Nếu có user_id, filter ra các vật phẩm vĩnh viễn đã mua
        if user_id:
            try:
                # Lấy danh sách vật phẩm vĩnh viễn user đã sở hữu
                inventory_res = supabase.table("UserInventory").select("item_id, ShopItems!inner(type)").eq("user_id", int(user_id)).execute()
                owned_permanent_items = set()
                
                if inventory_res.data:
                    for inv in inventory_res.data:
                        item_type = inv.get('ShopItems', {}).get('type')
                        # Các loại vật phẩm vĩnh viễn: theme, avatar_frame, title
                        if item_type in ['theme', 'avatar_frame', 'title']:
                            owned_permanent_items.add(inv['item_id'])
                
                # Filter ra các vật phẩm vĩnh viễn đã mua
                # Giữ lại: items không phải vĩnh viễn HOẶC items vĩnh viễn chưa mua
                items = [
                    item for item in items 
                    if item.get('type') not in ['theme', 'avatar_frame', 'title'] 
                    or item['id'] not in owned_permanent_items
                ]
            except Exception as e:
                print(f"Error filtering owned items: {e}")
                # Nếu có lỗi, vẫn trả về tất cả items
        
        return items
    except: return []

@st.cache_data(ttl=30, show_spinner=False)  # Cache 30s - inventory changes infrequently
def get_user_inventory(user_id):
    """
    Lấy kho đồ của user kèm thông tin vật phẩm và trạng thái active.
    Cached for 30 seconds to improve performance.
    Note: Cache will be invalidated when user buys/activates items.
    """
    if not supabase: return []
    try:
        # Join UserInventory with ShopItems (is_active field is included by default)
        res = supabase.table("UserInventory").select("*, ShopItems(name, type, value, icon, description)").eq("user_id", int(user_id)).execute()
        inventory_items = res.data if res.data else []
        
        # Get active theme from inventory (is_active = true for theme type)
        # The activate_theme RPC should set is_active in UserInventory
        # No need to modify is_active here, just use what's in the database
        
        # Get active powerup info from Users table (including item name from ShopItems)
        try:
            user_res = supabase.table("Users").select("active_powerup_inventory_id, active_powerup_expires_at, active_powerup_type").eq("id", int(user_id)).single().execute()
            if user_res.data:
                active_inventory_id = user_res.data.get('active_powerup_inventory_id')
                active_expires_at = user_res.data.get('active_powerup_expires_at')
                active_powerup_type = user_res.data.get('active_powerup_type')
                
                # Mark active items in inventory and get item name
                for item in inventory_items:
                    if item.get('id') == active_inventory_id:
                        item['is_active'] = True
                        item['expires_at'] = active_expires_at
                        item['active_powerup_type'] = active_powerup_type
        except:
            pass
        
        return inventory_items
    except Exception as e:
        print(f"Inventory error: {e}")
        return []

def buy_shop_item(user_id, item_id, cost):
    """Gọi RPC để mua vật phẩm."""
    if not supabase: return False, "No DB"
    try:
        res = supabase.rpc("buy_item", {
            "p_user_id": int(user_id),
            "p_item_id": item_id,
            "p_cost": cost
        }).execute()
        
        if res.data == 'Success':
            # Security Monitor: Log successful purchase
            try:
                from core.security_monitor import SecurityMonitor
                SecurityMonitor.log_user_action(user_id, 'shop_buy', success=True, metadata={'item_id': item_id, 'cost': cost})
            except Exception:
                pass
            
            return True, "Mua thành công!"
        elif res.data == 'Not enough coins':
            # Security Monitor: Log failed purchase (not enough coins)
            try:
                from core.security_monitor import SecurityMonitor
                SecurityMonitor.log_user_action(user_id, 'shop_buy', success=False, metadata={'item_id': item_id, 'reason': 'not_enough_coins'})
            except Exception:
                pass
            
            return False, "Bạn không đủ Coin."
        else:
            # Security Monitor: Log failed purchase
            try:
                from core.security_monitor import SecurityMonitor
                SecurityMonitor.log_user_action(user_id, 'shop_buy', success=False, metadata={'item_id': item_id, 'error': str(res.data)})
            except Exception:
                pass
            
            return False, f"Lỗi giao dịch: {res.data}"
    except Exception as e:
        error_msg = str(e)
        
        # Security Monitor: Log error
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'shop_buy', success=False, metadata={'item_id': item_id, 'error': error_msg})
        except Exception:
            pass
        
        # Check if RPC function doesn't exist
        if 'does not exist' in error_msg.lower() or 'function' in error_msg.lower():
            print(f"WARNING: RPC function 'buy_item' may not exist in database. Please run db_create_rpc_functions.sql")
            return False, "Hệ thống đang bảo trì. Vui lòng thử lại sau."
        return False, f"Lỗi: {error_msg}"

def activate_user_theme(user_id, item_id):
    """Kích hoạt theme.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    if not supabase: return False
    try:
        supabase.rpc("activate_theme", {"p_user_id": int(user_id), "p_item_id": item_id}).execute()
        return True
    except Exception as e:
        error_msg = str(e)
        # Log error but don't use logger since this module might not have it
        print(f"Error activating theme for user {user_id}: {error_msg}")
        # Check if RPC function doesn't exist
        if 'does not exist' in error_msg.lower() or 'function' in error_msg.lower():
            print(f"WARNING: RPC function 'activate_theme' may not exist in database. Please run db_create_rpc_functions.sql")
        return False

def check_and_use_freeze_streak(user_id):
    """Kiểm tra và sử dụng Freeze Streak nếu có. Trả về True nếu cứu được streak."""
    if not supabase: return False
    try:
        # Tìm item freeze streak có quantity > 0
        res = supabase.table("UserInventory").select("id, quantity, ShopItems!inner(type)").eq("user_id", int(user_id)).eq("ShopItems.type", "streak_freeze").gt("quantity", 0).limit(1).execute()
        
        if res.data:
            inv_item = res.data[0]
            # Trừ 1 cái
            new_qty = inv_item['quantity'] - 1
            supabase.table("UserInventory").update({"quantity": new_qty}).eq("id", inv_item['id']).execute()
            return True
    except Exception as e:
        print(f"Freeze check error: {e}")
    return False

def use_item(user_id, inventory_id):
    """Sử dụng vật phẩm từ inventory
    
    Args:
        user_id: User ID
        inventory_id: UserInventory ID
        
    Returns:
        str: Message kết quả
    """
    if not supabase: 
        return "Lỗi: Không có kết nối database"
    
    try:
        # Lấy thông tin inventory item
        inv_res = supabase.table("UserInventory").select("*, ShopItems(*)").eq("id", inventory_id).eq("user_id", int(user_id)).single().execute()
        
        if not inv_res.data:
            return "Lỗi: Không tìm thấy vật phẩm"
        
        inv_item = inv_res.data
        item_info = inv_item.get('ShopItems')
        
        if not item_info:
            return "Lỗi: Không tìm thấy thông tin vật phẩm"
        
        item_type = item_info.get('type')
        item_value = item_info.get('value')
        
        if item_type == 'avatar_frame':
            # Activate avatar frame (vĩnh viễn)
            # Update Users table
            supabase.table("Users").update({
                "active_avatar_frame": item_value
            }).eq("id", int(user_id)).execute()
            
            return "Đã kích hoạt khung avatar thành công!"
            
        elif item_type == 'title':
            # Activate title (vĩnh viễn)
            # Update Users table
            supabase.table("Users").update({
                "active_title": item_value
            }).eq("id", int(user_id)).execute()
            
            return "Đã kích hoạt danh hiệu thành công!"
            
        elif item_type == 'streak_freeze':
            # Streak freeze tự động dùng, không cần gọi từ đây
            return "Vật phẩm này tự động được sử dụng khi cần."
            
        elif item_type == 'powerup':
            # Powerup items (vật phẩm tiêu hao với thời gian)
            # Get duration from item value (default 24 hours if not specified)
            duration_hours = 24  # Default 24 hours
            try:
                if item_value and item_value.isdigit():
                    duration_hours = int(item_value)
            except:
                pass
            
            # Calculate expiration time (dùng VN timezone)
            from datetime import datetime, timezone, timedelta
            from core.timezone_utils import get_vn_now_utc
            now_utc = datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00'))
            expires_at = now_utc + timedelta(hours=duration_hours)
            
            # Update Users table to mark item as active
            supabase.table("Users").update({
                "active_powerup_type": item_type,
                "active_powerup_expires_at": expires_at.isoformat(),
                "active_powerup_inventory_id": inventory_id
            }).eq("id", int(user_id)).execute()
            
            # Reduce quantity
            current_qty = inv_item.get('quantity', 1)
            if current_qty > 1:
                supabase.table("UserInventory").update({
                    "quantity": current_qty - 1
                }).eq("id", inventory_id).execute()
            else:
                # If only 1 left, delete the inventory item after activation
                supabase.table("UserInventory").delete().eq("id", inventory_id).execute()
            
            return f"Đã kích hoạt {item_info.get('name', 'vật phẩm')} thành công! (Còn lại {duration_hours}h)"
            
        else:
            return f"Loại vật phẩm '{item_type}' chưa được hỗ trợ."
            
    except Exception as e:
        return f"Lỗi khi sử dụng vật phẩm: {str(e)}"