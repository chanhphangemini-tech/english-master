import streamlit as st
from typing import Dict, Any

from core.theme_applier import apply_page_theme
from core.data import get_user_stats, get_shop_items, get_user_inventory
from core.debug_tools import render_debug_panel
from views.shop_view import (
    render_shop_header,
    render_shop_navigation,
    render_shop_items,
    render_user_inventory
)

# --- Auth Check ---
if not st.session_state.get("logged_in"):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth

st.title("🛒 Cửa Hàng (Shop)")
st.caption("Dùng Coin tích lũy được để đổi lấy các vật phẩm hỗ trợ và giao diện đẹp mắt.")

user_id: int = st.session_state.user_info.get("id")

# --- Header Stats ---
stats: Dict[str, Any] = get_user_stats(user_id)
coins: int = stats.get('coins', 0)

render_shop_header(coins)

# --- NAVIGATION ---
default_tab = "shop"
if "shop_active_tab" in st.session_state:
    del st.session_state.shop_active_tab  # Reset flag

selected_tab = render_shop_navigation(default_tab)

if selected_tab == "🛍️ Mua Sắm":
    items = get_shop_items(user_id)  # Pass user_id to filter owned permanent items
    render_shop_items(items, user_id, coins)
    
    # --- DEBUG --- (Disabled)
    # render_debug_panel("Shop Items", {
    #     "user_coins": coins,
    #     "items_count": len(items) if items else 0
    # })

elif selected_tab == "🎒 Kho Đồ Của Tôi":
    inventory = get_user_inventory(user_id)
    render_user_inventory(inventory, user_id)
