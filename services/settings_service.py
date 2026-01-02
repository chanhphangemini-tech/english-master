"""
System Settings Service
Handles system-wide configurable settings (Admin only)
"""

import streamlit as st
from core.database import supabase
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def get_system_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a system setting value by key.
    
    Args:
        key: Setting key
        default: Default value if setting not found
        
    Returns:
        Setting value or default
    """
    if not supabase:
        logger.warning("Supabase client not initialized")
        return default
    
    try:
        res = supabase.table("SystemSettings")\
            .select("setting_value")\
            .eq("setting_key", key)\
            .single()\
            .execute()
        
        if res.data:
            return res.data.get("setting_value", default)
        return default
    except Exception as e:
        logger.error(f"Error getting system setting '{key}': {e}")
        return default


def get_all_system_settings() -> List[Dict[str, Any]]:
    """
    Get all system settings.
    
    Returns:
        List of all settings
    """
    if not supabase:
        logger.warning("Supabase client not initialized")
        return []
    
    try:
        res = supabase.table("SystemSettings")\
            .select("*")\
            .order("setting_key")\
            .execute()
        
        return res.data if res.data else []
    except Exception as e:
        logger.error(f"Error getting all system settings: {e}")
        return []


def update_system_setting(key: str, value: str, updated_by: int) -> bool:
    """
    Update a system setting value.
    
    Args:
        key: Setting key
        value: New value
        updated_by: User ID of admin making the change
        
    Returns:
        True if successful, False otherwise
    """
    if not supabase:
        logger.warning("Supabase client not initialized")
        return False
    
    try:
        res = supabase.table("SystemSettings")\
            .update({
                "setting_value": value,
                "updated_by": updated_by,
                "updated_at": "now()"
            })\
            .eq("setting_key", key)\
            .execute()
        
        if res.data:
            logger.info(f"System setting '{key}' updated by user {updated_by}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating system setting '{key}': {e}")
        return False


def get_email_config() -> Dict[str, str]:
    """
    Get email configuration from database.
    Falls back to st.secrets if not found in database.
    
    Returns:
        Dictionary with email config:
        - sender: Email address
        - password: App password
        - smtp_server: SMTP server
        - smtp_port: SMTP port
        - enabled: Whether email is enabled
    """
    config = {}
    
    # Try to get from database first
    try:
        if supabase:
            settings = get_all_system_settings()
            settings_dict = {s['setting_key']: s['setting_value'] for s in settings}
            
            config['sender'] = settings_dict.get('email_sender')
            config['password'] = settings_dict.get('email_sender_password')
            config['smtp_server'] = settings_dict.get('email_smtp_server', 'smtp.gmail.com')
            config['smtp_port'] = int(settings_dict.get('email_smtp_port', 587))
            config['enabled'] = settings_dict.get('email_enabled', 'true').lower() == 'true'
            
            # If we have both sender and password from database, return it
            if config.get('sender') and config.get('password'):
                logger.info("Using email config from database")
                return config
    except Exception as e:
        logger.warning(f"Error getting email config from database: {e}")
    
    # Fallback to st.secrets
    try:
        secrets_email = st.secrets.get("email", {})
        config['sender'] = secrets_email.get("sender")
        config['password'] = secrets_email.get("password")
        config['smtp_server'] = secrets_email.get("smtp_server", "smtp.gmail.com")
        config['smtp_port'] = int(secrets_email.get("smtp_port", 587))
        config['enabled'] = secrets_email.get("enabled", True)
        
        if config.get('sender') and config.get('password'):
            logger.info("Using email config from secrets.toml")
            return config
    except Exception as e:
        logger.warning(f"Error getting email config from secrets: {e}")
    
    # If both failed, return empty config
    logger.warning("No email configuration found")
    return {
        'sender': None,
        'password': None,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'enabled': False
    }


def update_email_config(sender: str, password: str, updated_by: int) -> bool:
    """
    Update email configuration in database.
    
    Args:
        sender: Sender email address
        password: Email app password
        updated_by: Admin user ID
        
    Returns:
        True if successful
    """
    if not supabase:
        return False
    
    try:
        # Update sender
        update_system_setting('email_sender', sender, updated_by)
        
        # Update password
        update_system_setting('email_sender_password', password, updated_by)
        
        logger.info(f"Email config updated by user {updated_by}")
        return True
    except Exception as e:
        logger.error(f"Error updating email config: {e}")
        return False


def toggle_email_enabled(enabled: bool, updated_by: int) -> bool:
    """
    Enable or disable email notifications.
    
    Args:
        enabled: True to enable, False to disable
        updated_by: Admin user ID
        
    Returns:
        True if successful
    """
    value = 'true' if enabled else 'false'
    return update_system_setting('email_enabled', value, updated_by)

