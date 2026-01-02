from core.database import supabase
from datetime import datetime, timezone

def get_chat_sessions(user_id):
    """Lấy danh sách các phiên chat của người dùng."""
    if not supabase: return []
    try:
        res = supabase.table("ChatSessions").select("*").eq("user_id", int(user_id)).order("updated_at", desc=True).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Error getting chat sessions: {e}")
        return []

def get_chat_messages(session_id):
    """Lấy toàn bộ tin nhắn của một phiên chat."""
    if not supabase: return []
    try:
        res = supabase.table("ChatMessages").select("*").eq("session_id", str(session_id)).order("created_at", desc=False).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Error getting chat messages: {e}")
        return []

def create_chat_session(user_id, title):
    """Tạo một phiên chat mới và trả về object session."""
    if not supabase: return None
    try:
        res = supabase.table("ChatSessions").insert({
            "user_id": int(user_id),
            "title": title
        }).select("*").single().execute()
        if res.data:
            return res.data
    except Exception as e:
        print(f"Error creating chat session: {e}")
    return None

def add_chat_message(session_id, role, content):
    """Thêm một tin nhắn mới vào phiên chat."""
    if not supabase: return False
    try:
        supabase.table("ChatMessages").insert({"session_id": str(session_id), "role": role, "content": content}).execute()
        # Cập nhật timestamp của session cha để sắp xếp
        from core.timezone_utils import get_vn_now_utc
        supabase.table("ChatSessions").update({"updated_at": get_vn_now_utc()}).eq("id", str(session_id)).execute()
        return True
    except Exception as e:
        print(f"Error adding chat message: {e}")
        return False