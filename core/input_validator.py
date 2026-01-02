"""
Input Validation Module
Validate và sanitize user inputs để prevent security issues
"""
import re
import html
from typing import Tuple, Optional
import streamlit as st
from core.database import supabase
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """Validator cho các loại input khác nhau"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate email address
        
        Returns:
            (is_valid, sanitized_email, message)
        """
        if not email or not email.strip():
            return False, None, "Email không được để trống"
        
        email = email.strip().lower()
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, None, "Email không hợp lệ"
        
        # Check length
        if len(email) > 255:
            return False, None, "Email quá dài"
        
        return True, email, "Email hợp lệ"
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate username
        - 3-20 ký tự
        - Chỉ chữ cái, số, underscore, dash
        
        Returns:
            (is_valid, sanitized_username, message)
        """
        if not username or not username.strip():
            return False, None, "Username không được để trống"
        
        username = username.strip().lower()
        
        # Check length
        if len(username) < 3:
            return False, None, "Username phải có ít nhất 3 ký tự"
        if len(username) > 20:
            return False, None, "Username không được quá 20 ký tự"
        
        # Check characters
        pattern = r'^[a-z0-9_-]+$'
        if not re.match(pattern, username):
            return False, None, "Username chỉ được chứa chữ cái, số, _ và -"
        
        # Check reserved words
        reserved = ['admin', 'root', 'system', 'null', 'undefined']
        if username in reserved:
            return False, None, "Username này không được sử dụng"
        
        return True, username, "Username hợp lệ"
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        - Ít nhất 8 ký tự
        - Có chữ hoa, chữ thường, số
        
        Returns:
            (is_valid, message)
        """
        if not password:
            return False, "Mật khẩu không được để trống"
        
        if len(password) < 8:
            return False, "Mật khẩu phải có ít nhất 8 ký tự"
        
        if len(password) > 128:
            return False, "Mật khẩu quá dài"
        
        # Check complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Mật khẩu phải có chữ hoa, chữ thường và số"
        
        return True, "Mật khẩu hợp lệ"
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """
        Sanitize text input để prevent XSS
        - Remove HTML tags
        - Escape special characters
        - Limit length
        
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Escape HTML entities
        text = html.escape(text)
        
        # Remove script-like patterns
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        # Trim whitespace
        text = text.strip()
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate URL
        
        Returns:
            (is_valid, sanitized_url, message)
        """
        if not url or not url.strip():
            return False, None, "URL không được để trống"
        
        url = url.strip()
        
        # Basic URL pattern
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        if not re.match(pattern, url):
            return False, None, "URL không hợp lệ"
        
        # Check length
        if len(url) > 2048:
            return False, None, "URL quá dài"
        
        return True, url, "URL hợp lệ"
    
    @staticmethod
    def validate_integer(value: any, min_val: int = None, max_val: int = None) -> Tuple[bool, Optional[int], str]:
        """
        Validate integer input
        
        Returns:
            (is_valid, integer_value, message)
        """
        try:
            val = int(value)
            
            if min_val is not None and val < min_val:
                return False, None, f"Giá trị phải >= {min_val}"
            
            if max_val is not None and val > max_val:
                return False, None, f"Giá trị phải <= {max_val}"
            
            return True, val, "Số hợp lệ"
        except (ValueError, TypeError):
            return False, None, "Không phải là số nguyên hợp lệ"
    
    @staticmethod
    def validate_with_db(value: str, validation_type: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate using database RPC function
        
        Args:
            value: Value to validate
            validation_type: 'email', 'username', 'text', 'url'
        
        Returns:
            (is_valid, sanitized_value, message)
        """
        if not supabase:
            # Fallback to local validation
            if validation_type == 'email':
                return InputValidator.validate_email(value)
            elif validation_type == 'username':
                return InputValidator.validate_username(value)
            elif validation_type == 'url':
                return InputValidator.validate_url(value)
            else:
                return True, InputValidator.sanitize_text(value), "OK"
        
        try:
            result = supabase.rpc('validate_input', {
                'p_input': value,
                'p_type': validation_type
            }).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0] if isinstance(result.data, list) else result.data
                if isinstance(data, dict):
                    return (
                        data.get('valid', False),
                        data.get('sanitized'),
                        data.get('message', '')
                    )
        except Exception as e:
            error_msg = str(e)
            # RPC is optional, use fallback
            if 'does not exist' in error_msg.lower() or 'function' in error_msg.lower():
                logger.debug(f"RPC function 'validate_input' not found. Using local validation.")
            else:
                logger.error(f"DB validation error: {e}")
        
        # Fallback to local validation
        return True, value, "OK"


class FormValidator:
    """Validator cho forms với nhiều fields"""
    
    def __init__(self):
        self.errors = {}
    
    def validate_field(self, field_name: str, value: any, validator_func, *args, **kwargs):
        """
        Validate một field và lưu error nếu có
        
        Args:
            field_name: Tên field
            value: Giá trị cần validate
            validator_func: Function để validate (vd: InputValidator.validate_email)
            *args, **kwargs: Arguments cho validator function
        
        Returns:
            bool: True nếu valid
        """
        result = validator_func(value, *args, **kwargs)
        
        if isinstance(result, tuple):
            is_valid = result[0]
            message = result[-1]
            
            if not is_valid:
                self.errors[field_name] = message
                return False
        
        return True
    
    def is_valid(self) -> bool:
        """Check nếu tất cả fields hợp lệ"""
        return len(self.errors) == 0
    
    def get_errors(self) -> dict:
        """Get dictionary của errors"""
        return self.errors
    
    def show_errors(self):
        """Display errors trong Streamlit"""
        if self.errors:
            for field, message in self.errors.items():
                st.error(f"**{field}**: {message}")


# Convenience decorators
def validate_input(input_type: str, param_name: str = None):
    """
    Decorator để validate function parameters
    
    Usage:
        @validate_input('email', 'email_param')
        def send_email(email_param):
            # email_param đã được validate
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get value from kwargs or args
            value = kwargs.get(param_name) if param_name else (args[0] if len(args) > 0 else None)
            
            # Validate
            if input_type == 'email':
                is_valid, sanitized, message = InputValidator.validate_email(value)
            elif input_type == 'username':
                is_valid, sanitized, message = InputValidator.validate_username(value)
            elif input_type == 'url':
                is_valid, sanitized, message = InputValidator.validate_url(value)
            elif input_type == 'text':
                sanitized = InputValidator.sanitize_text(value)
                is_valid = True
            else:
                is_valid = True
                sanitized = value
            
            if not is_valid:
                raise ValueError(message)
            
            # Replace value with sanitized version
            if param_name and param_name in kwargs:
                kwargs[param_name] = sanitized
            elif len(args) > 0:
                args = (sanitized,) + args[1:]
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Usage examples:
"""
# 1. Validate trong form
from core.input_validator import InputValidator, FormValidator

def register_form():
    with st.form("register"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Đăng ký"):
            validator = FormValidator()
            
            validator.validate_field("Username", username, InputValidator.validate_username)
            validator.validate_field("Email", email, InputValidator.validate_email)
            validator.validate_field("Password", password, InputValidator.validate_password)
            
            if validator.is_valid():
                st.success("Đăng ký thành công!")
            else:
                validator.show_errors()

# 2. Sanitize text input
from core.input_validator import InputValidator

user_comment = st.text_area("Bình luận")
safe_comment = InputValidator.sanitize_text(user_comment, max_length=500)

# 3. Validate với decorator
from core.input_validator import validate_input

@validate_input('email', 'email')
def send_welcome_email(email):
    # email đã được validate và sanitize
    send_email(email, "Welcome!")

# 4. Integer validation
from core.input_validator import InputValidator

age = st.number_input("Tuổi", min_value=0, max_value=150)
is_valid, validated_age, message = InputValidator.validate_integer(age, min_val=13, max_val=120)
if not is_valid:
    st.error(message)
"""
