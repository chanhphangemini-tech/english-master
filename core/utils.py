from datetime import datetime, timedelta, timezone
import streamlit as st
import base64

def get_vietnam_time():
    """Trả về thời gian hiện tại theo múi giờ Việt Nam (UTC+7)."""
    return datetime.now(timezone(timedelta(hours=7)))

def format_date_vn(date_obj):
    """Định dạng ngày tháng kiểu Việt Nam (dd/mm/yyyy)."""
    if not date_obj: return ""
    return date_obj.strftime("%d/%m/%Y")

def play_sound(sound_type="correct"):
    """
    Phát âm thanh hiệu ứng.
    Types: 'correct', 'wrong', 'win', 'click'
    """
    # Sử dụng URL âm thanh ngắn từ các nguồn CDN miễn phí hoặc base64
    sounds = {
        "correct": "https://cdn.pixabay.com/download/audio/2021/08/04/audio_bb630cc098.mp3?filename=short-success-sound-glockenspiel-treasure-video-game-6346.mp3",
        "wrong": "https://cdn.pixabay.com/download/audio/2021/08/04/audio_c6ccf3232f.mp3?filename=negative-beeps-6008.mp3",
        "win": "https://cdn.pixabay.com/download/audio/2021/08/09/audio_16678756b7.mp3?filename=success-fanfare-trumpets-6185.mp3",
        "click": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3?filename=mouse-click-153941.mp3"
    }
    
    url = sounds.get(sound_type)
    if url:
        # Hack: Nhúng audio autoplay ẩn
        st.markdown(f"""
            <audio autoplay style="display:none;">
                <source src="{url}" type="audio/mpeg">
            </audio>
        """, unsafe_allow_html=True)
