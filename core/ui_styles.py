"""
Centralized UI styles for beautiful, eye-friendly learning interface
"""

# Modern color palette - Eye-friendly
COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    'background': '#f8fafc',
    'card': '#ffffff',
    'text': '#1e293b',
    'text_secondary': '#64748b',
    'border': '#e2e8f0',
}

# Global styles for eye-friendly reading
GLOBAL_STYLES = """
<style>
    /* Import Google Fonts - MUST BE AT TOP */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global settings */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Streamlit containers */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Main content area */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
    }
    
    /* Headers - DARK, READABLE */
    h1 {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    h2 {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 1.75rem !important;
        margin-top: 1rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    h3 {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
    }
    
    /* Vocabulary cards - Consistent height */
    [data-testid="stVerticalBlock"] > div {
        border-radius: 16px;
        transition: all 0.3s ease;
    }
    
    [data-testid="stVerticalBlock"] > div:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.15);
    }
    
    /* Ensure columns have equal height for vocabulary cards */
    [data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
    }
    
    [data-testid="column"] > [data-testid="stVerticalBlock"] {
        flex: 1 !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    [data-testid="column"] > [data-testid="stVerticalBlock"] > [data-testid="stContainer"] {
        flex: 1 !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        font-weight: 500;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Input fields - Hide widget keys */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    /* === FIX "keyboard_double_arrow_right" TRIỆT ĐỂ - ULTRA AGGRESSIVE === */
    
    /* 1. NUCLEAR: Hide ANY element containing keyboard text */
    body *:not(script):not(style) {
        /* Scan all text content */
    }
    
    /* 2. Hide specific patterns in text nodes */
    [data-testid="stText"],
    [data-testid="stMarkdown"] span,
    div span,
    p span {
        /* Will be handled by JS */
    }
    
    /* 3. Hide Material Icon text fallbacks EVERYWHERE */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* 4. Force hide specific text patterns */
    [data-testid="stText"]:not(h1 *):not(h2 *):not(h3 *):not(p *):not(li *):not([data-testid="stMarkdown"] p *) {
        display: none !important;
        visibility: hidden !important;
        position: absolute !important;
        left: -99999px !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
    }
    
    /* 5. Hide sidebar navigation icons */
    [data-testid="stSidebar"] [data-testid="stText"],
    [data-testid="stSidebarNav"] [data-testid="stText"],
    [data-testid="stPageLink-NavLink"] span:not(:first-child),
    a[href*="pages/"] span:not(:first-child) {
        display: none !important;
        visibility: hidden !important;
        position: absolute !important;
        left: -99999px !important;
    }
    
    /* 6. Re-enable legitimate markdown text */
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] strong,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] em {
        display: block !important;
        visibility: visible !important;
        position: static !important;
        font-size: inherit !important;
        opacity: 1 !important;
    }
    
    /* Responsive audio player */
    audio {
        max-width: 100%;
        height: 40px;
    }
    
    /* Mobile responsive fixes */
    @media (max-width: 768px) {
        audio {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .stButton > button {
            font-size: 0.9rem !important;
            padding: 8px 16px !important;
        }
        
        /* Sidebar responsive */
        [data-testid="stSidebar"] {
            min-width: 250px !important;
        }
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #667eea;
        background-color: #f8fafc;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    [data-testid="stMetricDelta"] {
        font-weight: 500;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: white;
        border-radius: 12px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* Containers with borders - Consistent card styling */
    [data-testid="stVerticalBlock"] > [data-testid="stContainer"] {
        background-color: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
        min-height: 350px; /* Consistent minimum height for vocabulary cards */
        display: flex;
        flex-direction: column;
    }
    
    /* Success/Warning/Error messages */
    .stSuccess {
        background-color: #f0fdf4;
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stWarning {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stError {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stInfo {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Sidebar text color */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    /* Readable text - DARK, LARGE */
    body {
        line-height: 1.7;
        letter-spacing: 0.01em;
    }
    
    p {
        color: #1e293b !important;
        line-height: 1.8 !important;
        font-size: 1.1rem !important;
    }
    
    li, span {
        color: #334155 !important;
        line-height: 1.7 !important;
        font-size: 1.05rem !important;
    }
    
    /* Bold text - VERY DARK */
    strong, b {
        color: #0f172a !important;
        font-weight: 600 !important;
    }
    
    /* Italic text */
    em, i {
        color: #475569 !important;
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Loading spinners */
    .stSpinner > div {
        border-color: #667eea !important;
    }
    
    /* Radio buttons & checkboxes */
    .stRadio > label, .stCheckbox > label {
        font-weight: 500;
        color: #334155;
    }
    
    /* Code blocks */
    code {
        background-color: #f1f5f9;
        padding: 0.2em 0.4em;
        border-radius: 6px;
        font-size: 0.9em;
        color: #e11d48;
    }
    
    /* Tables */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* Remove default padding on mobile */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
    }
    
    /* === OPTION A: ULTRA AGGRESSIVE CSS - KILL ALL ICON TEXT === */
    
    /* Layer 1: Hide ALL spans in sidebar */
    [data-testid="stSidebarNav"] span,
    [data-testid="stSidebar"] nav span,
    [data-testid="stSidebar"] a span,
    nav[aria-label] span {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        position: absolute !important;
        left: -999999px !important;
        width: 0 !important;
        height: 0 !important;
        font-size: 0 !important;
        line-height: 0 !important;
        overflow: hidden !important;
        clip: rect(0,0,0,0) !important;
        clip-path: inset(100%) !important;
    }
    
    /* Layer 2: Show ONLY paragraph (labels) */
    [data-testid="stSidebarNav"] p,
    [data-testid="stSidebar"] a p {
        display: inline !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: static !important;
        font-size: 1rem !important;
        clip: auto !important;
        clip-path: none !important;
    }
    
    /* Layer 3: Hide Material Icons */
    .material-icons, .material-symbols-outlined {
        display: none !important;
    }
    
    /* Layer 4: Nuclear - ALL non-p in nav */
    [data-testid="stSidebar"] a *:not(p) {
        font-size: 0 !important;
        color: transparent !important;
    }
    
    /* === OPTION A: HIDE ALL HEADER BUTTONS (RECOMMENDED) === */
    
    /* Hide deploy button and app menu completely */
    [data-testid="stAppDeployButton"],
    button[aria-label*="Deploy"],
    button[aria-label*="App menu"],
    header button:not([kind="header"]):not([kind="headerNoPadding"]),
    [data-testid="stHeader"] button:not([kind="header"]):not([kind="headerNoPadding"]),
    header [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
        position: absolute !important;
        left: -99999px !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
    }
    
    /* Keep sidebar toggle button visible and styled */
    button[kind="header"],
    button[kind="headerNoPadding"],
    [data-testid="collapsedControl"],
    button[aria-label*="sidebar"] {
        background: transparent !important;
        border: none !important;
        padding: 0.5rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        border-radius: 8px !important;
        color: #667eea !important;
    }
    
    button[kind="header"]:hover,
    button[kind="headerNoPadding"]:hover,
    [data-testid="collapsedControl"]:hover,
    button[aria-label*="sidebar"]:hover {
        background: rgba(102, 126, 234, 0.1) !important;
        transform: scale(1.05) !important;
    }
    
    /* === HIDE keyboard TEXT IN TABS === */
    [data-baseweb="tab-list"] span,
    [data-baseweb="tab"] span,
    [role="tab"] span,
    button[role="tab"] span {
        font-size: 0 !important;
        color: transparent !important;
    }
    
    /* Show tab label text (p tags) */
    [data-baseweb="tab"] p,
    [role="tab"] p,
    button[role="tab"] p {
        font-size: 1rem !important;
        color: inherit !important;
    }
    
    /* === HIDE keyboard TEXT IN SELECTBOX/DROPDOWN === */
    [data-baseweb="select"] span,
    [data-baseweb="select"] *,
    .stSelectbox span,
    .stSelectbox *,
    select option,
    [data-baseweb="popover"] span {
        font-size: 0 !important;
        color: transparent !important;
    }
    
    /* Show actual selectbox text */
    [data-baseweb="select"] p,
    .stSelectbox p {
        font-size: 1rem !important;
        color: inherit !important;
    }
    
    /* Hide keyboard_arrow_down in selectbox */
    [data-baseweb="select"] span:contains("keyboard"),
    [data-baseweb="select"] span:contains("arrow"),
    .stSelectbox span:contains("keyboard"),
    .stSelectbox span:contains("arrow") {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* === HIDE keyboard TEXT IN HEADERS/TITLES === */
    [data-testid="stHeader"] span,
    h1 span:not([data-testid="stMarkdown"] span),
    h2 span:not([data-testid="stMarkdown"] span),
    h3 span:not([data-testid="stMarkdown"] span) {
        display: inline !important;
    }
    
    /* === BEAUTIFUL SIDEBAR - BALANCED DESIGN === */
    
    /* Sidebar Background - Gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Section Headers (Tiêu đề) - HIGHLY VISIBLE */
    [data-testid="stSidebar"] .stMarkdown strong {
        color: #fbbf24 !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        margin-top: 8px !important;
        margin-bottom: 14px !important;
        display: block !important;
        padding: 9px 12px 9px 14px !important;
        background: rgba(251, 191, 36, 0.15) !important;
        border-radius: 6px !important;
        border-left: 4px solid #fbbf24 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Navigation Buttons (Menu con) - BALANCED */
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([key*="logout"]) {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-left: 3px solid transparent !important;
        border-radius: 6px !important;
        padding: 0.45rem 0.9rem !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        text-align: left !important;
        transition: all 0.25s ease !important;
        margin-bottom: 4px !important;
        margin-top: 0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        color: rgba(255, 255, 255, 0.9) !important;
        width: 100% !important;
        min-height: 36px !important;
        line-height: 1.4 !important;
    }
    
    /* Prevent overlapping - add spacing to button containers */
    [data-testid="stSidebar"] .stButton {
        margin-top: 2px !important;
    }
    
    /* Button containers spacing */
    [data-testid="stSidebar"] .stButton {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        padding: 0 !important;
    }
    
    /* Hover effect for menu items - SMOOTH */
    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([key*="logout"]):hover {
        background: rgba(255, 255, 255, 0.15) !important;
        border-left-color: #fbbf24 !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        transform: translateX(5px) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Primary button (Trang Chủ) - HIGHLIGHTED & PROMINENT */
    [data-testid="stSidebar"] button[kind="primary"]:not([key*="logout"]) {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4), 0 2px 4px rgba(251, 191, 36, 0.3) !important;
        margin-bottom: 6px !important;
        margin-top: 0 !important;
        min-height: 40px !important;
        line-height: 1.4 !important;
        font-size: 0.92rem !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    /* Add shine effect to Trang Chủ button */
    [data-testid="stSidebar"] button[kind="primary"]:not([key*="logout"])::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent) !important;
        transition: left 0.5s ease !important;
    }
    
    [data-testid="stSidebar"] button[kind="primary"]:not([key*="logout"]):hover::before {
        left: 100% !important;
    }
    
    [data-testid="stSidebar"] button[kind="primary"]:not([key*="logout"]):hover {
        background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%) !important;
        transform: translateX(5px) translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(251, 191, 36, 0.5), 0 4px 8px rgba(251, 191, 36, 0.4) !important;
    }
    
    /* Logout button - DISTINCTIVE */
    [data-testid="stSidebar"] button[key*="logout"] {
        background: rgba(248, 113, 113, 0.15) !important;
        border: 1px solid rgba(248, 113, 113, 0.4) !important;
        color: #fca5a5 !important;
        margin-top: 6px !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        min-height: 38px !important;
        line-height: 1.4 !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }
    
    [data-testid="stSidebar"] button[key*="logout"]:hover {
        background: rgba(248, 113, 113, 0.25) !important;
        border-color: #f87171 !important;
        color: #fecaca !important;
        transform: scale(1.02) !important;
    }
    
    /* Divider styling - SUBTLE */
    [data-testid="stSidebar"] hr {
        border: none !important;
        border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
        margin: 10px 0 !important;
    }
    
    /* Balanced spacing in sidebar vertical blocks */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 2px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Profile section - IMPROVED */
    [data-testid="stSidebar"] .stImage {
        margin-bottom: 8px !important;
        margin-top: 8px !important;
        border-radius: 50% !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    
    [data-testid="stSidebar"] h3 {
        margin-top: 8px !important;
        margin-bottom: 2px !important;
        color: white !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    }
    
    [data-testid="stSidebar"] p {
        margin-top: 2px !important;
        margin-bottom: 4px !important;
    }
    
    /* Stats columns - IMPROVED */
    [data-testid="stSidebar"] [data-testid="column"] {
        padding: 4px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        margin: 0 2px !important;
        transition: all 0.25s ease !important;
    }
    
    [data-testid="stSidebar"] [data-testid="column"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateY(-2px) !important;
    }
</style>
"""

# Vocabulary card styles
VOCAB_CARD_STYLES = """
<style>
    .vocab-card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 2px solid #e2e8f0;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
        min-height: 300px; /* Ensure consistent minimum height */
        display: flex;
        flex-direction: column;
    }
    
    /* Consistent card container styling */
    [data-testid="stVerticalBlock"] > [data-testid="stContainer"] {
        min-height: 300px;
    }
    
    .vocab-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .vocab-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 32px rgba(102, 126, 234, 0.2);
        border-color: #667eea;
    }
    
    .vocab-word {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .vocab-pronunciation {
        font-size: 1.25rem;
        color: #667eea;
        font-weight: 500;
        font-family: 'Courier New', monospace;
    }
    
    .vocab-meaning {
        font-size: 1.5rem;
        color: #475569;
        margin: 1rem 0;
        font-style: italic;
    }
    
    .vocab-type {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .vocab-example {
        background: #f8fafc;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    
    .vocab-example-en {
        color: #1e293b;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    
    .vocab-example-vi {
        color: #64748b;
        font-size: 1rem;
    }
    
    .tts-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        padding: 12px 24px;
        border-radius: 25px;
        cursor: pointer;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .tts-button:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.5);
    }
    
    .tts-button:active {
        transform: translateY(-1px) scale(1);
    }
    
    .new-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .review-badge {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
</style>
"""

def apply_beautiful_theme():
    """Apply beautiful, eye-friendly theme to Streamlit app"""
    import streamlit as st
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)

def apply_vocab_card_styles():
    """Apply vocabulary card styles"""
    import streamlit as st
    st.markdown(VOCAB_CARD_STYLES, unsafe_allow_html=True)

