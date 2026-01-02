"""Service for managing avatar frame styles and effects"""
from typing import Dict, Optional, Tuple

# Frame definitions với hiệu ứng đặc biệt
FRAME_STYLES: Dict[str, Dict[str, any]] = {
    # Basic frames (hàng thường - đơn giản)
    'gold_frame': {
        'name': 'Khung Vàng',
        'border': '3px solid #ffd700',
        'box_shadow': '0 0 15px #ffd700, 0 0 25px rgba(255, 215, 0, 0.5)',
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'tier': 'basic',
        'extra_css': '''
            .frame-gold_frame::before {
                content: '';
                position: absolute;
                inset: -6px;
                border-radius: 50%;
                padding: 3px;
                background: linear-gradient(45deg, #ffd700, #ffed4e, #ffd700);
                background-size: 200% 200%;
                -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                -webkit-mask-composite: xor;
                mask-composite: exclude;
                animation: gold-rotate 3s linear infinite;
            }
            @keyframes gold-rotate {
                0% { background-position: 0% 50%; }
                100% { background-position: 200% 50%; }
            }
        '''
    },
    'fire_frame': {
        'name': 'Khung Lửa',
        'border': '3px solid #ff4500',
        'box_shadow': '0 0 20px #ff4500, 0 0 40px rgba(255, 69, 0, 0.6)',
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'tier': 'basic',
        'extra_css': '''
            & {
                position: relative;
            }
            &::before {
                content: '';
                position: absolute;
                inset: -8px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(255,69,0,0.8) 0%, transparent 70%);
                animation: fire-flicker 0.5s ease-in-out infinite alternate;
            }
            @keyframes fire-flicker {
                0% { opacity: 0.6; transform: scale(0.95); }
                100% { opacity: 1; transform: scale(1.05); }
            }
        '''
    },
    'diamond_frame': {
        'name': 'Khung Kim Cương',
        'border': '3px solid #b9f2ff',
        'box_shadow': '0 0 20px #00c4ff, 0 0 40px rgba(0, 196, 255, 0.5), inset 0 0 20px rgba(185, 242, 255, 0.3)',
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'tier': 'basic',
        'extra_css': '''
            &::after {
                content: '';
                position: absolute;
                inset: -4px;
                border-radius: 50%;
                background: conic-gradient(from 0deg, transparent, #b9f2ff, transparent, #00c4ff, transparent);
                animation: diamond-spin 4s linear infinite;
                z-index: -1;
            }
            @keyframes diamond-spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        '''
    },
    
    # Premium frames (hàng xịn - hiệu ứng đặc biệt)
    'rainbow_frame': {
        'name': 'Khung Cầu Vồng',
        'border': '4px solid transparent',
        'box_shadow': '0 0 30px rgba(255, 0, 255, 0.6), 0 0 60px rgba(255, 215, 0, 0.4)',
        'background': 'linear-gradient(135deg, #ff0080 0%, #ff8c00 16.66%, #ffd700 33.33%, #32cd32 50%, #00bfff 66.66%, #4169e1 83.33%, #8000ff 100%)',
        'background_size': '300% 300%',
        'animation': 'rainbow-flow 4s ease infinite',
        'tier': 'premium',
        'extra_css': '''
            & {
                position: relative;
            }
            &::before {
                content: '';
                position: absolute;
                inset: -8px;
                border-radius: 50%;
                padding: 4px;
                background: linear-gradient(45deg, #ff0080, #ff8c00, #ffd700, #32cd32, #00bfff, #4169e1, #8000ff, #ff0080);
                background-size: 400% 400%;
                -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                -webkit-mask-composite: xor;
                mask-composite: exclude;
                animation: rainbow-rotate 3s linear infinite;
                filter: blur(2px);
            }
            @keyframes rainbow-flow {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            @keyframes rainbow-rotate {
                0% { background-position: 0% 50%; transform: rotate(0deg); }
                100% { background-position: 400% 50%; transform: rotate(360deg); }
            }
        '''
    },
    'galaxy_frame': {
        'name': 'Khung Thiên Hà',
        'border': '4px solid #4a148c',
        'box_shadow': '0 0 40px #9c27b0, 0 0 80px #e91e63, 0 0 120px #673ab7, 0 0 160px rgba(26, 35, 126, 0.5)',
        'background': 'radial-gradient(ellipse at 30% 30%, #e91e63 0%, #673ab7 40%, #1a237e 100%)',
        'animation': 'galaxy-pulse 5s ease-in-out infinite',
        'tier': 'premium',
        'extra_css': '''
            & {
                position: relative;
            }
            &::before,
            &::after {
                content: '';
                position: absolute;
                border-radius: 50%;
                animation: galaxy-float 6s ease-in-out infinite;
            }
            &::before {
                inset: -15px;
                background: radial-gradient(circle, rgba(233, 30, 99, 0.4) 0%, transparent 70%);
                animation-delay: 0s;
            }
            &::after {
                inset: -25px;
                background: radial-gradient(circle, rgba(103, 58, 183, 0.3) 0%, transparent 70%);
                animation-delay: 2s;
            }
            @keyframes galaxy-pulse {
                0%, 100% { 
                    box-shadow: 0 0 40px #9c27b0, 0 0 80px #e91e63, 0 0 120px #673ab7;
                }
                50% { 
                    box-shadow: 0 0 60px #9c27b0, 0 0 120px #e91e63, 0 0 180px #673ab7, 0 0 240px rgba(26, 35, 126, 0.6);
                }
            }
            @keyframes galaxy-float {
                0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.6; }
                50% { transform: scale(1.2) rotate(180deg); opacity: 1; }
            }
        '''
    },
    'lightning_frame': {
        'name': 'Khung Sét',
        'border': '4px solid #00ffff',
        'box_shadow': '0 0 30px #00ffff, 0 0 60px #00bfff, 0 0 90px rgba(255, 255, 255, 0.8)',
        'background': 'linear-gradient(135deg, #00ffff 0%, #0080ff 50%, #0000ff 100%)',
        'animation': 'lightning-flash 1.5s ease-in-out infinite',
        'tier': 'premium',
        'extra_css': '''
            & {
                position: relative;
            }
            &::before {
                content: '';
                position: absolute;
                inset: -10px;
                border-radius: 50%;
                background: conic-gradient(from 0deg, transparent, #00ffff, transparent, #00bfff, transparent, #ffffff, transparent);
                animation: lightning-spin 2s linear infinite;
                filter: blur(3px);
            }
            @keyframes lightning-flash {
                0%, 100% { 
                    box-shadow: 0 0 30px #00ffff, 0 0 60px #00bfff;
                    filter: brightness(1);
                }
                25%, 75% { 
                    box-shadow: 0 0 50px #00ffff, 0 0 100px #00bfff, 0 0 150px #ffffff;
                    filter: brightness(1.8);
                }
                50% { 
                    box-shadow: 0 0 30px #00ffff, 0 0 60px #00bfff;
                    filter: brightness(1);
                }
            }
            @keyframes lightning-spin {
                0% { transform: rotate(0deg); opacity: 0.8; }
                50% { opacity: 1; }
                100% { transform: rotate(360deg); opacity: 0.8; }
            }
        '''
    },
    'crystal_frame': {
        'name': 'Khung Pha Lê',
        'border': '4px solid rgba(255, 255, 255, 0.9)',
        'box_shadow': '0 0 40px rgba(200, 220, 255, 1), 0 0 80px rgba(255, 255, 255, 0.6), inset 0 0 40px rgba(255, 255, 255, 0.4)',
        'background': 'linear-gradient(135deg, rgba(255, 255, 255, 0.5) 0%, rgba(200, 220, 255, 0.7) 50%, rgba(255, 255, 255, 0.5) 100%)',
        'background_size': '300% 300%',
        'animation': 'crystal-shine 4s ease-in-out infinite',
        'tier': 'premium',
        'extra_css': '''
            & {
                position: relative;
            }
            &::before,
            &::after {
                content: '';
                position: absolute;
                border-radius: 50%;
            }
            &::before {
                inset: -8px;
                background: conic-gradient(from 45deg, transparent, rgba(255,255,255,0.8), transparent, rgba(200,220,255,0.8), transparent);
                animation: crystal-rotate 3s linear infinite;
                filter: blur(2px);
            }
            &::after {
                inset: -12px;
                background: radial-gradient(circle, rgba(255,255,255,0.6) 0%, transparent 70%);
                animation: crystal-pulse 2s ease-in-out infinite;
            }
            @keyframes crystal-shine {
                0% { 
                    background-position: 0% 50%;
                    filter: brightness(1);
                }
                50% { 
                    background-position: 200% 50%;
                    filter: brightness(1.3);
                }
                100% { 
                    background-position: 0% 50%;
                    filter: brightness(1);
                }
            }
            @keyframes crystal-rotate {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes crystal-pulse {
                0%, 100% { opacity: 0.4; transform: scale(0.95); }
                50% { opacity: 0.8; transform: scale(1.05); }
            }
        '''
    },
    'neon_frame': {
        'name': 'Khung Neon',
        'border': '4px solid #ff00ff',
        'box_shadow': '0 0 30px #ff00ff, 0 0 60px #ff00ff, 0 0 90px #ff00ff, 0 0 120px #00ffff',
        'background': 'linear-gradient(135deg, #ff00ff 0%, #00ffff 50%, #ff00ff 100%)',
        'background_size': '300% 300%',
        'animation': 'neon-glow 2s ease-in-out infinite',
        'tier': 'premium',
        'extra_css': '''
            & {
                position: relative;
            }
            &::before {
                content: '';
                position: absolute;
                inset: -12px;
                border-radius: 50%;
                background: linear-gradient(45deg, #ff00ff, #00ffff, #ff00ff, #00ffff);
                background-size: 400% 400%;
                -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                -webkit-mask-composite: xor;
                mask-composite: exclude;
                padding: 4px;
                animation: neon-border 2s linear infinite;
                filter: blur(4px);
            }
            @keyframes neon-glow {
                0%, 100% { 
                    box-shadow: 0 0 30px #ff00ff, 0 0 60px #ff00ff, 0 0 90px #ff00ff;
                    background-position: 0% 50%;
                }
                50% { 
                    box-shadow: 0 0 50px #ff00ff, 0 0 100px #ff00ff, 0 0 150px #ff00ff, 0 0 200px #00ffff;
                    background-position: 200% 50%;
                }
            }
            @keyframes neon-border {
                0% { background-position: 0% 50%; transform: rotate(0deg); }
                100% { background-position: 400% 50%; transform: rotate(360deg); }
            }
        '''
    },
    'cosmic_frame': {
        'name': 'Khung Vũ Trụ',
        'border': '4px solid #8b00ff',
        'box_shadow': '0 0 50px #8b00ff, 0 0 100px #4b0082, 0 0 150px #0000ff, 0 0 200px rgba(255, 20, 147, 0.6)',
        'background': 'radial-gradient(ellipse at center, #ff1493 0%, #8b00ff 50%, #0000ff 100%)',
        'background_size': '200% 200%',
        'animation': 'cosmic-swirl 6s linear infinite',
        'tier': 'premium',
        'extra_css': '''
            & {
                position: relative;
            }
            &::before,
            &::after {
                content: '';
                position: absolute;
                border-radius: 50%;
                background: conic-gradient(from 0deg, transparent, #ff1493, transparent, #8b00ff, transparent, #0000ff, transparent);
                animation: cosmic-rotate 4s linear infinite;
            }
            &::before {
                inset: -15px;
                filter: blur(5px);
                opacity: 0.8;
            }
            &::after {
                inset: -25px;
                filter: blur(8px);
                opacity: 0.5;
                animation-duration: 6s;
                animation-direction: reverse;
            }
            @keyframes cosmic-swirl {
                0% { 
                    background-position: 0% 50%;
                    transform: rotate(0deg);
                }
                100% { 
                    background-position: 200% 50%;
                    transform: rotate(360deg);
                }
            }
            @keyframes cosmic-rotate {
                0% { transform: rotate(0deg) scale(1); }
                50% { transform: rotate(180deg) scale(1.1); }
                100% { transform: rotate(360deg) scale(1); }
            }
        '''
    }
}

def get_frame_style(frame_value: Optional[str]) -> Tuple[str, Optional[str], str]:
    """Get CSS style for avatar frame.
    
    Args:
        frame_value: Frame value from database (e.g., 'fire_frame', 'rainbow_frame')
        
    Returns:
        Tuple of (container_style, extra_css, frame_class)
    """
    if not frame_value:
        # Default style
        return "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);", None, ""
    
    frame_config = FRAME_STYLES.get(frame_value)
    if not frame_config:
        # Unknown frame, use default
        return "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);", None, ""
    
    # Build style string
    style_parts = []
    
    # Background
    bg = frame_config.get('background', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
    style_parts.append(f"background: {bg}")
    
    # Background size if specified
    if 'background_size' in frame_config:
        style_parts.append(f"background-size: {frame_config['background_size']}")
    
    # Box shadow
    box_shadow = frame_config.get('box_shadow', '0 8px 16px rgba(102, 126, 234, 0.3)')
    style_parts.append(f"box-shadow: {box_shadow}")
    
    # Animation if specified
    if 'animation' in frame_config:
        style_parts.append(f"animation: {frame_config['animation']}")
    
    # Position relative for pseudo-elements
    if frame_config.get('tier') == 'premium' or frame_config.get('extra_css'):
        style_parts.append("position: relative")
    
    container_style = "; ".join(style_parts)
    
    # Get extra CSS if any
    extra_css = frame_config.get('extra_css', '')
    
    # Frame class for targeting
    frame_class = f"frame-{frame_value}" if frame_value else ""
    
    return container_style, extra_css, frame_class

def get_frame_border_style(frame_value: Optional[str]) -> str:
    """Get border style for avatar image inside frame container.
    
    Args:
        frame_value: Frame value from database
        
    Returns:
        CSS border style string
    """
    if not frame_value:
        return "border: 3px solid white;"
    
    frame_config = FRAME_STYLES.get(frame_value)
    if not frame_config:
        return "border: 3px solid white;"
    
    border = frame_config.get('border', '3px solid white')
    return border
