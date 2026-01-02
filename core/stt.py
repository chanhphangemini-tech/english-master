import speech_recognition as sr
import io

def recognize_audio(audio_bytes):
    """
    Chuyển đổi dữ liệu âm thanh (wav) thành văn bản sử dụng Google Web Speech API.
    
    Args:
        audio_bytes: Dữ liệu bytes của file âm thanh.
        
    Returns:
        Một tuple: (success, result_text)
        - success (bool): True nếu nhận dạng thành công, False nếu có lỗi.
        - result_text (str): Văn bản được nhận dạng hoặc thông báo lỗi.
    """
    r = sr.Recognizer()
    
    try:
        wav_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(wav_file) as source:
            audio_data = r.record(source)
        
        text = r.recognize_google(audio_data, language="en-US")
        return (True, text)
        
    except sr.UnknownValueError:
        return (False, "AI không thể nhận dạng được giọng nói của bạn.")
    except sr.RequestError as e:
        return (False, f"Lỗi dịch vụ nhận dạng giọng nói; {e}")
    except Exception as e:
        return (False, f"Đã có lỗi xảy ra: {e}")