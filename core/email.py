import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def send_otp_email(to_email, otp):
    """Gửi email OTP thực tế sử dụng SMTP (Gmail).
    
    Email config được lấy từ database (SystemSettings) trước, 
    fallback về secrets.toml nếu không tìm thấy.
    """
    # Lấy cấu hình email từ database hoặc secrets
    try:
        from services.settings_service import get_email_config
        email_config = get_email_config()
        
        sender_email = email_config.get('sender')
        sender_password = email_config.get('password')
        smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        smtp_port = email_config.get('smtp_port', 587)
        enabled = email_config.get('enabled', True)
        
        if not enabled:
            logger.info("Email notifications are disabled in system settings")
            return False, "Gửi email đã bị tắt bởi Admin"
    except Exception as e:
        logger.warning(f"Error getting email config from database, falling back to secrets: {e}")
        # Fallback to old method
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = st.secrets.get("email", {}).get("sender")
        sender_password = st.secrets.get("email", {}).get("password")

    if not sender_email or not sender_password:
        print(f"📧 [SIMULATION] Sending OTP {otp} to {to_email} (Missing Secrets)")
        return True, "Mã OTP giả lập (Do chưa cấu hình Email Secrets)"

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "Mã xác thực English Master của bạn"
        body = f"Xin chào,\n\nMã OTP của bạn là: {otp}\n\nMã này có hiệu lực trong 5 phút. Vui lòng không chia sẻ cho ai khác."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True, "Đã gửi mã OTP qua Email!"
    except Exception as e:
        print(f"Email Error: {e}")
        return False, f"Lỗi gửi email: {str(e)}"