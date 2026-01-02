"""
Script để tạo Supabase Storage bucket 'tts-audio'
Note: Supabase Python client không có method create_bucket() trực tiếp
Cần tạo thủ công qua Dashboard hoặc REST API
"""
import streamlit as st
from core.database import supabase
import requests
import os

def create_bucket_via_api():
    """
    Tạo bucket qua Supabase REST API (nếu có quyền)
    """
    try:
        # Lấy URL và key từ secrets
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        # API endpoint
        api_url = f"{url}/storage/v1/bucket"
        
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "name": "tts-audio",
            "public": True,  # Public bucket
            "file_size_limit": None,
            "allowed_mime_types": ["audio/mpeg", "audio/mp3", "audio/wav"]
        }
        
        response = requests.post(api_url, json=data, headers=headers)
        
        if response.status_code == 200:
            print(f"[OK] Bucket 'tts-audio' created successfully!")
            return True
        elif response.status_code == 409:
            print(f"[OK] Bucket 'tts-audio' already exists!")
            return True
        else:
            print(f"[ERROR] Failed to create bucket: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error creating bucket: {e}")
        return False

if __name__ == "__main__":
    print("Creating Supabase Storage bucket 'tts-audio'...")
    print("Note: If this fails, create bucket manually in Supabase Dashboard")
    print("=" * 60)
    
    # Try to create via API
    success = create_bucket_via_api()
    
    if not success:
        print("\n" + "=" * 60)
        print("[WARNING] Manual setup required:")
        print("1. Go to Supabase Dashboard -> Storage")
        print("2. Click 'New bucket'")
        print("3. Name: tts-audio")
        print("4. Set to PUBLIC")
        print("5. Save")
