"""
Premium Usage Service - Tracking và Rate Limiting cho Premium Users
Bảo vệ chi phí API khi Premium users sử dụng AI features
Hỗ trợ Tier Pricing (Basic/Premium/Pro) và Top-Up System
"""
import streamlit as st
from core.database import supabase
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from core.timezone_utils import get_vn_now_utc, get_vn_start_of_month_utc

logger = logging.getLogger(__name__)

# Premium Tier AI Usage Limits
PREMIUM_TIER_LIMITS = {
    'basic': 300,    # Basic: 300 requests/tháng
    'premium': 600,  # Premium: 600 requests/tháng (increased for better value)
    'pro': 1200      # Pro: 1200 requests/tháng (increased as anchor tier)
}

PREMIUM_TIER_WARNING_THRESHOLDS = {
    'basic': 240,    # 80% of 300
    'premium': 480,  # 80% of 600
    'pro': 960       # 80% of 1200
}

def get_premium_tier_limit(tier: str) -> int:
    """Lấy limit cho tier cụ thể"""
    return PREMIUM_TIER_LIMITS.get(tier, PREMIUM_TIER_LIMITS['premium'])

def get_premium_tier_warning(tier: str) -> int:
    """Lấy warning threshold cho tier cụ thể"""
    return PREMIUM_TIER_WARNING_THRESHOLDS.get(tier, PREMIUM_TIER_WARNING_THRESHOLDS['premium'])

def has_premium_subscription(user_id: int = None, user_plan: str = None) -> bool:
    """
    Check if user has premium subscription (basic/premium/pro).
    
    Args:
        user_id: User ID (optional, if provided will fetch from DB)
        user_plan: User plan string (optional, if provided will use directly)
    
    Returns:
        True if user has basic/premium/pro plan, False otherwise
    """
    if user_plan:
        return user_plan.lower() in ('basic', 'premium', 'pro')
    
    if not supabase or not user_id:
        return False
    
    try:
        res = supabase.table("Users").select("plan").eq("id", int(user_id)).maybe_single().execute()
        if res and hasattr(res, 'data') and res.data:
            plan = res.data.get('plan', 'free')
            return plan.lower() in ('basic', 'premium', 'pro')
    except Exception as e:
        logger.error(f"Error checking premium subscription for user {user_id}: {e}")
    
    return False

def get_user_premium_tier(user_id: int) -> Optional[str]:
    """Lấy premium tier của user (basic/premium/pro)"""
    if not supabase or not user_id:
        return None
    
    try:
        res = supabase.table("Users").select("premium_tier, plan").eq("id", int(user_id)).maybe_single().execute()
        if res and hasattr(res, 'data') and res.data:
            plan = res.data.get('plan', 'free')
            # Check if user has premium subscription (basic/premium/pro)
            if plan.lower() in ('basic', 'premium', 'pro'):
                # For basic/premium/pro, tier is the plan name or premium_tier
                tier = res.data.get('premium_tier') or plan.lower()
                # Ensure tier is valid
                if tier in ('basic', 'premium', 'pro'):
                    return tier
            return None  # Not premium user
    except Exception as e:
        logger.error(f"Error getting premium tier for user {user_id}: {e}")
    
    return None

def get_topup_balance(user_id: int) -> int:
    """
    Lấy số lượt AI còn lại từ top-up purchases (cho cả Free và Premium users)
    
    Returns:
        int: Tổng số lượt top-up còn lại (chưa dùng hết và chưa hết hạn)
    """
    if not supabase or not user_id:
        return 0
    
    try:
        now = get_vn_now_utc()
        
        # Lấy tất cả top-ups còn hiệu lực (chưa hết hạn và chưa dùng hết)
        # Filter: expires_at > now (chưa hết hạn) để query chính xác hơn
        result = supabase.table("AIUsageTopUp").select("amount, used_count, expires_at").eq(
            "user_id", user_id
        ).gt("expires_at", now).execute()
        
        if not result.data:
            return 0
        
        total_available = 0
        for topup in result.data:
            amount = topup.get('amount', 0)
            used_count = topup.get('used_count', 0)
            expires_at = topup.get('expires_at')
            
            # Check if top-up is still valid (not expired)
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                now_dt = datetime.fromisoformat(now.replace('Z', '+00:00'))
                if expires_dt > now_dt:
                    total_available += max(0, amount - used_count)
        
        return total_available
    except Exception as e:
        logger.error(f"Error getting top-up balance for user {user_id}: {e}")
        return 0

def use_topup_credit(user_id: int, count: int = 1) -> bool:
    """
    Sử dụng credit từ top-up (FIFO - First In First Out)
    
    Returns:
        bool: True nếu sử dụng thành công
    """
    if not supabase or not user_id or count <= 0:
        return False
    
    try:
        now = get_vn_now_utc()
        start_of_month = get_vn_start_of_month_utc()
        
        # Lấy top-ups còn hiệu lực, sắp xếp theo purchase_date (FIFO)
        # Filter: expires_at > now (chưa hết hạn) để query chính xác hơn
        result = supabase.table("AIUsageTopUp").select("id, amount, used_count, expires_at, purchase_date").eq(
            "user_id", user_id
        ).gt("expires_at", now).order("purchase_date", desc=False).execute()
        
        if not result.data:
            return False
        
        remaining_to_use = count
        for topup in result.data:
            if remaining_to_use <= 0:
                break
            
            topup_id = topup['id']
            amount = topup.get('amount', 0)
            used_count = topup.get('used_count', 0)
            
            available = amount - used_count
            if available > 0:
                use_this = min(available, remaining_to_use)
                new_used_count = used_count + use_this
                
                # Update used_count
                supabase.table("AIUsageTopUp").update({
                    "used_count": new_used_count
                }).eq("id", topup_id).execute()
                
                remaining_to_use -= use_this
        
        return remaining_to_use == 0  # Success if all credits were used
    except Exception as e:
        logger.error(f"Error using top-up credit for user {user_id}: {e}")
        return False

def track_premium_ai_usage(user_id: int, feature_type: str, success: bool = True, metadata: Dict = None) -> bool:
    """
    Track AI usage cho Premium users vào database
    
    Logic: Dùng top-up TRƯỚC, chỉ khi hết top-up mới dùng base limit
    
    Args:
        user_id: ID của user
        feature_type: Loại tính năng AI (listening, speaking, reading, writing, etc.)
        success: Thành công hay thất bại
        metadata: Thông tin bổ sung (prompt_length, tokens, etc.)
    
    Returns:
        bool: True nếu track thành công
    """
    if not supabase or not user_id:
        return False
    
    # Don't track failed requests
    if not success:
        return False
    
    try:
        # PRIORITY 1: Check top-up balance FIRST (user đã trả tiền cho top-up)
        topup_balance = get_topup_balance(user_id)
        
        if topup_balance > 0:
            # Use top-up credit (priority - user đã trả tiền)
            if use_topup_credit(user_id, 1):
                # Successfully used top-up → Don't track to ActivityLog
                # Top-up credits are separate from base subscription limit
                return True
            else:
                # Top-up usage failed (shouldn't happen, but log it)
                logger.warning(f"Top-up credit usage failed for user {user_id}, falling back to base limit")
        
        # PRIORITY 2: No top-up available or top-up failed → use base subscription limit
        # Track to ActivityLog (this counts against base monthly limit)
        supabase.table("ActivityLog").insert({
            "user_id": user_id,
            "action_type": "ai_call_premium",
            "value": 1,
            "metadata": {
                **(metadata or {}),
                "feature_type": feature_type,
                "plan": "premium",
                "used_topup": False
            }
        }).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error tracking premium AI usage for user {user_id}: {e}")
        return False

def get_premium_ai_usage_monthly(user_id: int) -> Dict[str, int]:
    """
    Lấy số lượng AI requests của Premium user trong tháng hiện tại (không tính top-up)
    
    Returns:
        Dict với keys: 'count', 'limit', 'remaining', 'topup_balance', 'total_remaining', 'warning', 'tier'
    """
    if not supabase or not user_id:
        tier = 'premium'
        limit = get_premium_tier_limit(tier)
        return {'count': 0, 'limit': limit, 'remaining': limit, 'topup_balance': 0, 'total_remaining': limit, 'warning': False, 'tier': tier}
    
    try:
        # Get user tier
        tier = get_user_premium_tier(user_id)
        if not tier:
            # Not a premium user
            return {'count': 0, 'limit': 0, 'remaining': 0, 'topup_balance': 0, 'total_remaining': 0, 'warning': False, 'tier': None}
        
        limit = get_premium_tier_limit(tier)
        warning_threshold = get_premium_tier_warning(tier)
        
        # Tính từ đầu tháng (VN timezone) đến hiện tại
        start_of_month = get_vn_start_of_month_utc()
        now = get_vn_now_utc()
        
        # Đếm số lượng AI calls trong tháng (base subscription, không tính top-up)
        result = supabase.table("ActivityLog").select("id", count="exact").eq(
            "user_id", user_id
        ).eq("action_type", "ai_call_premium").gte(
            "created_at", start_of_month
        ).lte("created_at", now).execute()
        
        count = result.count if result.count is not None else 0
        
        # Get top-up balance
        topup_balance = get_topup_balance(user_id)
        
        # Calculate remaining (base limit - count)
        remaining_base = max(0, limit - count)
        
        # Total remaining = base remaining + top-up balance
        total_remaining = remaining_base + topup_balance
        
        warning = count >= warning_threshold
        
        return {
            'count': count,
            'limit': limit,
            'remaining': remaining_base,
            'topup_balance': topup_balance,
            'total_remaining': total_remaining,
            'warning': warning,
            'tier': tier
        }
    except Exception as e:
        logger.error(f"Error getting premium AI usage for user {user_id}: {e}")
        tier = 'premium'
        limit = get_premium_tier_limit(tier)
        return {'count': 0, 'limit': limit, 'remaining': limit, 'topup_balance': 0, 'total_remaining': limit, 'warning': False, 'tier': tier}

def can_premium_use_ai(user_id: int) -> Tuple[bool, str]:
    """
    Kiểm tra xem Premium user có thể sử dụng AI feature không (bao gồm cả top-up)
    
    Returns:
        Tuple (allowed: bool, message: str)
        - allowed: True nếu được phép, False nếu đã hết limit (cả base và top-up)
        - message: Thông báo về usage hiện tại
    """
    usage = get_premium_ai_usage_monthly(user_id)
    
    if usage['tier'] is None:
        return False, "Bạn không phải Premium user."
    
    tier_display = {'basic': 'Basic', 'premium': 'Premium', 'pro': 'Pro'}.get(usage['tier'], 'Premium')
    
    # Check total remaining (base + top-up)
    if usage['total_remaining'] <= 0:
        return False, f"Bạn đã sử dụng hết {usage['limit']} lượt AI ({tier_display}) và top-up trong tháng này. Limit sẽ reset vào đầu tháng tới."
    
    # Build message
    message_parts = [f"Bạn còn {usage['total_remaining']} lượt AI"]
    if usage['topup_balance'] > 0:
        message_parts.append(f"(Base: {usage['remaining']}, Top-up: {usage['topup_balance']})")
    message_parts.append(f"trong tháng này ({tier_display} - {usage['limit']}/tháng).")
    
    if usage['warning']:
        return True, "⚠️ " + " ".join(message_parts)
    
    return True, " ".join(message_parts)

def purchase_ai_topup(user_id: int, amount: int, price_vnd: int) -> Tuple[bool, str]:
    """
    Mua top-up AI credits cho TẤT CẢ users (Free + Premium)
    
    Args:
        user_id: ID của user
        amount: Số lượng lượt AI muốn mua (50, 100, 200, 500)
        price_vnd: Giá tiền (VNĐ) - để log vào PaymentLogs
    
    Returns:
        Tuple (success: bool, message: str)
    
    Note:
        - Premium users: Top-up expires at end of month
        - Free users: Top-up expires after 90 days (more generous for pay-as-you-go)
    """
    if not supabase or not user_id or amount <= 0:
        return False, "Thông tin không hợp lệ."
    
    try:
        # Check user plan
        user_res = supabase.table("Users").select("plan").eq("id", user_id).single().execute()
        user_plan = user_res.data.get('plan', 'free') if user_res.data else 'free'
        
        # Calculate expiration date based on user plan
        from datetime import datetime
        import pytz
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_vn = datetime.now(vn_tz)
        
        if user_plan.lower() in ('basic', 'premium', 'pro'):
            # Premium users: Top-up expires at end of current month
            if now_vn.month == 12:
                last_day = datetime(now_vn.year + 1, 1, 1, 23, 59, 59, tzinfo=vn_tz) - timedelta(seconds=1)
            else:
                last_day = datetime(now_vn.year, now_vn.month + 1, 1, 23, 59, 59, tzinfo=vn_tz) - timedelta(seconds=1)
            expires_message = "Top-up sẽ hết hạn vào cuối tháng này."
        else:
            # Free users: Top-up expires after 90 days (more generous for pay-as-you-go)
            expires_at_vn = now_vn + timedelta(days=90)
            last_day = expires_at_vn.replace(hour=23, minute=59, second=59)
            expires_message = "Top-up sẽ hết hạn sau 90 ngày."
        
        expires_at_utc = last_day.astimezone(pytz.UTC).isoformat()
        
        # Insert top-up record
        result = supabase.table("AIUsageTopUp").insert({
            "user_id": user_id,
            "amount": amount,
            "expires_at": expires_at_utc,
            "used_count": 0
        }).execute()
        
        if result.data:
            # Log payment (optional)
            try:
                supabase.table("PaymentLogs").insert({
                    "user_id": user_id,
                    "amount": price_vnd,
                    "currency": "VND",
                    "provider": "topup",
                    "transaction_id": f"topup_{result.data[0]['id']}",
                    "status": "completed"
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to log payment for top-up: {e}")
            
            return True, f"Mua thành công {amount} lượt AI. {expires_message}"
        
        return False, "Không thể tạo top-up. Vui lòng thử lại."
    except Exception as e:
        logger.error(f"Error purchasing top-up for user {user_id}: {e}")
        return False, f"Lỗi khi mua top-up: {str(e)}"

def get_all_premium_users_usage(month: Optional[datetime] = None) -> list:
    """
    Lấy usage của tất cả Premium users trong tháng (cho Admin dashboard)
    
    Args:
        month: Tháng cần xem (nếu None thì dùng tháng hiện tại)
    
    Returns:
        List of dicts với keys: user_id, username, tier, usage_count, limit, topup_balance, total_remaining, percentage
    """
    if not supabase:
        return []
    
    try:
        # Tính tháng cần xem
        if month is None:
            start_of_month = get_vn_start_of_month_utc()
        else:
            # Tính start of month từ datetime object
            start_of_month_str = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            start_of_month = start_of_month_str
        
        now = get_vn_now_utc()
        
        # Lấy tất cả Premium users (basic/premium/pro)
        users_result = supabase.table("Users").select("id, username, name, premium_tier, plan").in_("plan", ["basic", "premium", "pro"]).execute()
        
        usage_list = []
        for user in users_result.data:
            user_id = user['id']
            plan = user.get('plan', 'premium')
            # Tier is premium_tier or plan name
            tier = user.get('premium_tier') or plan.lower()
            # Ensure tier is valid
            if tier not in ('basic', 'premium', 'pro'):
                tier = plan.lower() if plan.lower() in ('basic', 'premium', 'pro') else 'premium'
            limit = get_premium_tier_limit(tier)
            
            # Đếm AI calls trong tháng
            count_result = supabase.table("ActivityLog").select("id", count="exact").eq(
                "user_id", user_id
            ).eq("action_type", "ai_call_premium").gte(
                "created_at", start_of_month
            ).lte("created_at", now).execute()
            
            count = count_result.count if count_result.count is not None else 0
            topup_balance = get_topup_balance(user_id)
            total_remaining = max(0, limit - count) + topup_balance
            percentage = (count / limit * 100) if limit > 0 else 0
            
            usage_list.append({
                'user_id': user_id,
                'username': user.get('username', 'N/A'),
                'name': user.get('name', 'N/A'),
                'tier': tier,
                'usage_count': count,
                'limit': limit,
                'topup_balance': topup_balance,
                'total_remaining': total_remaining,
                'percentage': round(percentage, 1)
            })
        
        # Sort by usage_count descending
        usage_list.sort(key=lambda x: x['usage_count'], reverse=True)
        return usage_list
    except Exception as e:
        logger.error(f"Error getting all premium users usage: {e}")
        return []
