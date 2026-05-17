# eye_guard.py

import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSpinBox,
    QSystemTrayIcon,
    QMenu,
    QMessageBox,
    QFrame,
    QSizePolicy,
)


class BreakOverlay(QWidget):
    def __init__(self, on_back_clicked):
        super().__init__()
        self.on_back_clicked = on_back_clicked
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Eye Guard Break")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        overlay = QFrame()
        overlay.setObjectName("overlay")
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(40, 40, 40, 40)
        overlay_layout.setSpacing(20)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(520)
        card.setMaximumWidth(760)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(18)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Time to rest your eyes")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Look at something far away for 20 seconds.\n"
            "Relax your eyes, blink a few times, then come back."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.back_button = QPushButton("I am back")
        self.back_button.setObjectName("primary")
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.handle_back)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        overlay_layout.addWidget(card)
        root.addWidget(overlay)

        self.setStyleSheet("""
            #overlay {
                background-color: rgba(10, 10, 14, 180);
            }

            #card {
                background-color: rgba(31, 31, 40, 235);
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 28px;
            }

            QLabel#title {
                color: white;
                font-size: 30px;
                font-weight: 700;
                letter-spacing: 0.2px;
            }

            QLabel#subtitle {
                color: #c7c7d1;
                font-size: 15px;
                line-height: 1.4em;
            }

            QPushButton#primary {
                background-color: #48c78e;
                color: #0b0b0f;
                border: none;
                border-radius: 14px;
                padding: 14px 28px;
                font-size: 15px;
                font-weight: 700;
                min-width: 170px;
            }

            QPushButton#primary:hover {
                background-color: #5edaa0;
            }

            QPushButton#primary:pressed {
                background-color: #39b37e;
            }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()
        self.activateWindow()

    def handle_back(self):
        self.hide()
        self.on_back_clicked()

    def keyPressEvent(self, event):
        # Prevent accidental dismissal by keyboard shortcuts.
        event.ignore()

    def closeEvent(self, event):
        # Hide instead of destroying.
        event.ignore()
        self.hide()


class EyeGuard(QWidget):
    def __init__(self):
        super().__init__()

        self.interval_minutes = 20
        self.break_seconds = 20
        self.running = True
        self.remaining_seconds = self.interval_minutes * 60

        self.overlay = BreakOverlay(self.on_break_finished)

        self.setup_ui()
        self.setup_timer()
        self.setup_tray()

    def setup_ui(self):
        self.setWindowTitle("Eye Guard")
        self.setMinimumSize(560, 360)
        self.resize(640, 420)

        self.setStyleSheet("""
            QWidget {
                background-color: #1f1f28;
                color: #f2f2f2;
                font-family: Inter, Ubuntu, Sans-serif;
            }

            QLabel#title {
                font-size: 30px;
                font-weight: 700;
                color: white;
            }

            QLabel#subtitle {
                font-size: 13px;
                color: #9ca3af;
            }

            QLabel#timer {
                font-size: 58px;
                font-weight: 800;
                color: #48c78e;
                padding: 8px;
                min-width: 220px;
                min-height: 90px;
            }

            QLabel#small {
                font-size: 13px;
                color: #c9c9d4;
            }

            QPushButton {
                background-color: #2b2b38;
                border: 1px solid #3b3b4c;
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #363648;
            }

            QPushButton#primary {
                background-color: #48c78e;
                color: #0b0b0f;
                font-weight: 700;
                border: none;
            }

            QPushButton#primary:hover {
                background-color: #5edaa0;
            }

            QSpinBox {
                background-color: #2b2b38;
                border: 1px solid #3b3b4c;
                border-radius: 10px;
                padding: 6px 10px;
                min-width: 90px;
                font-size: 14px;
            }

            QFrame#card {
                background-color: #252532;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 10);
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(18)

        title = QLabel("Eye Guard")
        title.setObjectName("title")

        subtitle = QLabel("20-20-20 eye rest reminder")
        subtitle.setObjectName("subtitle")

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        self.timer_label = QLabel()
        self.timer_label.setObjectName("timer")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        hint = QLabel("Next reminder countdown")
        hint.setObjectName("small")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(self.timer_label)
        card_layout.addWidget(hint)

        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)

        interval_text = QLabel("Reminder every")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 180)
        self.interval_spin.setValue(20)
        self.interval_spin.valueChanged.connect(self.update_interval)
        minutes_text = QLabel("minutes")

        settings_row.addWidget(interval_text)
        settings_row.addWidget(self.interval_spin)
        settings_row.addWidget(minutes_text)
        settings_row.addStretch()

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(10)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_timer)

        test_button = QPushButton("Test Reminder")
        test_button.setObjectName("primary")
        test_button.clicked.connect(self.show_break_overlay)

        buttons_row.addWidget(self.pause_button)
        buttons_row.addWidget(reset_button)
        buttons_row.addWidget(test_button)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(4)
        main_layout.addWidget(card, stretch=1)
        main_layout.addLayout(settings_row)
        main_layout.addStretch()
        main_layout.addLayout(buttons_row)

        self.update_timer_display()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Eye Guard")

        menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Quit", self)

        show_action.triggered.connect(self.show_window)
        quit_action.triggered.connect(QApplication.quit)

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_clicked)
        self.tray.show()

    def tick(self):
        if not self.running:
            return

        self.remaining_seconds -= 1

        if self.remaining_seconds <= 0:
            self.show_break_overlay()
            self.reset_timer()

        self.update_timer_display()

    def update_timer_display(self):
        minutes = max(0, self.remaining_seconds) // 60
        seconds = max(0, self.remaining_seconds) % 60
        self.timer_label.setText(f"{minutes:02}:{seconds:02}")

    def update_interval(self):
        self.interval_minutes = self.interval_spin.value()
        self.reset_timer()

    def reset_timer(self):
        self.remaining_seconds = self.interval_minutes * 60
        self.update_timer_display()

    def toggle_pause(self):
        self.running = not self.running
        self.pause_button.setText("Pause" if self.running else "Resume")

    def show_break_overlay(self):
        if self.overlay.isVisible():
            return

        self.overlay.showFullScreen()
        self.overlay.raise_()
        self.overlay.activateWindow()

    def on_break_finished(self):
        self.reset_timer()
        self.show_window()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "Eye Guard",
            "Application minimized to tray.",
            QSystemTrayIcon.MessageIcon.Information,
            2500
        )

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = EyeGuard()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()