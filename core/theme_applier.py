"""
Quick theme applier for all pages
"""
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def apply_page_theme():
    """Apply beautiful theme to any page - ONE LINE IMPORT + FIX keyboard_double_arrow_right"""
    
    # === NUCLEAR OPTION: Apply to ALL pages ===
    st.markdown("""
    <script>
    (function() {
        'use strict';
        const BLOCKED = ['keyboard', 'arrow', 'double_arrow', 'keyboard_double_arrow_right', 'keyboard_arrow', 'keyboard_arrow_right', 'key_', 'arrow_right', 'arrow_forward', 'arrow_down', 'arrow_up'];
        
        function nuke() {
            let removed = 0;
            
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
            let node;
            const nodesToRemove = [];
            
            while (node = walker.nextNode()) {
                const text = node.nodeValue?.trim() || '';
                if (BLOCKED.some(p => text.toLowerCase().includes(p)) && text.length > 3) {
                    const parent = node.parentElement;
                    if (parent && parent.tagName !== 'SCRIPT' && parent.tagName !== 'STYLE') {
                        nodesToRemove.push(parent);
                    }
                }
            }
            
            nodesToRemove.forEach(el => { el.remove(); removed++; });
            
            document.querySelectorAll('[data-testid="stText"]').forEach(el => {
                const text = el.textContent?.trim() || '';
                if (BLOCKED.some(p => text.toLowerCase().includes(p))) {
                    el.remove();
                    removed++;
                }
            });
            
            document.querySelectorAll('div, span, p').forEach(el => {
                const text = el.textContent?.trim() || '';
                if (BLOCKED.some(p => text.toLowerCase() === p.toLowerCase())) {
                    el.remove();
                    removed++;
                }
            });
            
            document.querySelectorAll('[data-testid="stExpander"], [role="group"]').forEach(container => {
                container.querySelectorAll('div, span').forEach(el => {
                    const text = el.textContent?.trim() || '';
                    if (BLOCKED.some(p => text.toLowerCase().includes(p)) && text.length < 50) {
                        el.remove();
                        removed++;
                    }
                });
            });
            
            document.querySelectorAll('*').forEach(el => {
                if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return;
                if (el.children.length === 0) {
                    const text = el.textContent?.trim() || '';
                    if (text.length > 0 && text.length < 50 && BLOCKED.some(p => text.toLowerCase().includes(p))) {
                        el.style.cssText = 'display:none!important;position:absolute!important;left:-99999px!important;';
                        removed++;
                    }
                }
            });
            
            if (removed > 0) console.log('🔥 Nuked', removed, 'keyboard elements');
        }
        
        nuke();
        setTimeout(nuke, 100);
        setTimeout(nuke, 300);
        setTimeout(nuke, 500);
        setTimeout(nuke, 1000);
        if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', nuke);
        setInterval(nuke, 200);
        
        let timeout;
        new MutationObserver(() => {
            clearTimeout(timeout);
            timeout = setTimeout(nuke, 50);
        }).observe(document.body, {childList:true, subtree:true, characterData:true, attributes:true});
        
        console.log('✅ NUCLEAR keyboard remover initialized');
    })();
    </script>
    """, unsafe_allow_html=True)
    
    from core.ui_styles import apply_beautiful_theme
    from core.sidebar import render_sidebar
    from core.global_theme import apply_global_theme
    
    # Check auth first
    if not st.session_state.get('logged_in'):
        st.switch_page("home.py")
    
    # Security Monitor: Check user status
    try:
        from core.security_monitor import SecurityMonitor
        user_id = st.session_state.user_info.get('id')
        if user_id:
            is_allowed, message = SecurityMonitor.check_user_status(user_id)
            if not is_allowed:
                st.error(f"🔒 {message}")
                st.stop()
    except Exception as e:
        # Fail open - allow user if security check fails
        logger.debug(f"Security check error (non-critical): {e}")
    
    # Load active theme from inventory if not already in session
    # Always reload to ensure theme is up-to-date
    try:
        from core.data import get_user_inventory
        user_id = st.session_state.user_info.get('id')
        if user_id:
            inventory = get_user_inventory(user_id)
            active_theme = next((item['ShopItems']['value'] for item in inventory if item.get('is_active') and item.get('ShopItems', {}).get('type') == 'theme'), None)
            if active_theme:
                st.session_state.active_theme_value = active_theme
    except:
        pass
    
    # Apply professional theme and sidebar
    apply_global_theme()  # Apply new professional theme (now theme-aware)
    render_sidebar()

