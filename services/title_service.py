"""Service for handling title translations and formatting"""
from typing import Optional

# Mapping từ title value sang tên tiếng Việt
TITLE_TRANSLATIONS = {
    'dai_gia': 'Đại Gia',
    'tri_tue': 'Trí Tuệ',
    'chieu_tu': 'Chiếu Tử',
    'huynh_dao': 'Huynh Đạo',
    'vo_dich': 'Vô Địch',
    'than_thoai': 'Thần Thoại',
    'huyen_thoai': 'Huyền Thoại',
    'bach_vuong': 'Bạch Vương',
    'kim_cuong': 'Kim Cương',
    'bach_kim': 'Bạch Kim',
    'vang': 'Vàng',
    'bac': 'Bạc',
    'dong': 'Đồng',
    'thuong': 'Thường',
}

def get_title_display_name(title_value: Optional[str]) -> Optional[str]:
    """Convert title value to Vietnamese display name with emoji.
    
    Args:
        title_value: Title value from database (e.g., 'dai_gia')
        
    Returns:
        Formatted title name with emoji (e.g., '✨ Đại Gia') or None
    """
    if not title_value:
        return None
    
    # Try to get from translations
    display_name = TITLE_TRANSLATIONS.get(title_value.lower())
    
    # If not found, try to format the value (replace _ with space and title case)
    if not display_name:
        display_name = title_value.replace('_', ' ').title()
    
    return f'✨ {display_name}'

