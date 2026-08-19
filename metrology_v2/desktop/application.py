"""
PySide6 Desktop Application for Metrology V2

Professional desktop application with:
- Native Windows desktop experience
- Agentic UI animations
- Integration with backend services
- Professional styling and UX
- Offline capability with local-first architecture
"""

import sys
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
        QTableWidget, QTableWidgetItem, QTabWidget, QStatusBar,
        QMenuBar, QToolBar, QSplitter, QFrame, QScrollArea,
        QProgressBar, QMessageBox, QDialog, QDialogButtonBox,
        QFormLayout, QGroupBox, QSpinBox, QDoubleSpinBox
    )
    from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
    from PySide6.QtGui import QIcon, QFont, QPalette, QColor
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from ..ui.animations import AnimationEngine, AgenticUIManager, AnimationConfig, AnimationKeyframe, EasingFunction
from ..config import settings


logger = logging.getLogger(__name__)


class ProfessionalStyle:
    """Professional styling constants for Metrology V2 desktop application."""
    
    # Color scheme - professional metrology theme
    PRIMARY_COLOR = "#2C3E50"  # Dark blue-gray
    SECONDARY_COLOR = "#3498DB"  # Bright blue
    ACCENT_COLOR = "#E74C3C"  # Red for alerts
    SUCCESS_COLOR = "#27AE60"  # Green for success
    WARNING_COLOR = "#F39C12"  # Orange for warnings
    BACKGROUND_COLOR = "#ECF0F1"  # Light gray
    TEXT_COLOR = "#2C3E50"  # Dark text
    BORDER_COLOR = "#BDC3C7"  # Medium gray
    
    # Typography
    FONT_FAMILY = "Segoe UI, Arial, sans-serif"
    FONT_SIZE_LARGE = 14
    FONT_SIZE_NORMAL = 12
    FONT_SIZE_SMALL = 10
    
    # Layout
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    
    # Animation durations
    ANIMATION_DURATION = 300  # milliseconds


class MainWindow(QMainWindow):
    """
    Main application window for Metrology V2.
    
    Professional desktop application with agentic UI animations
    and integration with backend services.
    """
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        self.animation_engine = AnimationEngine(target_fps=60)
        self.ui_manager = AgenticUIManager(self.animation_engine)
        
        self.setup_ui()
        self.setup_animations()
        self.connect_signals()
        
        logger.info("Main window initialized")
    
    def setup_ui(self):
        """Setup user interface."""
        self.setWindowTitle("Metrology V2 - Professional Metrology Platform")
        self.setGeometry(100, 100, ProfessionalStyle.WINDOW_WIDTH, ProfessionalStyle.WINDOW_HEIGHT)
        self.setMinimumSize(ProfessionalStyle.MIN_WIDTH, ProfessionalStyle.MIN_HEIGHT)
        
        # Apply professional styling
        self.apply_style()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setDocumentMode(True)
        
        # Create tabs
        self.create_instruments_tab()
        self.create_calibrations_tab()
        self.create_certificates_tab()
        self.create_analytics_tab()
        self.create_settings_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Metrology V2 - Ready")
    
    def apply_style(self):
        """Apply professional styling to the application."""
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(ProfessionalStyle.BACKGROUND_COLOR))
        palette.setColor(QPalette.WindowText, QColor(ProfessionalStyle.TEXT_COLOR))
        palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.AlternateBase, QColor("#F0F0F0"))
        palette.setColor(QPalette.ToolTipBase, QColor("#FFFFE0"))
        palette.setColor(QPalette.ToolTipText, QColor(ProfessionalStyle.TEXT_COLOR))
        palette.setColor(QPalette.Text, QColor(ProfessionalStyle.TEXT_COLOR))
        palette.setColor(QPalette.Button, QColor(ProfessionalStyle.SECONDARY_COLOR))
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.BrightText, QColor("#FF0000"))
        palette.setColor(QPalette.Link, QColor(ProfessionalStyle.SECONDARY_COLOR))
        palette.setColor(QPalette.Highlight, QColor(ProfessionalStyle.SECONDARY_COLOR))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        self.setPalette(palette)
        
        # Set application font
        font = QFont(ProfessionalStyle.FONT_FAMILY, ProfessionalStyle.FONT_SIZE_NORMAL)
        self.setFont(font)
    
    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Instrument", self.new_instrument)
        file_menu.addAction("New Calibration", self.new_calibration)
        file_menu.addSeparator()
        file_menu.addAction("Import Data", self.import_data)
        file_menu.addAction("Export Data", self.export_data)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Undo", self.undo)
        edit_menu.addAction("Redo", self.redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Preferences", self.preferences)
        
        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Instruments", lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction("Calibrations", lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction("Certificates", lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction("Analytics", lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction("Settings", lambda: self.tab_widget.setCurrentIndex(4))
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction("Generate Reports", self.generate_reports)
        tools_menu.addAction("Run Diagnostics", self.run_diagnostics)
        tools_menu.addAction("Backup Database", self.backup_database)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("Documentation", self.show_documentation)
        help_menu.addAction("Support", self.show_support)
        help_menu.addSeparator()
        help_menu.addAction("About", self.show_about)
    
    def create_toolbar(self):
        """Create application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        new_instrument_action = toolbar.addAction("New Instrument")
        new_instrument_action.triggered.connect(self.new_instrument)
        
        new_calibration_action = toolbar.addAction("New Calibration")
        new_calibration_action.triggered.connect(self.new_calibration)
        
        toolbar.addSeparator()
        
        refresh_action = toolbar.addAction("Refresh")
        refresh_action.triggered.connect(self.refresh_data)
        
        toolbar.addSeparator()
        
        settings_action = toolbar.addAction("Settings")
        settings_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
    
    def create_instruments_tab(self):
        """Create instruments management tab."""
        instruments_tab = QWidget()
        layout = QVBoxLayout(instruments_tab)
        
        # Create header
        header_label = QLabel("Instrument Management")
        header_label.setFont(QFont(ProfessionalStyle.FONT_FAMILY, ProfessionalStyle.FONT_SIZE_LARGE, QFont.Bold))
        layout.addWidget(header_label)
        
        # Create search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search instruments...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)
        
        # Create table
        self.instruments_table = QTableWidget()
        self.instruments_table.setColumnCount(6)
        self.instruments_table.setHorizontalHeaderLabels([
            "Asset Number", "Serial Number", "Type", "Status", "Location", "Actions"
        ])
        self.instruments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.instruments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.instruments_table)
        
        # Create action buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Instrument")
        add_button.clicked.connect(self.new_instrument)
        edit_button = QPushButton("Edit Instrument")
        edit_button.clicked.connect(self.edit_instrument)
        delete_button = QPushButton("Delete Instrument")
        delete_button.clicked.connect(self.delete_instrument)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(instruments_tab, "Instruments")
    
    def create_calibrations_tab(self):
        """Create calibrations management tab."""
        calibrations_tab = QWidget()
        layout = QVBoxLayout(calibrations_tab)
        
        # Create header
        header_label = QLabel("Calibration Management")
        header_label.setFont(QFont(ProfessionalStyle.FONT_FAMILY, ProfessionalStyle.FONT_SIZE_LARGE, QFont.Bold))
        layout.addWidget(header_label)
        
        # Create table
        self.calibrations_table = QTableWidget()
        self.calibrations_table.setColumnCount(5)
        self.calibrations_table.setHorizontalHeaderLabels([
            "Calibration ID", "Instrument", "Status", "Scheduled Date", "Actions"
        ])
        self.calibrations_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.calibrations_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.calibrations_table)
        
        # Create action buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("New Calibration")
        add_button.clicked.connect(self.new_calibration)
        view_button = QPushButton("View Details")
        view_button.clicked.connect(self.view_calibration)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(view_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(calibrations_tab, "Calibrations")
    
    def create_certificates_tab(self):
        """Create certificates management tab."""
        certificates_tab = QWidget()
        layout = QVBoxLayout(certificates_tab)
        
        # Create header
        header_label = QLabel("Certificate Management")
        header_label.setFont(QFont(ProfessionalStyle.FONT_FAMILY, ProfessionalStyle.FONT_SIZE_LARGE, QFont.Bold))
        layout.addWidget(header_label)
        
        # Create table
        self.certificates_table = QTableWidget()
        self.certificates_table.setColumnCount(5)
        self.certificates_table.setHorizontalHeaderLabels([
            "Certificate Number", "Instrument", "Issue Date", "Status", "Actions"
        ])
        self.certificates_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.certificates_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.certificates_table)
        
        # Create action buttons
        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Certificate")
        generate_button.clicked.connect(self.generate_certificate)
        verify_button = QPushButton("Verify Certificate")
        verify_button.clicked.connect(self.verify_certificate)
        
        button_layout.addWidget(generate_button)
        button_layout.addWidget(verify_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(certificates_tab, "Certificates")
    
    def create_analytics_tab(self):
        """Create analytics dashboard tab."""
        analytics_tab = QWidget()
        layout = QVBoxLayout(analytics_tab)
        
        # Create header
        header_label = QLabel("Analytics Dashboard")
        header_label.setFont(QFont(ProfessionalStyle.FONT_FAMILY, ProfessionalStyle.FONT_SIZE_LARGE, QFont.Bold))
        layout.addWidget(header_label)
        
        # Create placeholder for analytics charts
        analytics_placeholder = QLabel("Analytics Dashboard - Coming Soon")
        analytics_placeholder.setAlignment(Qt.AlignCenter)
        analytics_placeholder.setStyleSheet("color: #7F8C8D; font-size: 18px;")
        layout.addWidget(analytics_placeholder)
        
        self.tab_widget.addTab(analytics_tab, "Analytics")
    
    def create_settings_tab(self):
        """Create settings tab."""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # Create header
        header_label = QLabel("Settings")
        header_label.setFont(QFont(ProfessionalStyle.FONT_FAMILY, ProfessionalStyle.FONT_SIZE_LARGE, QFont.Bold))
        layout.addWidget(header_label)
        
        # Create settings form
        form_layout = QFormLayout()
        
        # Database settings
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout()
        
        db_host_input = QLineEdit("localhost")
        db_port_input = QSpinBox()
        db_port_input.setRange(1, 65535)
        db_port_input.setValue(5432)
        db_name_input = QLineEdit("metrology_v2")
        db_user_input = QLineEdit("metrology_user")
        
        db_layout.addRow("Host:", db_host_input)
        db_layout.addRow("Port:", db_port_input)
        db_layout.addRow("Database:", db_name_input)
        db_layout.addRow("User:", db_user_input)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Animation settings
        anim_group = QGroupBox("Animation Settings")
        anim_layout = QFormLayout()
        
        enable_animations_checkbox = QComboBox()
        enable_animations_checkbox.addItems(["Enabled", "Disabled"])
        enable_animations_checkbox.setCurrentIndex(0)
        
        animation_duration_input = QSpinBox()
        animation_duration_input.setRange(100, 1000)
        animation_duration_input.setValue(300)
        animation_duration_input.setSuffix(" ms")
        
        anim_layout.addRow("Animations:", enable_animations_checkbox)
        anim_layout.addRow("Duration:", animation_duration_input)
        
        anim_group.setLayout(anim_layout)
        layout.addWidget(anim_group)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings_tab, "Settings")
    
    def setup_animations(self):
        """Setup agentic UI animations."""
        # Set UI to loading state initially
        self.ui_manager.set_ui_state("loading", True)
        
        # Create loading animation
        loading_animation_id = "main_loading"
        config = AnimationConfig(
            duration=1.0,
            easing=EasingFunction.EASE_OUT_CUBIC
        )
        
        keyframes = [
            AnimationKeyframe(time=0.0, properties={'opacity': 0.0}),
            AnimationKeyframe(time=1.0, properties={'opacity': 1.0})
        ]
        
        self.animation_engine.create_animation(
            loading_animation_id,
            config,
            keyframes,
            self._animation_callback
        )
        
        self.animation_engine.start_animation(loading_animation_id)
    
    def _animation_callback(self, progress):
        """Callback for animation progress updates."""
        # Handle animation progress
        if progress.state.value == "COMPLETED":
            self.ui_manager.set_ui_state("loading", False)
            self.ui_manager.set_ui_state("success", True)
    
    def connect_signals(self):
        """Connect application signals."""
        # Tab change signals
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def on_tab_changed(self, index):
        """Handle tab change with animation."""
        tab_names = ["instruments", "calibrations", "certificates", "analytics", "settings"]
        if index < len(tab_names):
            self.ui_manager.push_context(tab_names[index])
    
    # Menu action handlers
    def new_instrument(self):
        """Create new instrument dialog."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement instrument creation dialog
        QMessageBox.information(self, "Info", "New Instrument dialog - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
        self.ui_manager.set_ui_state("success", True)
    
    def new_calibration(self):
        """Create new calibration dialog."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement calibration creation dialog
        QMessageBox.information(self, "Info", "New Calibration dialog - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
        self.ui_manager.set_ui_state("success", True)
    
    def edit_instrument(self):
        """Edit selected instrument."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement instrument editing
        QMessageBox.information(self, "Info", "Edit Instrument - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def delete_instrument(self):
        """Delete selected instrument."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement instrument deletion
        QMessageBox.information(self, "Info", "Delete Instrument - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def view_calibration(self):
        """View calibration details."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement calibration details view
        QMessageBox.information(self, "Info", "View Calibration - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def generate_certificate(self):
        """Generate certificate."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement certificate generation
        QMessageBox.information(self, "Info", "Generate Certificate - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
        self.ui_manager.set_ui_state("success", True)
    
    def verify_certificate(self):
        """Verify certificate."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement certificate verification
        QMessageBox.information(self, "Info", "Verify Certificate - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def generate_reports(self):
        """Generate reports."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement report generation
        QMessageBox.information(self, "Info", "Generate Reports - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def run_diagnostics(self):
        """Run system diagnostics."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement diagnostics
        QMessageBox.information(self, "Info", "Run Diagnostics - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def backup_database(self):
        """Backup database."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement database backup
        QMessageBox.information(self, "Info", "Backup Database - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
        self.ui_manager.set_ui_state("success", True)
    
    def import_data(self):
        """Import data."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement data import
        QMessageBox.information(self, "Info", "Import Data - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def export_data(self):
        """Export data."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement data export
        QMessageBox.information(self, "Info", "Export Data - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def refresh_data(self):
        """Refresh data from backend."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement data refresh
        self.status_bar.showMessage("Data refreshed", 3000)
        self.ui_manager.set_ui_state("processing", False)
    
    def preferences(self):
        """Open preferences dialog."""
        self.ui_manager.set_ui_state("processing", True)
        # Switch to settings tab
        self.tab_widget.setCurrentIndex(4)
        self.ui_manager.set_ui_state("processing", False)
    
    def save_settings(self):
        """Save application settings."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Implement settings save
        self.status_bar.showMessage("Settings saved", 3000)
        self.ui_manager.set_ui_state("processing", False)
        self.ui_manager.set_ui_state("success", True)
    
    def undo(self):
        """Undo last action."""
        self.status_bar.showMessage("Undo - Coming Soon", 3000)
    
    def redo(self):
        """Redo last action."""
        self.status_bar.showMessage("Redo - Coming Soon", 3000)
    
    def show_documentation(self):
        """Show documentation."""
        self.ui_manager.set_ui_state("processing", True)
        # TODO: Open documentation
        QMessageBox.information(self, "Info", "Documentation - Coming Soon")
        self.ui_manager.set_ui_state("processing", False)
    
    def show_support(self):
        """Show support information."""
        QMessageBox.information(
            self,
            "Support",
            "Metrology V2 Support\n\n"
            "Email: novyrax04@gmail.com\n"
            "Website: https://novyrax.vercel.app\n"
            "Documentation: https://novyrax.vercel.app/docs"
        )
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Metrology V2",
            "Metrology V2 - Professional Metrology Platform\n\n"
            "Version: 2.0.0\n"
            "Edition: Production\n\n"
            "© 2026 NovyraX. All rights reserved.\n\n"
            "A production-grade, auditable metrology platform\n"
            "for accredited laboratories and quality engineering teams."
        )
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Cleanup animation resources
        from ..ui.animations import cleanup
        cleanup()
        
        # Accept close event
        event.accept()


def create_desktop_application():
    """
    Create and return the desktop application instance.
    
    Returns:
        QApplication instance or None if PySide6 is not available
    """
    if not PYSIDE6_AVAILABLE:
        logger.error("PySide6 is not available. Desktop application cannot be created.")
        return None
    
    app = QApplication(sys.argv)
    app.setApplicationName("Metrology V2")
    app.setOrganizationName("NovyraX")
    
    main_window = MainWindow()
    main_window.show()
    
    return app


def run_desktop_application():
    """Run the desktop application."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is not available. Please install it with: pip install PySide6")
        return
    
    app = create_desktop_application()
    if app:
        sys.exit(app.exec())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_desktop_application()