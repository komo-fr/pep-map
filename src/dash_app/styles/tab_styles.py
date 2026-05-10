"""Tab button and content styles for Groups tab."""

import json

TAB_ACCENT_COLOR = "#DDAD3E"

TAB_BUTTON_BASE_STYLE = {
    "padding": "6px 12px",
    "border": "1px solid #ddd",
    "borderBottom": "none",
    "backgroundColor": "#f5f5f5",
    "cursor": "pointer",
    "marginRight": "4px",
    "borderRadius": "4px 4px 0 0",
    "fontSize": "13px",
}

TAB_BUTTON_SELECTED_STYLE = {
    **TAB_BUTTON_BASE_STYLE,
    "backgroundColor": "#fff",
    "fontWeight": "bold",
    "borderTop": f"3px solid {TAB_ACCENT_COLOR}",
    "borderBottom": "1px solid #fff",
    "marginBottom": "-1px",
}

TAB_BUTTON_UNSELECTED_STYLE = TAB_BUTTON_BASE_STYLE

TAB_CONTENT_VISIBLE_STYLE = {
    "visibility": "visible",
    "position": "relative",
    "zIndex": "1",
}

TAB_CONTENT_HIDDEN_STYLE = {
    "visibility": "hidden",
    "position": "absolute",
    "top": "0",
    "left": "0",
    "right": "0",
    "zIndex": "0",
}


def get_tab_styles_js() -> str:
    """Generate JavaScript object literals for tab styles."""
    return f"""
            const visibleContentStyle = {json.dumps(TAB_CONTENT_VISIBLE_STYLE)};
            const hiddenContentStyle = {json.dumps(TAB_CONTENT_HIDDEN_STYLE)};
            const selectedButtonStyle = {json.dumps(TAB_BUTTON_SELECTED_STYLE)};
            const unselectedButtonStyle = {json.dumps(TAB_BUTTON_UNSELECTED_STYLE)};
"""
