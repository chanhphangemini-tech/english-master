"""View components for Shop page."""
import streamlit as st
from typing import Dict, Any, List
import time


def render_shop_header(coins: int) -> None:
    """Render shop header with user coins.
    
    Args:
        coins: User's current coin balance
    """
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            st.metric("💰 Coin hiện có", coins)
        with c2:
            st.info("💡 **Mẹo:** Hoàn thành bài học hàng ngày để nhận thêm Coin!")


def render_shop_navigation(default_tab: str = "shop") -> str:
    """Render shop navigation tabs.
    
    Args:
        default_tab: Default selected tab
        
    Returns:
        Selected tab value
    """
    # CSS for styled radio buttons
    st.markdown("""
    <style>
    div.row-widget.stRadio > div {flex-direction: row; gap: 10px; justify-content: center; margin-bottom: 20px;}
    div.row-widget.stRadio > div > label {
        background-color: #ffffff; padding: 10px 20px; border-radius: 8px; 
        cursor: pointer; border: 1px solid #e0e0e0; font-weight: 500;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.3s;
    }
    div.row-widget.stRadio > div > label:hover {
        background-color: #f8f9fa; border-color: #b0b0b0;
    }
    div.row-widget.stRadio > div > label[data-baseweb="radio"] {
        background-color: #e3f2fd; border-color: #2196f3; color: #1565c0; font-weight: bold;
        box-shadow: 0 2px 4px rgba(33, 150, 243, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    options = ["🛍️ Mua Sắm", "🎒 Kho Đồ Của Tôi"]
    default_idx = 0
    
    return st.radio("Shop Nav", options, index=default_idx, label_visibility="collapsed")


def render_shop_items(items: List[Dict[str, Any]], user_id: int, coins: int) -> None:
    """Render shop items in grid layout with category tabs.
    
    Args:
        items: List of shop items
        user_id: Current user ID
        coins: User's current coin balance
    """
    from core.data import buy_shop_item
    from core.theme import render_empty_state
    
    if not items:
        render_empty_state("Cửa hàng đang đóng cửa để nhập hàng.", "🚧")
        return
    
    # Category tabs
    cat_tabs = st.tabs(["Tất cả", "🎨 Giao diện", "🛠️ Công cụ", "💎 Thời trang"])
    
    categories = {
        "Tất cả": None,
        "🎨 Giao diện": ["theme"],
        "🛠️ Công cụ": ["streak_freeze", "powerup"],
        "💎 Thời trang": ["avatar_frame", "title"]
    }
    
    for idx, (cat_name, cat_types) in enumerate(categories.items()):
        with cat_tabs[idx]:
            # Filter items by type
            filtered_items = (
                [i for i in items if i['type'] in cat_types] 
                if cat_types 
                else items
            )
            
            if not filtered_items:
                st.info(f"Chưa có vật phẩm nào trong mục {cat_name}")
            else:
                # Grid layout
                cols = st.columns(3)
                for i, item in enumerate(filtered_items):
                    with cols[i % 3]:
                        render_shop_item_card(item, user_id, coins, idx, i)


def render_shop_item_card(
    item: Dict[str, Any], 
    user_id: int, 
    coins: int, 
    tab_idx: int, 
    item_idx: int
) -> None:
    """Render a single shop item card.
    
    Args:
        item: Item data
        user_id: Current user ID
        coins: User's current coin balance
        tab_idx: Tab index for unique key
        item_idx: Item index for unique key
    """
    from core.data import buy_shop_item
    
    with st.container(border=True):
        st.markdown(
            f"<div style='font-size:40px; text-align:center;'>"
            f"{item.get('icon', '📦')}</div>", 
            unsafe_allow_html=True
        )
        st.markdown(f"**{item['name']}**")
        st.caption(item['description'])
        st.markdown(
            f"**Giá:** <span style='color:#d63031; font-weight:bold'>"
            f"{item['cost']} 🪙</span>", 
            unsafe_allow_html=True
        )
        
        can_afford = coins >= item['cost']
        if st.button(
            "Mua ngay", 
            key=f"buy_{tab_idx}_{item['id']}", 
            type="primary" if can_afford else "secondary", 
            disabled=not can_afford
        ):
            with st.spinner("Đang giao dịch..."):
                success, msg = buy_shop_item(user_id, item['id'], item['cost'])
                if success:
                    st.success(msg)
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)


def render_user_inventory(inventory: List[Dict[str, Any]], user_id: int) -> None:
    """Render user's inventory with categories.
    
    Args:
        inventory: List of user's inventory items
        user_id: Current user ID
    """
    from core.theme import render_empty_state
    from core.data import activate_user_theme, use_item
    
    if not inventory:
        render_empty_state("Bạn chưa mua vật phẩm nào.", "🎒")
        return
    
    # Group items by type
    items_by_type = {
        'theme': [],
        'avatar_frame': [],
        'title': [],
        'streak_freeze': [],
        'powerup': []
    }
    
    for inv in inventory:
        item_info = inv.get('ShopItems')
        if not item_info:
            continue
        item_type = item_info.get('type', 'powerup')
        if item_type in items_by_type:
            items_by_type[item_type].append((inv, item_info))
        else:
            items_by_type['powerup'].append((inv, item_info))
    
    # Category names
    category_names = {
        'theme': '🎨 Giao diện',
        'avatar_frame': '🖼️ Khung Avatar',
        'title': '🏷️ Danh hiệu',
        'streak_freeze': '❄️ Bảo vệ Streak',
        'powerup': '⚡ Vật phẩm khác'
    }
    
    # Render each category
    for item_type, items_list in items_by_type.items():
        if items_list:
            st.subheader(category_names.get(item_type, '📦 Khác'))
            for inv, item_info in items_list:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 3, 2])
                    with c1:
                        st.markdown(
                            f"<div style='font-size:30px;'>"
                            f"{item_info.get('icon', '📦')}</div>", 
                            unsafe_allow_html=True
                        )
                    with c2:
                        st.markdown(f"**{item_info['name']}** (x{inv['quantity']})")
                        st.caption(item_info.get('description', ''))
                    with c3:
                        render_inventory_action_button(inv, item_info, user_id)
            st.divider()


def render_inventory_action_button(
    inv: Dict[str, Any], 
    item_info: Dict[str, Any], 
    user_id: int
) -> None:
    """Render action button for inventory item.
    
    Args:
        inv: Inventory entry
        item_info: Item information
        user_id: Current user ID
    """
    from core.data import activate_user_theme, use_item
    
    item_type = item_info['type']
    
    if item_type == 'theme':
        is_active = inv.get('is_active', False)
        if is_active:
            st.button(
                "✅ Đang sử dụng", 
                key=f"active_{inv['id']}", 
                disabled=True)
        else:
            if st.button("🎨 Áp dụng Theme", key=f"use_{inv['id']}"):
                activate_user_theme(user_id, inv['item_id'])
                # Set theme value in session state
                theme_value = item_info.get('value', '')
                st.session_state.active_theme_value = theme_value
                st.success(f"Đã đổi giao diện! Theme: {theme_value}")
                time.sleep(1)
                st.cache_data.clear()  # Clear cache to refresh
                # Force rerun to apply theme immediately
                st.rerun()
    elif item_type == 'streak_freeze':
        st.info("Tự động dùng khi mất chuỗi.")
    elif item_type == 'avatar_frame':
        # Avatar frame - vĩnh viễn
        current_frame = st.session_state.user_info.get('active_avatar_frame')
        is_active = current_frame == item_info.get('value')
        
        if is_active:
            st.button(
                "✅ Đang sử dụng", 
                key=f"active_frame_{inv['id']}", 
                disabled=True)
        else:
            if st.button("🖼️ Kích hoạt khung", key=f"use_frame_{inv['id']}"):
                msg = use_item(user_id, inv['id'])
                if msg and ("thành công" in msg.lower() or "kích hoạt" in msg.lower()):
                    # Reload user_info from database
                    from core.database import supabase
                    try:
                        user_res = supabase.table("Users").select("*").eq("id", int(user_id)).single().execute()
                        if user_res.data:
                            st.session_state.user_info.update(user_res.data)
                    except Exception as e:
                        print(f"Error reloading user_info: {e}")
                    st.success(msg)
                    time.sleep(1)
                    st.cache_data.clear()  # Clear cache
                    st.rerun()
                else:
                    st.error(msg if msg else "Lỗi không xác định")
    
    elif item_type == 'title':
        # Title - vĩnh viễn
        current_title = st.session_state.user_info.get('active_title')
        is_active = current_title == item_info.get('value')
        
        if is_active:
            st.button(
                "✅ Đang sử dụng", 
                key=f"active_title_{inv['id']}", 
                disabled=True)
        else:
            if st.button("🏷️ Kích hoạt danh hiệu", key=f"use_title_{inv['id']}"):
                msg = use_item(user_id, inv['id'])
                if msg and ("thành công" in msg.lower() or "kích hoạt" in msg.lower()):
                    # Reload user_info from database
                    from core.database import supabase
                    try:
                        user_res = supabase.table("Users").select("*").eq("id", int(user_id)).single().execute()
                        if user_res.data:
                            st.session_state.user_info.update(user_res.data)
                    except Exception as e:
                        print(f"Error reloading user_info: {e}")
                    st.success(msg)
                    time.sleep(1)
                    st.cache_data.clear()  # Clear cache
                    st.rerun()
                else:
                    st.error(msg if msg else "Lỗi không xác định")
    
    elif item_type == 'powerup':
        # Powerup items - vật phẩm tiêu hao với thời gian
        is_active = inv.get('is_active', False)
        expires_at = inv.get('expires_at')
        
        if is_active and expires_at:
            # Calculate remaining time
            from core.timezone_utils import get_vn_now_utc
            from datetime import datetime, timezone
            try:
                expires = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                now = datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00'))
                
                if expires > now:
                    remaining = expires - now
                    hours_left = int(remaining.total_seconds() / 3600)
                    minutes_left = int((remaining.total_seconds() % 3600) / 60)
                    time_str = f"{hours_left}h {minutes_left}m" if hours_left > 0 else f"{minutes_left}m"
                    
                    st.button(
                        f"⚡ Đang sử dụng (Còn: {time_str})", 
                        key=f"active_powerup_{inv['id']}", 
                        disabled=True)
                else:
                    # Expired, can use again
                    if st.button("⚡ Sử dụng", key=f"use_powerup_{inv['id']}"):
                        msg = use_item(user_id, inv['id'])
                        if msg and ("thành công" in msg.lower() or "kích hoạt" in msg.lower()):
                            # Reload user_info
                            from core.database import supabase
                            try:
                                user_res = supabase.table("Users").select("*").eq("id", int(user_id)).single().execute()
                                if user_res.data:
                                    st.session_state.user_info.update(user_res.data)
                            except:
                                pass
                            st.success(msg)
                            time.sleep(1)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(msg if msg else "Lỗi không xác định")
            except:
                # If error parsing, show active button
                st.button(
                    "⚡ Đang sử dụng", 
                    key=f"active_powerup_{inv['id']}", 
                    disabled=True)
        else:
            # Not active, can use
            if st.button("⚡ Sử dụng", key=f"use_powerup_{inv['id']}"):
                msg = use_item(user_id, inv['id'])
                if msg and ("thành công" in msg.lower() or "kích hoạt" in msg.lower()):
                    # Reload user_info
                    from core.database import supabase
                    try:
                        user_res = supabase.table("Users").select("*").eq("id", int(user_id)).single().execute()
                        if user_res.data:
                            st.session_state.user_info.update(user_res.data)
                    except:
                        pass
                    st.success(msg)
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg if msg else "Lỗi không xác định")
    
    else:
        # Unknown item type
        st.info(f"Loại vật phẩm: {item_type}")


def render_premium_section() -> None:
    """Render premium subscription section with pricing plans."""
    # Header Banner
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #003366 0%, #0056b3 100%); border-radius: 15px; color: white; margin-bottom: 30px;">
        <h1 style="color: #FFD700; margin-bottom: 10px;">👑 ENGLISH MASTER PREMIUM</h1>
        <p style="font-size: 1.2em; opacity: 0.9;">Đầu tư cho kiến thức là khoản đầu tư sinh lời nhất.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Comparison table
    st.markdown("### 🆚 So sánh quyền lợi")
    
    st.markdown("""
    <style>
    .comp-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    .comp-table th, .comp-table td { padding: 12px 10px; text-align: left; border-bottom: 1px solid #eee; }
    .comp-table th { background-color: #f8f9fa; color: #333; font-weight: bold; text-align: center; }
    .comp-table td.check { color: #2ecc71; font-weight: bold; text-align: center; }
    .comp-table td.cross { color: #e74c3c; text-align: center; }
    .comp-table td.center { text-align: center; }
    .comp-table tr:hover { background-color: #f1f1f1; }
    .comp-table .tier-header { font-weight: bold; }
    .comp-table .tier-basic { color: #3498db; }
    .comp-table .tier-premium { color: #d35400; }
    .comp-table .tier-pro { color: #9b59b6; }
    </style>
    
    <table class="comp-table">
        <thead>
            <tr>
                <th style="width: 30%;">Tính năng</th>
                <th style="width: 17.5%;" class="tier-header">Free</th>
                <th style="width: 17.5%;" class="tier-header tier-basic">Basic</th>
                <th style="width: 17.5%;" class="tier-header tier-premium">Premium</th>
                <th style="width: 17.5%;" class="tier-header tier-pro">Pro</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>📚 Học từ vựng (SRS)</td>
                <td class="center">20 từ/ngày</td>
                <td class="check">♾️ Không giới hạn</td>
                <td class="check">♾️ Không giới hạn</td>
                <td class="check">♾️ Không giới hạn</td>
            </tr>
            <tr>
                <td>🤖 Luyện kỹ năng AI</td>
                <td class="center">5 lượt/ngày</td>
                <td class="center">300 lượt/tháng<br><small>(≈10/ngày)</small></td>
                <td class="center tier-premium">600 lượt/tháng<br><small>(≈20/ngày)</small></td>
                <td class="center tier-pro">1200 lượt/tháng<br><small>(≈40/ngày)</small></td>
            </tr>
            <tr>
                <td>⚡ Mua thêm lượt AI (Top-up)</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
            </tr>
            <tr>
                <td>🧪 Bài học Ngữ pháp</td>
                <td class="center">Chỉ A1, A2</td>
                <td class="check">🔓 A1-C2</td>
                <td class="check">🔓 A1-C2</td>
                <td class="check">🔓 A1-C2</td>
            </tr>
            <tr>
                <td>🎯 Kiểm tra lại trình độ</td>
                <td class="cross">❌</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
            </tr>
            <tr>
                <td>📊 Xuất dữ liệu (CSV/Excel)</td>
                <td class="cross">❌</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
            </tr>
            <tr>
                <td>💎 Khung Avatar & Danh hiệu VIP</td>
                <td class="cross">❌</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
                <td class="check">✅</td>
            </tr>
            <tr>
                <td>🚫 Quảng cáo</td>
                <td class="center">Có thể có</td>
                <td class="check">✅ Không quảng cáo</td>
                <td class="check">✅ Không quảng cáo</td>
                <td class="check">✅ Không quảng cáo</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.divider()
    
    # Show current tier for Premium users
    user_info = st.session_state.get("user_info", {})
    if user_info.get("plan") == "premium":
        from services.premium_usage_service import get_user_premium_tier, get_premium_tier_limit
        current_tier = get_user_premium_tier(user_info.get("id"))
        tier_display = {'basic': 'Basic (300 lượt/tháng)', 'premium': 'Premium (600 lượt/tháng)', 'pro': 'Pro (1200 lượt/tháng)'}.get(current_tier, 'Premium (600 lượt/tháng)')
        st.info(f"👑 Gói hiện tại của bạn: **{tier_display}**")
    
    st.subheader("💎 Chọn gói phù hợp với bạn")
    
    st.info("💰 **Giá áp dụng cho gói Premium (600 lượt/tháng)**. Liên hệ Admin để chọn gói Basic (300 lượt) hoặc Pro (1200 lượt).")
    
    render_pricing_plans()
    
    st.info("ℹ️ Hiện tại hệ thống thanh toán đang bảo trì. Vui lòng liên hệ Admin để nâng cấp thủ công.")
    
    # Top-Up Section (for ALL users - Free + Premium)
    st.divider()
    render_topup_section(user_info.get("id"))


def render_pricing_plans() -> None:
    """Render pricing plan cards."""
    p1, p2, p3 = st.columns(3)
    
    with p1:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>📅 1 Tháng</h3>", unsafe_allow_html=True)
            st.markdown("<h2 style='color:#007BFF; text-align: center;'>49.000đ</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray; font-size: 0.85em;'>Premium: 600 lượt/tháng</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Thanh toán linh hoạt</p>", unsafe_allow_html=True)
            st.write("")  # Spacer
            st.button("Chọn gói 1 tháng")
    
    with p2:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>🚀 6 Tháng</h3>", unsafe_allow_html=True)
            st.markdown("<h2 style='color:#007BFF; text-align: center;'>239.000đ</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #2ecc71; font-weight: bold;'>Tiết kiệm 19%</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 0.9em;'>~39.833đ/tháng</p>", unsafe_allow_html=True)
            st.button("Chọn gói 6 tháng", type="primary")
    
    with p3:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>🌟 1 Năm</h3>", unsafe_allow_html=True)
            st.markdown("<h2 style='color:#007BFF; text-align: center;'>379.000đ</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #e67e22; font-weight: bold;'>Tiết kiệm 36%</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 0.9em;'>~31.583đ/tháng</p>", unsafe_allow_html=True)
            st.button("Chọn gói 1 năm")

def render_topup_section(user_id: int) -> None:
    """Render AI top-up purchase section for ALL users (Free + Premium)."""
    from services.premium_usage_service import get_premium_ai_usage_monthly, purchase_ai_topup, get_topup_balance
    
    st.subheader("⚡ Mua thêm lượt AI")
    
    user_info = st.session_state.get("user_info", {})
    user_plan = user_info.get("plan", "free")
    
    if user_plan == "premium":
        st.caption("Người dùng gói Basic, Premium hoặc Pro có thể mua thêm lượt AI khi hết limit. Top-up sẽ hết hạn vào cuối tháng.")
        
        # Show current usage for Premium users
        usage = get_premium_ai_usage_monthly(user_id)
        tier_display = {'basic': 'Basic', 'premium': 'Premium', 'pro': 'Pro'}.get(usage.get('tier', 'premium'), 'Premium')
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Lượt còn lại (Base)", f"{usage.get('remaining', 0)}/{usage.get('limit', 0)}", 
                     delta=f"{tier_display} Tier")
        with col2:
            st.metric("Lượt Top-up", usage.get('topup_balance', 0), 
                     delta=f"Tổng: {usage.get('total_remaining', 0)} lượt")
    else:
        st.caption("Người dùng Free có thể mua thêm lượt AI để tiếp tục học. Top-up sẽ hết hạn sau 90 ngày (Pay-as-you-go).")
        
        # Show current usage for Free users
        from core.premium import initialize_ai_usage_tracker, AI_USAGE_LIMIT
        
        initialize_ai_usage_tracker()
        topup_balance = get_topup_balance(user_id)
        total_daily_usage = sum(st.session_state.get('ai_usage_counts', {}).values())
        
        col1, col2 = st.columns(2)
        with col1:
            remaining_daily = max(0, AI_USAGE_LIMIT * 4 - total_daily_usage)  # 4 features * 5 each = 20 total
            st.metric("Lượt còn lại hôm nay", f"{remaining_daily}/{AI_USAGE_LIMIT * 4}", 
                     delta="5 lượt/tính năng")
        with col2:
            st.metric("Lượt Top-up", topup_balance, 
                     delta=f"Hết hạn sau 90 ngày")
    
    st.markdown("---")
    
    # Top-up packages
    st.markdown("### 📦 Gói Top-up")
    topup_packages = [
        {"amount": 50, "price": 9000, "per_unit": 0.18},
        {"amount": 100, "price": 15000, "per_unit": 0.15, "popular": True},
        {"amount": 200, "price": 25000, "per_unit": 0.125},
        {"amount": 500, "price": 55000, "per_unit": 0.11, "best_value": True}
    ]
    
    cols = st.columns(4)
    for idx, pkg in enumerate(topup_packages):
        with cols[idx]:
            with st.container(border=True):
                if pkg.get("popular"):
                    st.markdown("<div style='text-align: center; color: #e67e22; font-weight: bold; margin-bottom: 10px;'>🔥 Phổ biến nhất</div>", unsafe_allow_html=True)
                elif pkg.get("best_value"):
                    st.markdown("<div style='text-align: center; color: #2ecc71; font-weight: bold; margin-bottom: 10px;'>⭐ Giá tốt nhất</div>", unsafe_allow_html=True)
                else:
                    # Add spacer for packages without badge to maintain equal height
                    st.markdown("<div style='text-align: center; margin-bottom: 10px; height: 25px; visibility: hidden;'>Spacer</div>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='text-align: center; margin: 10px 0;'>{pkg['amount']} lượt</h4>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='color:#007BFF; text-align: center; margin: 15px 0;'>{pkg['price']:,}đ</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-size: 0.85em; color: gray; margin: 10px 0;'>{pkg['per_unit']:.3f}đ/lượt</p>", unsafe_allow_html=True)
                st.write("")  # Additional spacing before button
                
                btn_type = "primary" if (pkg.get("popular") or pkg.get("best_value")) else "secondary"
                if st.button(f"Mua {pkg['amount']} lượt", key=f"topup_{pkg['amount']}", 
                           type=btn_type, width='stretch'):
                    with st.spinner("Đang xử lý..."):
                        success, msg = purchase_ai_topup(user_id, pkg['amount'], pkg['price'])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
