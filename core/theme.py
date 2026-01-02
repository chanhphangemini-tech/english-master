import streamlit as st

def apply_custom_theme():
    """Áp dụng CSS tùy chỉnh cho toàn bộ ứng dụng."""
    
    # Default Colors
    primary_color = "#003366"
    secondary_color = "#007BFF"
    bg_color = "#f8f9fa"
    
    # Check session state for active theme
    theme = st.session_state.get('active_theme_value')
    
    if theme == 'ocean_blue':
        primary_color = "#006064" # Cyan dark
        secondary_color = "#00BCD4" # Cyan
        bg_color = "#E0F7FA"
    elif theme == 'sunset':
        primary_color = "#BF360C" # Deep Orange
        secondary_color = "#FF5722" # Orange
        bg_color = "#FBE9E7"
    elif theme == 'forest':
        primary_color = "#1B5E20" # Green
        secondary_color = "#4CAF50" # Light Green
        bg_color = "#E8F5E9"
    elif theme == 'gold' or theme == 'yellow' or theme == 'vang' or theme == 'gold_theme' or theme == 'yellow_theme':
        # Theme Vàng (Gold/Yellow)
        primary_color = "#D97706" # Amber dark
        secondary_color = "#FBBF24" # Amber/Gold
        bg_color = "#FEF3C7" # Light yellow/amber
    elif theme == 'pink' or theme == 'rose' or theme == 'hong' or theme == 'pink_theme' or theme == 'rose_theme':
        # Theme Hồng (Pink/Rose)
        primary_color = "#BE185D" # Pink dark
        secondary_color = "#EC4899" # Pink
        bg_color = "#FCE7F3" # Light pink

    st.markdown(f"""
        <style>
        /* Import fonts FIRST */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        :root {{
            --primary-color: {primary_color};
            --secondary-color: {secondary_color};
            --bg-color: {bg_color};
        }}
        
        /* --- 1. Sidebar Fix (FOUC) --- */
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}
        
        /* --- 4. Typography & Colors --- */
        
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}
        
        /* Main Container */
        .stApp {{
            background-color: {bg_color};
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: #ffffff;
            border-right: 1px solid #e9ecef;
        }}
        
        /* Headings */
        h1, h2, h3 {{
            color: {primary_color};
            font-weight: 700;
        }}
        
        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: {secondary_color};
            font-weight: bold;
        }}
        
        /* Buttons */
        .stButton button {{
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s;
            background-color: {secondary_color};
            color: white;
        }}
        .stButton button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            background-color: {primary_color};
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 20px;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px;
            color: #495057;
            font-size: 16px;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: #e7f1ff;
            color: {secondary_color};
            font-weight: bold;
        }}
        
        /* Cards/Containers */
        div[data-testid="stVerticalBlock"] > div[style*="border"] {{
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            border: 1px solid #eee;
        }}

        /* --- 3. Empty States --- */
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }}
        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 10px;
            opacity: 0.5;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .stTabs [data-baseweb="tab"] {{
                font-size: 14px;
                padding: 8px 12px;
            }}
            h1 {{ font-size: 1.5em !important; }}
            h2 {{ font-size: 1.3em !important; }}
            h3 {{ font-size: 1.1em !important; }}
        }}
        </style>
    """, unsafe_allow_html=True)

def render_empty_state(message="Chưa có dữ liệu", icon="📭"):
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div>{message}</div>
    </div>
    """, unsafe_allow_html=True)

def show_skeleton_loading():
    """Hiển thị skeleton loading animation"""
    st.markdown("""
    <div style="background: #f0f2f6; border-radius: 8px; padding: 20px; margin: 10px 0;">
        <div style="height: 20px; background: #e0e0e0; margin: 10px 0; border-radius: 4px;"></div>
        <div style="height: 20px; background: #e0e0e0; width: 80%; margin: 10px 0; border-radius: 4px;"></div>
        <div style="height: 20px; background: #e0e0e0; width: 60%; margin: 10px 0; border-radius: 4px;"></div>
    </div>
    """, unsafe_allow_html=True)

def animated_progress(value, max_value, label="", height=20):
    """Progress bar với animation"""
    percent = min(100, int((value / max_value) * 100)) if max_value > 0 else 0
    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="background: #e0e0e0; border-radius: 10px; height: {height}px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #4CAF50, #45a049); 
                        width: {percent}%; height: 100%; 
                        transition: width 1s ease-in-out;
                        display: flex; align-items: center; justify-content: center;
                        color: white; font-size: 12px; font-weight: bold;">
                {percent}%
            </div>
        </div>
        {f'<div style="text-align: center; margin-top: 5px;">{label}</div>' if label else ''}
    </div>
    """, unsafe_allow_html=True)
