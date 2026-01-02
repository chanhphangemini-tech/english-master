import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

url = None
key = None

try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    logger.info("Loaded Supabase credentials from st.secrets")
except Exception:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    logger.info("Loaded Supabase credentials from environment variables")

supabase: Client = None
if url and key:
    try:
        supabase = create_client(url, key)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Supabase Connection Error: {e}")
        print(f"Supabase Connection Error: {e}")
