"""
Export Service - Premium-exclusive features để export data
"""
import streamlit as st
import pandas as pd
import csv
import io
from typing import List, Dict, Any
from core.database import supabase
import logging

logger = logging.getLogger(__name__)

def export_vocabulary_csv(user_id: int) -> bytes:
    """
    Export user vocabulary với progress và SRS stats ra CSV file
    
    Returns:
        bytes: CSV file content
    """
    if not supabase or not user_id:
        return b""
    
    try:
        # Get user vocabulary với join Vocabulary table
        result = supabase.table("UserVocabulary").select(
            "*, Vocabulary(word, meaning, pronunciation, type, level, topic, example, example_translation)"
        ).eq("user_id", int(user_id)).execute()
        
        if not result.data:
            return b""
        
        # Prepare data for CSV
        rows = []
        for item in result.data:
            vocab = item.get('Vocabulary', {}) or {}
            rows.append({
                'Word': vocab.get('word', ''),
                'Meaning': vocab.get('meaning', ''),
                'Pronunciation': vocab.get('pronunciation', ''),
                'Type': vocab.get('type', ''),
                'Level': vocab.get('level', ''),
                'Topic': vocab.get('topic', ''),
                'Status': item.get('status', ''),
                'Streak': item.get('streak', 0),
                'Interval (days)': item.get('interval', 0),
                'Ease Factor': item.get('ease_factor', 2.5),
                'Last Reviewed': item.get('last_reviewed_at', ''),
                'Due Date': item.get('due_date', ''),
                'Example': vocab.get('example', ''),
                'Example Translation': vocab.get('example_translation', '')
            })
        
        # Create DataFrame and convert to CSV
        df = pd.DataFrame(rows)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')  # UTF-8 with BOM for Excel compatibility
        return csv_buffer.getvalue().encode('utf-8-sig')
    except Exception as e:
        logger.error(f"Error exporting vocabulary for user {user_id}: {e}")
        return b""

def export_vocabulary_excel(user_id: int) -> bytes:
    """
    Export user vocabulary với progress và SRS stats ra Excel file
    
    Returns:
        bytes: Excel file content
    """
    try:
        import openpyxl
    except ImportError:
        logger.warning("openpyxl not installed, falling back to CSV")
        return export_vocabulary_csv(user_id)
    
    if not supabase or not user_id:
        return b""
    
    try:
        # Get user vocabulary với join Vocabulary table
        result = supabase.table("UserVocabulary").select(
            "*, Vocabulary(word, meaning, pronunciation, type, level, topic, example, example_translation)"
        ).eq("user_id", int(user_id)).execute()
        
        if not result.data:
            return b""
        
        # Prepare data
        rows = []
        for item in result.data:
            vocab = item.get('Vocabulary', {}) or {}
            rows.append({
                'Word': vocab.get('word', ''),
                'Meaning': vocab.get('meaning', ''),
                'Pronunciation': vocab.get('pronunciation', ''),
                'Type': vocab.get('type', ''),
                'Level': vocab.get('level', ''),
                'Topic': vocab.get('topic', ''),
                'Status': item.get('status', ''),
                'Streak': item.get('streak', 0),
                'Interval (days)': item.get('interval', 0),
                'Ease Factor': item.get('ease_factor', 2.5),
                'Last Reviewed': item.get('last_reviewed_at', ''),
                'Due Date': item.get('due_date', ''),
                'Example': vocab.get('example', ''),
                'Example Translation': vocab.get('example_translation', '')
            })
        
        # Create DataFrame and convert to Excel
        df = pd.DataFrame(rows)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        return excel_buffer.getvalue()
    except Exception as e:
        logger.error(f"Error exporting vocabulary to Excel for user {user_id}: {e}")
        # Fallback to CSV
        return export_vocabulary_csv(user_id)
