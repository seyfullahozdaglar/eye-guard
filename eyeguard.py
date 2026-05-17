# eyeguard.py

import os
import sys

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QSettings,
    QPropertyAnimation,
    QEasingCurve,
    pyqtProperty,
)
from PyQt6.QtGui import QAction, QIcon, QPainter, QColor
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
    QFrame,
    QSizePolicy,
)


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath("")
    return os.path.join(base_path, relative_path)


ICON_PATH = resource_path("icon.png")


class BreakOverlay(QWidget):
    def __init__(self, on_back_clicked):
        super().__init__()
        self.on_back_clicked = on_back_clicked

        self._overlay_alpha = 0.0
        self._close_after_fade = False
        self.break_duration = 20
        self.remaining_seconds = 20

        self.fade_animation = QPropertyAnimation(self, b"overlayAlpha")
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.finished.connect(self._on_fade_finished)

        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self._tick_break)

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Eye Guard Break")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.center_wrap = QFrame()
        self.center_wrap.setObjectName("center_wrap")

        wrap_layout = QVBoxLayout(self.center_wrap)
        wrap_layout.setContentsMargins(40, 40, 40, 40)
        wrap_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(520)
        card.setMaximumWidth(760)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 30, 32, 30)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Time to rest your eyes")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Look at something far away.\n"
            "Blink normally and relax your eyes."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.countdown_label = QLabel("20")
        self.countdown_label.setObjectName("countdown")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        seconds_label = QLabel("seconds left")
        seconds_label.setObjectName("seconds_label")
        seconds_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.back_button = QPushButton("I am back")
        self.back_button.setObjectName("primary")
        self.back_button.clicked.connect(self.handle_back)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(6)
        card_layout.addWidget(self.countdown_label)
        card_layout.addWidget(seconds_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        wrap_layout.addWidget(card)
        root.addWidget(self.center_wrap)

        self.setStyleSheet("""
            #center_wrap {
                background: transparent;
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
            }

            QLabel#subtitle {
                color: #c7c7d1;
                font-size: 15px;
                line-height: 1.4em;
            }

            QLabel#countdown {
                color: #48c78e;
                font-size: 72px;
                font-weight: 800;
                min-width: 180px;
                min-height: 90px;
            }

            QLabel#seconds_label {
                color: #c9c9d4;
                font-size: 14px;
                letter-spacing: 1px;
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

    def start_break(self, duration_seconds: int = 20):
        if self.isVisible():
            return

        self.break_duration = max(1, duration_seconds)
        self.remaining_seconds = self.break_duration
        self._close_after_fade = False

        self._update_overlay_alpha(0.0)
        self._update_countdown_text()

        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        self.fade_animation.stop()
        self.fade_animation.setDuration(250)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(0.88)
        self.fade_animation.start()

        self.break_timer.start(1000)

    def handle_back(self):
        self.break_timer.stop()
        self._begin_close_animation()

    def _begin_close_animation(self):
        if not self.isVisible():
            self.on_back_clicked()
            return

        self._close_after_fade = True
        self.fade_animation.stop()
        self.fade_animation.setDuration(220)
        self.fade_animation.setStartValue(self._overlay_alpha)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()

    def _tick_break(self):
        self.remaining_seconds -= 1

        if self.remaining_seconds <= 0:
            self.break_timer.stop()
            self._begin_close_animation()
            return

        self._update_countdown_text()

        target_alpha = 0.88 * (self.remaining_seconds / self.break_duration)
        target_alpha = max(0.0, min(0.88, target_alpha))

        self.fade_animation.stop()
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(self._overlay_alpha)
        self.fade_animation.setEndValue(target_alpha)
        self.fade_animation.start()

    def _update_countdown_text(self):
        self.countdown_label.setText(str(max(0, self.remaining_seconds)))

    def _on_fade_finished(self):
        if self._close_after_fade:
            self._close_after_fade = False
            self.hide()
            self._update_overlay_alpha(0.0)
            self.on_back_clicked()

    def _get_overlay_alpha(self) -> float:
        return self._overlay_alpha

    def _set_overlay_alpha(self, value: float):
        self._overlay_alpha = max(0.0, min(1.0, float(value)))
        self.update()

    overlayAlpha = pyqtProperty(float, fget=_get_overlay_alpha, fset=_set_overlay_alpha)

    def _update_overlay_alpha(self, value: float):
        self._overlay_alpha = max(0.0, min(1.0, float(value)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        alpha = int(255 * self._overlay_alpha)
        painter.fillRect(self.rect(), QColor(10, 10, 14, alpha))
        super().paintEvent(event)

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class EyeGuard(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("Seyfullah", "EyeGuard")

        self.interval_minutes = int(self.settings.value("interval_minutes", 20))
        self.running = True
        self.remaining_seconds = self.interval_minutes * 60

        self.overlay = BreakOverlay(self.on_break_finished)

        self.setup_ui()
        self.setup_timer()
        self.setup_tray()

    def setup_ui(self):
        self.setWindowTitle("Eye Guard")
        self.setWindowIcon(QIcon(ICON_PATH))

        self.setMinimumSize(560, 360)
        self.resize(640, 420)

        geometry = self.settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)

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
        self.timer_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        hint = QLabel("Next reminder countdown")
        hint.setObjectName("small")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(self.timer_label)
        card_layout.addWidget(hint)

        settings_row = QHBoxLayout()

        interval_text = QLabel("Reminder every")

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 180)
        self.interval_spin.setValue(self.interval_minutes)
        self.interval_spin.valueChanged.connect(self.update_interval)

        minutes_text = QLabel("minutes")

        settings_row.addWidget(interval_text)
        settings_row.addWidget(self.interval_spin)
        settings_row.addWidget(minutes_text)
        settings_row.addStretch()

        buttons_row = QHBoxLayout()

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
        self.tray = QSystemTrayIcon(QIcon(ICON_PATH), self)
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
            return

        self.update_timer_display()

    def update_timer_display(self):
        minutes = max(0, self.remaining_seconds) // 60
        seconds = max(0, self.remaining_seconds) % 60
        self.timer_label.setText(f"{minutes:02}:{seconds:02}")

    def update_interval(self):
        self.interval_minutes = self.interval_spin.value()
        self.settings.setValue("interval_minutes", self.interval_minutes)
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
        self.overlay.start_break(20)

    def on_break_finished(self):
        self.reset_timer()
        self.show_window()

    def closeEvent(self, event):
        self.settings.setValue("window_geometry", self.saveGeometry())
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "Eye Guard",
            "Application minimized to tray.",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
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
    app.setWindowIcon(QIcon(ICON_PATH))

    window = EyeGuard()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()