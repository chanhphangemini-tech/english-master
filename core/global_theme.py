"""
Global theme CSS for all pages
"""
import streamlit as st

def apply_global_theme():
    """Apply professional theme to all pages with theme support"""
    
    # Get active theme from session state
    theme = st.session_state.get('active_theme_value')
    
    # Default colors
    primary_color = "#2563eb"
    secondary_color = "#3b82f6"
    bg_color = "#f8fafc"
    container_bg = "#ffffff"
    
    # Apply theme colors if theme is active
    # Normalize theme value (lowercase, strip whitespace, remove underscores/dashes)
    theme_normalized = None
    if theme:
        theme_normalized = str(theme).lower().strip().replace('_', '').replace('-', '').replace(' ', '')
    
    # Use normalized theme for matching (more flexible)
    theme_check = theme_normalized if theme_normalized else (str(theme).lower().strip() if theme else None)
    
    if theme and theme_check and ('ocean' in theme_check and 'blue' in theme_check):
        primary_color = "#006064"  # Cyan dark
        secondary_color = "#00BCD4"  # Cyan
        bg_color = "#E0F7FA"
        container_bg = "#ffffff"
    elif theme and theme_check and 'sunset' in theme_check:
        primary_color = "#BF360C"  # Deep Orange
        secondary_color = "#FF5722"  # Orange
        bg_color = "#FBE9E7"
        container_bg = "#ffffff"
    elif theme and theme_check and 'forest' in theme_check:
        primary_color = "#1B5E20"  # Green
        secondary_color = "#4CAF50"  # Light Green
        bg_color = "#E8F5E9"
        container_bg = "#ffffff"
    elif theme and theme_check and any(keyword in theme_check for keyword in ['gold', 'yellow', 'vang', 'vàng']):
        # Theme Vàng (Gold/Yellow)
        primary_color = "#D97706"  # Amber dark
        secondary_color = "#FBBF24"  # Amber/Gold
        bg_color = "#FEF3C7"  # Light yellow/amber
        container_bg = "#FFFFFF"
    elif theme and theme_check and any(keyword in theme_check for keyword in ['pink', 'rose', 'hong', 'hồng']):
        # Theme Hồng (Pink/Rose)
        primary_color = "#BE185D"  # Pink dark
        secondary_color = "#EC4899"  # Pink
        bg_color = "#FCE7F3"  # Light pink
        container_bg = "#FFFFFF"
    
    st.markdown(f"""
    <style>
        /* Hide the default Streamlit navigation */
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}
        
        /* Professional background colors */
        .stApp {{
            background-color: {bg_color} !important;
        }}
        
        .main .block-container {{
            background-color: {container_bg} !important;
            padding: 2rem 3rem !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        }}
        
        /* Professional Primary buttons - theme-aware */
        button[kind="primary"],
        .stButton > button[kind="primary"] {{
            background-color: {primary_color} !important;
            background: linear-gradient(135deg, {secondary_color} 0%, {primary_color} 100%) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
        }}
        
        button[kind="primary"]:hover,
        .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, {primary_color} 0%, {primary_color}dd 100%) !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px {primary_color}4d !important;
        }}
        
        button[kind="primary"]:active,
        .stButton > button[kind="primary"]:active {{
            transform: translateY(0) !important;
            box-shadow: 0 2px 4px {primary_color}33 !important;
        }}
        
        /* Professional Secondary buttons - elegant gray-blue */
        button[kind="secondary"],
        .stButton > button[kind="secondary"] {{
            background-color: #64748b !important;
            background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(100, 116, 139, 0.2) !important;
        }}
        
        button[kind="secondary"]:hover,
        .stButton > button[kind="secondary"]:hover {{
            background: linear-gradient(135deg, #475569 0%, #334155 100%) !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(100, 116, 139, 0.3) !important;
        }}
        
        /* Professional Tertiary buttons - subtle outline */
        button[kind="tertiary"],
        .stButton > button[kind="tertiary"] {{
            background-color: #ffffff !important;
            color: #475569 !important;
            border: 2px solid #cbd5e1 !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}
        
        button[kind="tertiary"]:hover,
        .stButton > button[kind="tertiary"]:hover {{
            background-color: #f1f5f9 !important;
            color: #334155 !important;
            border-color: #94a3b8 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }}
        
        /* Default buttons - clean and modern */
        .stButton > button:not([kind]):not([kind="primary"]):not([kind="secondary"]):not([kind="tertiary"]) {{
            background-color: #ffffff !important;
            color: #475569 !important;
            border: 1px solid #e2e8f0 !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }}
        
        .stButton > button:not([kind]):not([kind="primary"]):not([kind="secondary"]):not([kind="tertiary"]):hover {{
            background-color: #f8fafc !important;
            color: #334155 !important;
            border-color: #cbd5e1 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }}
        
        /* Hover effect for cards and containers */
        [data-testid="stVerticalBlock"] > div,
        .element-container {{
            transition: transform 0.2s ease !important;
        }}
        
        [data-testid="stVerticalBlock"] > div:hover,
        .element-container:hover {{
            transform: translateY(-2px) !important;
        }}
        
        /* Cards with borders */
        [data-testid="stVerticalBlock"] > [data-testid="stContainer"] {{
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }}
        
        [data-testid="stVerticalBlock"] > [data-testid="stContainer"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        }}
    </style>
    """, unsafe_allow_html=True)
