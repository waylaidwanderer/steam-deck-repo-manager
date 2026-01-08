class Theme:
    # Tailwind Slate Palette
    SLATE_950 = "#020617"
    SLATE_900 = "#0f172a"
    SLATE_800 = "#1e293b"
    SLATE_700 = "#334155"
    SLATE_600 = "#475569"
    SLATE_100 = "#f1f5f9"

    # Accent
    BLUE_500 = "#3b82f6"
    BLUE_600 = "#2563eb"
    BLUE_700 = "#1d4ed8"

    # Status
    RED_500 = "#ef4444"
    GREEN_500 = "#22c55e"

    @staticmethod
    def get_stylesheet():
        return f"""
        QMainWindow {{
            background-color: {Theme.SLATE_950};
            color: {Theme.SLATE_100};
        }}
        QWidget {{
            background-color: {Theme.SLATE_950};
            color: {Theme.SLATE_100};
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px; /* Larger font for Steam Deck */
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {Theme.SLATE_800};
            color: {Theme.SLATE_100};
            border: 1px solid {Theme.SLATE_700};
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 16px;
        }}
        QPushButton:hover {{
            background-color: {Theme.SLATE_700};
            border-color: {Theme.BLUE_500};
        }}
        QPushButton:pressed {{
            background-color: {Theme.BLUE_600};
            border-color: {Theme.BLUE_600};
        }}
        QPushButton:disabled {{
            background-color: {Theme.SLATE_900};
            color: {Theme.SLATE_600};
            border-color: {Theme.SLATE_800};
        }}
        
        /* Primary Action Buttons (if we define a class for them) */
        QPushButton[class="primary"] {{
            background-color: {Theme.BLUE_500};
            border: none;
        }}
        QPushButton[class="primary"]:hover {{
            background-color: {Theme.BLUE_600};
        }}
        
        /* Input Fields */
        QLineEdit {{
            background-color: {Theme.SLATE_900};
            border: 2px solid {Theme.SLATE_800};
            border-radius: 8px;
            padding: 12px;
            color: {Theme.SLATE_100};
            font-size: 16px;
            selection-background-color: {Theme.BLUE_500};
        }}
        QLineEdit:focus {{
            border: 2px solid {Theme.BLUE_500};
            background-color: {Theme.SLATE_800};
        }}
        
        /* Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: {Theme.SLATE_950};
            width: 12px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {Theme.SLATE_700};
            min-height: 40px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {Theme.BLUE_500};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* Tabs */
        QTabWidget::pane {{
            border: none; /* Removed border to prevent clash with pagination bar */
            top: -1px;
            background-color: {Theme.SLATE_950};
        }}
        QTabBar::tab {{
            background: {Theme.SLATE_900};
            color: {Theme.SLATE_100};
            padding: 12px 24px; /* More compact padding */
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 4px;
            font-size: 16px; /* Slightly smaller font */
            border-bottom: 3px solid transparent;
        }}
        QTabBar::tab:selected {{
            background: {Theme.SLATE_800};
            font-weight: bold;
            border-bottom: 3px solid {Theme.BLUE_500};
        }}
        
        /* Cards - Targeting by ObjectName for reliability */
        QFrame#VideoCard {{
            background-color: {Theme.SLATE_800};
            border-radius: 12px;
            border: 2px solid {Theme.SLATE_600};
        }}
        QFrame#VideoCard:hover {{
            border: 2px solid {Theme.BLUE_500};
            background-color: {Theme.SLATE_700};
        }}
        
        /* Labels */
        QLabel {{
            background: transparent;
        }}
        """
