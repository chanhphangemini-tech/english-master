"""
Rate Limiter Module
Wrapper cho rate limiting functions từ database
"""
import streamlit as st
from core.database import supabase
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter sử dụng Supabase RPC functions"""
    
    @staticmethod
    def check_limit(user_id, endpoint, max_requests=60, window_minutes=1):
        """
        Kiểm tra rate limit cho user/endpoint
        
        Args:
            user_id: ID của user
            endpoint: Tên endpoint (vd: 'learn_vocab', 'pvp_create')
            max_requests: Số request tối đa trong window
            window_minutes: Thời gian window (phút)
            
        Returns:
            dict: {
                'allowed': bool,
                'remaining': int,
                'reset_at': str,
                'message': str
            }
        """
        if not supabase:
            return {'allowed': True, 'remaining': max_requests, 'message': 'Rate limiter disabled'}
        
        try:
            # Get IP address từ Streamlit (nếu có)
            ip_address = '0.0.0.0'  # Default
            try:
                # Streamlit context có thể có IP
                if hasattr(st, 'session_state') and hasattr(st.session_state, 'ip_address'):
                    ip_address = st.session_state.ip_address
            except:
                pass
            
            result = supabase.rpc('check_rate_limit', {
                'p_user_id': int(user_id),
                'p_ip_address': ip_address,
                'p_endpoint': endpoint,
                'p_max_requests': max_requests,
                'p_window_minutes': window_minutes
            }).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                return {
                    'allowed': data.get('allowed', True),
                    'remaining': data.get('remaining', max_requests),
                    'reset_at': data.get('reset_at'),
                    'message': data.get('message', '')
                }
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open - cho phép request nếu có lỗi
            return {'allowed': True, 'remaining': max_requests, 'message': 'Error checking rate limit'}
        
        return {'allowed': True, 'remaining': max_requests}
    
    @staticmethod
    def require_limit(endpoint, max_requests=60, window_minutes=1):
        """
        Decorator để enforce rate limiting
        
        Usage:
            @RateLimiter.require_limit('learn_vocab', max_requests=30, window_minutes=1)
            def learn_vocabulary():
                # Your code here
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get user_id từ session
                if not st.session_state.get('logged_in'):
                    return func(*args, **kwargs)
                
                user_id = st.session_state.user_info.get('id')
                if not user_id:
                    return func(*args, **kwargs)
                
                # Check rate limit
                result = RateLimiter.check_limit(user_id, endpoint, max_requests, window_minutes)
                
                if not result['allowed']:
                    st.error(f"⚠️ {result['message']}")
                    st.info(f"Bạn đã vượt quá giới hạn {max_requests} requests/{window_minutes} phút. Vui lòng thử lại sau.")
                    st.stop()
                
                # Show remaining requests (optional, for debugging)
                if result['remaining'] < 5:
                    st.caption(f"⚠️ Còn {result['remaining']} requests trong {window_minutes} phút")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator


class LoginLimiter:
    """Login attempt limiter để prevent brute force"""
    
    @staticmethod
    def check_attempts(username, max_attempts=5, lockout_minutes=15):
        """
        Kiểm tra login attempts
        
        Returns:
            dict: {
                'allowed': bool,
                'attempts_remaining': int,
                'blocked_until': str,
                'message': str
            }
        """
        if not supabase:
            return {'allowed': True, 'attempts_remaining': max_attempts}
        
        try:
            ip_address = '0.0.0.0'
            
            result = supabase.rpc('check_login_attempts', {
                'p_username': username,
                'p_ip_address': ip_address,
                'p_max_attempts': max_attempts,
                'p_lockout_minutes': lockout_minutes
            }).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
        except Exception as e:
            logger.error(f"Login check error: {e}")
        
        return {'allowed': True, 'attempts_remaining': max_attempts}
    
    @staticmethod
    def log_attempt(username, success, user_agent=None):
        """Log login attempt"""
        if not supabase:
            return
        
        try:
            ip_address = '0.0.0.0'
            
            supabase.rpc('log_login_attempt', {
                'p_username': username,
                'p_ip_address': ip_address,
                'p_success': success,
                'p_user_agent': user_agent
            }).execute()
        except Exception as e:
            logger.error(f"Log attempt error: {e}")


class AuditLogger:
    """Audit logging cho sensitive operations"""
    
    @staticmethod
    def log(user_id, action, resource_type=None, resource_id=None, details=None):
        """
        Log audit event
        
        Args:
            user_id: ID của user
            action: Loại action (vd: 'login', 'delete_user', 'buy_item')
            resource_type: Loại resource (vd: 'User', 'Vocabulary', 'ShopItem')
            resource_id: ID của resource
            details: Dict với thông tin chi tiết
        """
        if not supabase:
            return
        
        try:
            ip_address = '0.0.0.0'
            
            supabase.rpc('log_audit_event', {
                'p_user_id': int(user_id) if user_id else None,
                'p_action': action,
                'p_resource_type': resource_type,
                'p_resource_id': int(resource_id) if resource_id else None,
                'p_details': details,
                'p_ip_address': ip_address,
                'p_user_agent': None
            }).execute()
        except Exception as e:
            logger.error(f"Audit log error: {e}")
    
    @staticmethod
    def audit(action, resource_type=None):
        """
        Decorator để tự động log audit
        
        Usage:
            @AuditLogger.audit('delete_vocabulary', 'Vocabulary')
            def delete_vocab(vocab_id):
                # Your code here
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get user_id từ session
                user_id = None
                if st.session_state.get('logged_in'):
                    user_id = st.session_state.user_info.get('id')
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Log audit
                resource_id = kwargs.get('id') or (args[0] if len(args) > 0 else None)
                AuditLogger.log(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details={'function': func.__name__, 'args': str(args)[:200]}
                )
                
                return result
            return wrapper
        return decorator


# Convenience functions
def rate_limit(endpoint, max_requests=60, window_minutes=1):
    """Shorthand cho RateLimiter.require_limit"""
    return RateLimiter.require_limit(endpoint, max_requests, window_minutes)

def audit_log(action, resource_type=None):
    """Shorthand cho AuditLogger.audit"""
    return AuditLogger.audit(action, resource_type)


# Usage examples:
"""
# 1. Rate limiting trong functions
from core.rate_limiter import rate_limit

@rate_limit('learn_vocab', max_requests=30, window_minutes=1)
def learn_vocabulary_page():
    st.title("Học từ vựng")
    # Your code here

# 2. Login limiting
from core.rate_limiter import LoginLimiter

def login(username, password):
    # Check nếu bị block
    check = LoginLimiter.check_attempts(username)
    if not check['allowed']:
        st.error(check['message'])
        return False
    
    # Attempt login
    success = verify_password(username, password)
    
    # Log attempt
    LoginLimiter.log_attempt(username, success)
    
    return success

# 3. Audit logging
from core.rate_limiter import audit_log, AuditLogger

@audit_log('delete_vocabulary', 'Vocabulary')
def delete_vocabulary(vocab_id):
    # Your delete code
    pass

# Or manual logging
def buy_item(user_id, item_id):
    # Buy logic
    AuditLogger.log(
        user_id=user_id,
        action='buy_shop_item',
        resource_type='ShopItem',
        resource_id=item_id,
        details={'price': 100, 'item_name': 'Avatar Frame'}
    )
"""
