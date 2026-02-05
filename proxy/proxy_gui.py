#!/usr/bin/env python3
"""
Meshtastic Multi-Client TCP Proxy - Qt GUI Application
"""

import sys
import os

# Add current directory and parent to path for imports
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)
sys.path.insert(0, os.path.dirname(application_path))

import asyncio
import logging
from datetime import datetime
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QGroupBox, QListWidget, QCheckBox, QComboBox, QSplitter, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QFont, QPalette, QColor, QTextCursor
import threading

# Import the proxy
from multi_client_proxy import MultiClientProxy


class QTextEditLogger(logging.Handler):
    """Custom logging handler that emits to Qt signal."""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)


class ProxyThread(QThread):
    """Thread to run the async proxy."""

    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    client_count_signal = pyqtSignal(int)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.proxy = None
        self.loop = None
        self.running = False

    def run(self):
        """Run the proxy in this thread."""
        self.running = True

        # Create new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Set up Gemini API key if provided
        if self.config.get('gemini_api_key'):
            os.environ['GEMINI_API_KEY'] = self.config['gemini_api_key']

        # Create proxy instance
        self.proxy = MultiClientProxy(
            listen_host=self.config['listen_host'],
            listen_port=self.config['listen_port'],
            radio_host=self.config['radio_host'],
            radio_port=self.config['radio_port'],
            channel_index=self.config['channel_index'],
            response_delay=self.config['response_delay']
        )

        try:
            self.status_signal.emit("Starting...")
            self.loop.run_until_complete(self.proxy.start())
        except Exception as e:
            self.log_signal.emit(f"ERROR: {e}")
            self.status_signal.emit("Error")
        finally:
            self.running = False
            self.status_signal.emit("Stopped")

    def stop(self):
        """Stop the proxy."""
        if self.proxy and self.loop:
            self.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.proxy.stop())
            )
            self.running = False


class ProxyGUI(QMainWindow):
    """Main GUI window for the Meshtastic Proxy."""

    # Define signals as class attributes
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.proxy_thread = None
        self.settings = QSettings('Meshtastic', 'ProxyGUI')
        self.start_time = None
        self.message_count = 0

        self.init_ui()
        self.load_settings()
        self.setup_logging()

        # Timer for statistics updates
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
        self.stats_timer.start(1000)

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Meshtastic Multi-Client TCP Proxy")
        self.setGeometry(100, 100, 1200, 800)

        # Apply dark theme
        self.apply_dark_theme()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel - Configuration and Controls
        left_panel = QVBoxLayout()

        # Configuration Group
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()

        # Listen settings
        listen_layout = QHBoxLayout()
        listen_layout.addWidget(QLabel("Listen Host:"))
        self.listen_host_input = QLineEdit("0.0.0.0")
        listen_layout.addWidget(self.listen_host_input)
        listen_layout.addWidget(QLabel("Port:"))
        self.listen_port_input = QSpinBox()
        self.listen_port_input.setRange(1, 65535)
        self.listen_port_input.setValue(4404)
        listen_layout.addWidget(self.listen_port_input)
        config_layout.addLayout(listen_layout)

        # Radio settings
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(QLabel("Radio Host:"))
        self.radio_host_input = QLineEdit("192.168.2.144")
        radio_layout.addWidget(self.radio_host_input)
        radio_layout.addWidget(QLabel("Port:"))
        self.radio_port_input = QSpinBox()
        self.radio_port_input.setRange(1, 65535)
        self.radio_port_input.setValue(4403)
        radio_layout.addWidget(self.radio_port_input)
        config_layout.addLayout(radio_layout)

        # Channel and delay
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channel:"))
        self.channel_input = QSpinBox()
        self.channel_input.setRange(0, 7)
        self.channel_input.setValue(2)
        channel_layout.addWidget(self.channel_input)
        channel_layout.addWidget(QLabel("Response Delay:"))
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setRange(0, 60)
        self.delay_input.setValue(2.0)
        self.delay_input.setSuffix(" s")
        channel_layout.addWidget(self.delay_input)
        config_layout.addLayout(channel_layout)

        # Gemini API Key
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("Gemini API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Optional - for /gem commands")
        api_layout.addWidget(self.api_key_input)
        config_layout.addLayout(api_layout)

        config_group.setLayout(config_layout)
        left_panel.addWidget(config_group)

        # Control Group
        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout()

        # Start/Stop button
        self.start_stop_btn = QPushButton("Start Proxy")
        self.start_stop_btn.setMinimumHeight(50)
        self.start_stop_btn.clicked.connect(self.toggle_proxy)
        control_layout.addWidget(self.start_stop_btn)

        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        control_layout.addLayout(status_layout)

        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        # Statistics Group
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()

        self.stats_clients = QLabel("Connected Clients: 0")
        self.stats_messages = QLabel("Messages Processed: 0")
        self.stats_uptime = QLabel("Uptime: 00:00:00")
        self.stats_radio = QLabel("Radio: Disconnected")

        stats_layout.addWidget(self.stats_clients)
        stats_layout.addWidget(self.stats_messages)
        stats_layout.addWidget(self.stats_uptime)
        stats_layout.addWidget(self.stats_radio)

        stats_group.setLayout(stats_layout)
        left_panel.addWidget(stats_group)

        # Connected Clients Group
        clients_group = QGroupBox("Connected Clients")
        clients_layout = QVBoxLayout()

        self.clients_list = QListWidget()
        clients_layout.addWidget(self.clients_list)

        clients_group.setLayout(clients_layout)
        left_panel.addWidget(clients_group)

        left_panel.addStretch()

        # Right panel - Logs
        right_panel = QVBoxLayout()

        # Log controls
        log_controls = QHBoxLayout()
        log_controls.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self.change_log_level)
        log_controls.addWidget(self.log_level_combo)

        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        log_controls.addWidget(self.auto_scroll_check)

        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        log_controls.addWidget(clear_btn)

        log_controls.addStretch()
        right_panel.addLayout(log_controls)

        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setFont(QFont("Courier", 9))
        right_panel.addWidget(self.log_viewer)

        # Combine panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(400)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage("Ready")

    def apply_dark_theme(self):
        """Apply a dark color scheme."""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))

        self.setPalette(dark_palette)

    def setup_logging(self):
        """Set up logging to capture to GUI."""
        # Get root logger
        logger = logging.getLogger()

        # Create handler
        handler = QTextEditLogger(self.log_signal)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

        # Connect signal
        self.log_signal.connect(self.append_log)

    def change_log_level(self, level):
        """Change the logging level."""
        logging.getLogger().setLevel(getattr(logging, level))
        self.append_log(f"Log level changed to {level}")

    def append_log(self, message):
        """Append a message to the log viewer."""
        self.log_viewer.append(message)
        if self.auto_scroll_check.isChecked():
            self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)

    def clear_logs(self):
        """Clear the log viewer."""
        self.log_viewer.clear()

    def toggle_proxy(self):
        """Start or stop the proxy."""
        if self.proxy_thread is None or not self.proxy_thread.running:
            self.start_proxy()
        else:
            self.stop_proxy()

    def start_proxy(self):
        """Start the proxy server."""
        config = {
            'listen_host': self.listen_host_input.text(),
            'listen_port': self.listen_port_input.value(),
            'radio_host': self.radio_host_input.text(),
            'radio_port': self.radio_port_input.value(),
            'channel_index': self.channel_input.value(),
            'response_delay': self.delay_input.value(),
            'gemini_api_key': self.api_key_input.text()
        }

        # Save settings
        self.save_settings()

        # Disable config inputs
        self.set_config_enabled(False)

        # Create and start thread
        self.proxy_thread = ProxyThread(config)
        self.proxy_thread.log_signal.connect(self.append_log)
        self.proxy_thread.status_signal.connect(self.update_status)
        self.proxy_thread.client_count_signal.connect(self.update_client_count)
        self.proxy_thread.start()

        self.start_stop_btn.setText("Stop Proxy")
        self.start_time = datetime.now()

    def stop_proxy(self):
        """Stop the proxy server."""
        if self.proxy_thread:
            self.proxy_thread.stop()
            self.proxy_thread.wait(5000)  # Wait up to 5 seconds
            self.proxy_thread = None

        self.start_stop_btn.setText("Start Proxy")
        self.set_config_enabled(True)
        self.start_time = None

    def set_config_enabled(self, enabled):
        """Enable or disable configuration inputs."""
        self.listen_host_input.setEnabled(enabled)
        self.listen_port_input.setEnabled(enabled)
        self.radio_host_input.setEnabled(enabled)
        self.radio_port_input.setEnabled(enabled)
        self.channel_input.setEnabled(enabled)
        self.delay_input.setEnabled(enabled)
        self.api_key_input.setEnabled(enabled)

    def update_status(self, status):
        """Update the status label."""
        self.status_label.setText(status)
        if status == "Running":
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
        elif status == "Stopped":
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
        elif status == "Error":
            self.status_label.setStyleSheet("font-weight: bold; color: orange;")
        else:
            self.status_label.setStyleSheet("font-weight: bold; color: yellow;")

    def update_client_count(self, count):
        """Update the client count display."""
        self.stats_clients.setText(f"Connected Clients: {count}")

    def update_statistics(self):
        """Update statistics display."""
        # Update uptime
        if self.start_time:
            uptime = datetime.now() - self.start_time
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            seconds = uptime.seconds % 60
            self.stats_uptime.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")

        # Update client list
        if self.proxy_thread and self.proxy_thread.proxy:
            proxy = self.proxy_thread.proxy
            self.clients_list.clear()
            for client_id, client in proxy.clients.items():
                self.clients_list.addItem(f"Client {client_id}: {client.address}")
            self.stats_clients.setText(f"Connected Clients: {len(proxy.clients)}")

            # Update radio status
            if proxy.radio_connected.is_set():
                self.stats_radio.setText("Radio: Connected")
                self.stats_radio.setStyleSheet("color: green;")
            else:
                self.stats_radio.setText("Radio: Disconnected")
                self.stats_radio.setStyleSheet("color: red;")

    def save_settings(self):
        """Save configuration to settings."""
        self.settings.setValue('listen_host', self.listen_host_input.text())
        self.settings.setValue('listen_port', self.listen_port_input.value())
        self.settings.setValue('radio_host', self.radio_host_input.text())
        self.settings.setValue('radio_port', self.radio_port_input.value())
        self.settings.setValue('channel_index', self.channel_input.value())
        self.settings.setValue('response_delay', self.delay_input.value())
        # Note: API key is not saved for security

    def load_settings(self):
        """Load configuration from settings."""
        self.listen_host_input.setText(self.settings.value('listen_host', '0.0.0.0'))
        self.listen_port_input.setValue(int(self.settings.value('listen_port', 4404)))
        self.radio_host_input.setText(self.settings.value('radio_host', '192.168.2.144'))
        self.radio_port_input.setValue(int(self.settings.value('radio_port', 4403)))
        self.channel_input.setValue(int(self.settings.value('channel_index', 2)))
        self.delay_input.setValue(float(self.settings.value('response_delay', 2.0)))

    def closeEvent(self, event):
        """Handle window close event."""
        if self.proxy_thread and self.proxy_thread.running:
            self.stop_proxy()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Meshtastic Proxy")

    window = ProxyGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
