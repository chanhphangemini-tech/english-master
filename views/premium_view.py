"""
Premium Subscription View
UI for Premium subscription management, tier selection, and pricing plans
"""
import streamlit as st
from typing import Dict, Any

def render_premium_page() -> None:
    """Render main premium subscription page with tier selection and pricing."""
    # Header Banner
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #003366 0%, #0056b3 100%); border-radius: 15px; color: white; margin-bottom: 30px;">
        <h1 style="color: #FFD700; margin-bottom: 10px;">⭐ ENGLISH MASTER - GÓI DỊCH VỤ</h1>
        <p style="font-size: 1.2em; opacity: 0.9;">Đầu tư cho kiến thức là khoản đầu tư sinh lời nhất.</p>
        <p style="font-size: 1em; opacity: 0.8; margin-top: 10px;">Chọn gói Basic, Premium hoặc Pro phù hợp với nhu cầu của bạn</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_info = st.session_state.get("user_info", {})
    user_id = user_info.get("id")
    current_plan = user_info.get("plan", "free")
    
    # Show current tier for Premium users
    if current_plan == "premium":
        from services.premium_usage_service import get_user_premium_tier
        current_tier = get_user_premium_tier(user_id)
        tier_display = {
            'basic': 'Basic (300 lượt/tháng)', 
            'premium': 'Premium (600 lượt/tháng)', 
            'pro': 'Pro (1200 lượt/tháng)'
        }.get(current_tier, 'Premium (600 lượt/tháng)')
        tier_emoji = {'basic': '🔵', 'premium': '🟠', 'pro': '🟣'}.get(current_tier, '🟠')
        st.info(f"{tier_emoji} Gói hiện tại của bạn: **{tier_display}**")
    
    # Comparison table
    render_comparison_table()
    
    st.divider()
    
    # Tier Selection
    st.subheader("💎 Chọn gói phù hợp với bạn")
    
    # Tier tabs
    tier_tabs = st.tabs(["🔵 Basic", "🟠 Premium", "🟣 Pro"])
    
    with tier_tabs[0]:
        render_tier_pricing("basic", 300, "39.000đ/tháng")
    
    with tier_tabs[1]:
        render_tier_pricing("premium", 600, "49.000đ/tháng", is_popular=True)
    
    with tier_tabs[2]:
        render_tier_pricing("pro", 1200, "69.000đ/tháng")
    
    st.info("ℹ️ Hiện tại hệ thống thanh toán đang bảo trì. Vui lòng liên hệ Admin để nâng cấp thủ công.")
    
    # Top-Up Section (for ALL users - Free + Premium)
    st.divider()
    render_topup_section(user_id)


def render_comparison_table() -> None:
    """Render comparison table for Free, Basic, Premium, Pro tiers."""
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


def render_tier_pricing(tier: str, ai_limit: int, monthly_price: str, is_popular: bool = False) -> None:
    """
    Render pricing plans for a specific tier.
    
    Args:
        tier: Tier name (basic, premium, pro)
        ai_limit: AI usage limit per month
        monthly_price: Monthly price display string
        is_popular: Whether this tier is marked as "Most Popular" (default: False)
    """
    tier_info = {
        "basic": {
            "name": "Basic",
            "color": "#3498db",
            "pricing": {
                1: {"price": 39000, "original": 39000},
                6: {"price": 189000, "original": 234000, "discount": 19},
                12: {"price": 299000, "original": 468000, "discount": 36}
            }
        },
        "premium": {
            "name": "Premium",
            "color": "#d35400",
            "pricing": {
                1: {"price": 49000, "original": 49000},
                6: {"price": 239000, "original": 294000, "discount": 19},
                12: {"price": 379000, "original": 588000, "discount": 36}
            }
        },
        "pro": {
            "name": "Pro",
            "color": "#9b59b6",
            "pricing": {
                1: {"price": 69000, "original": 69000},
                6: {"price": 339000, "original": 414000, "discount": 19},
                12: {"price": 539000, "original": 828000, "discount": 36}
            }
        }
    }
    
    info = tier_info.get(tier, tier_info["premium"])
    
    popular_badge = ""
    if is_popular:
        popular_badge = '<div style="background: linear-gradient(135deg, #e67e22 0%, #d35400 100%); color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold; margin-bottom: 10px; display: inline-block;">⭐ MOST POPULAR</div>'
    
    html_content = f'<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, {info["color"]}15 0%, {info["color"]}05 100%); border-radius: 10px; margin-bottom: 20px;">{popular_badge}<h3 style="color: {info["color"]}; margin-bottom: 10px;">{info["name"]} Plan</h3><p style="font-size: 1.1em; color: #333;">{ai_limit} lượt AI/tháng - {monthly_price}</p></div>'
    st.markdown(html_content, unsafe_allow_html=True)
    
    # Pricing cards - Ensure equal heights with consistent spacing
    p1, p2, p3 = st.columns(3)
    
    with p1:
        pricing_1 = info['pricing'][1]
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-bottom: 15px;'>📅 1 Tháng</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{info['color']}; text-align: center; margin: 15px 0;'>{pricing_1['price']:,}đ</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: gray; font-size: 0.85em; margin: 10px 0;'>{info['name']}: {ai_limit} lượt/tháng</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray; margin: 10px 0;'>Thanh toán linh hoạt</p>", unsafe_allow_html=True)
            # Add spacer to match height with discount cards
            st.markdown("<p style='text-align: center; margin: 10px 0; height: 25px; visibility: hidden;'>Spacer</p>", unsafe_allow_html=True)
            st.write("")  # Additional spacing
            st.button("Chọn gói 1 tháng", key=f"buy_{tier}_1m", width='stretch')
    
    with p2:
        pricing_6 = info['pricing'][6]
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-bottom: 15px;'>🚀 6 Tháng</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{info['color']}; text-align: center; margin: 15px 0;'>{pricing_6['price']:,}đ</h2>", unsafe_allow_html=True)
            if pricing_6.get('discount'):
                st.markdown(f"<p style='text-align: center; color: #2ecc71; font-weight: bold; margin: 10px 0;'>Tiết kiệm {pricing_6['discount']}%</p>", unsafe_allow_html=True)
            monthly = pricing_6['price'] / 6
            st.markdown(f"<p style='text-align: center; font-size: 0.9em; margin: 10px 0;'>~{monthly:,.0f}đ/tháng</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray; margin: 10px 0; height: 20px; visibility: hidden;'>Spacer</p>", unsafe_allow_html=True)
            st.write("")  # Additional spacing
            st.button("Chọn gói 6 tháng", key=f"buy_{tier}_6m", type="primary", width='stretch')
    
    with p3:
        pricing_12 = info['pricing'][12]
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-bottom: 15px;'>🌟 1 Năm</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{info['color']}; text-align: center; margin: 15px 0;'>{pricing_12['price']:,}đ</h2>", unsafe_allow_html=True)
            if pricing_12.get('discount'):
                st.markdown(f"<p style='text-align: center; color: #e67e22; font-weight: bold; margin: 10px 0;'>Tiết kiệm {pricing_12['discount']}%</p>", unsafe_allow_html=True)
            monthly = pricing_12['price'] / 12
            st.markdown(f"<p style='text-align: center; font-size: 0.9em; margin: 10px 0;'>~{monthly:,.0f}đ/tháng</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray; margin: 10px 0; height: 20px; visibility: hidden;'>Spacer</p>", unsafe_allow_html=True)
            st.write("")  # Additional spacing
            st.button("Chọn gói 1 năm", key=f"buy_{tier}_12m", width='stretch')


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
