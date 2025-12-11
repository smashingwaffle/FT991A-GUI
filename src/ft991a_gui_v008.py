import sys
import time
import threading
import xml.etree.ElementTree as ET
from functools import partial
from pathlib import Path

import serial
import serial.tools.list_ports

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox,
    QHBoxLayout, QMessageBox, QProgressBar, QTextEdit, QTabWidget,
    QFileDialog, QLineEdit, QStyleFactory, QGroupBox, QSlider,
    QCheckBox, QGridLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import (
    QPalette, QColor, QLinearGradient, QBrush, QPen, QFont, QPainter
)
from PyQt6.QtCore import Qt, QTimer

SERIAL_READ_TIMEOUT_MS = 60  # quick peek window for IF reply

BASE_DIR = Path(__file__).resolve().parent


def resource_path(name: str) -> str:
    """Resolve XML/preset files relative to this script, for safety."""
    p = Path(name)
    if not p.is_absolute():
        p = BASE_DIR / p
    return str(p)


MENU_DESCRIPTIONS = {
    "001": ("AGC FAST DELAY", "20 - 4000", "msec"),
    "002": ("AGC MID DELAY", "20 - 4000", "msec"),
    "003": ("AGC SLOW DELAY", "20 - 4000", "msec"),
    "004": ("HOME FUNCTION", "0:SCOPE, 1:FUNCTION", ""),
    "005": ("MY CALL INDICATOR", "0 - 5", "sec"),
    "006": ("DISPLAY COLOR", "0:BLUE, 1:GRAY, 2:GREEN, 3:ORANGE, 4:PURPLE, 5:RED, 6:SKY BLUE", ""),
    "007": ("DIMMER LED", "0:1, 1:2", ""),
    "008": ("DIMMER TFT", "0-15", ""),
    "009": ("DISPLAY BAR MTR PEAK HOLD", "0:0s, 1:0.5s, 2:1s, 3:2s", ""),
    "010": ("DVS RX OUT LEVEL", "0-100", ""),
    "011": ("DVS TX OUT LEVEL", "0-100", ""),
    "012": ("KEYER TYPE", "0:OFF, 1:BUG, 2:ELEKEY-A, 3:ELEKEY-B, 4:ELEKEY-Y, 5:ACS", ""),
    "013": ("KEYER DOT DASH", "0:NORMAL, 1:REVERSE", ""),
    "014": ("KEYER CW WEIGHT", "2.5 - 4.5", ""),
    "015": ("KEYER BEACON TIME", "0:OFF, 1:1 - 240", "sec"),
    "016": ("KEYER NUMBER STYLE", "0:1290, 1:AUNO, 2:AUNT, 3:A2NO, 4:A2NT, 5:12NO, 6:12NT", ""),
    "017": ("KEYER CONTEST NUMBER", "0-9999", ""),
    "018": ("KEYER CW MEMORY 1", "0:TEXT, 1:MESSAGE", ""),
    "019": ("KEYER CW MEMORY 2", "0:TEXT, 1:MESSAGE", ""),
    "020": ("KEYER CW MEMORY 3", "0:TEXT, 1:MESSAGE", ""),
    "021": ("KEYER CW MEMORY 4", "0:TEXT, 1:MESSAGE", ""),
    "022": ("KEYER CW MEMORY 5", "0:TEXT, 1:MESSAGE", ""),
    "023": ("NB WIDTH", "0:1ms, 1:3ms, 2:10ms", ""),
    "024": ("NB REJECTION", "0:10 dB, 1:30 dB, 2:50dB", ""),
    "025": ("NB LEVEL", "0-10", ""),
    "026": ("BEEP LEVEL", "0-100", ""),
    "027": ("Please set this at the radio", "TIMEZONE", ""),
    "028": ("GPS/232C SELECT", "0:GPS1, 1:GPS2, 2:RS232C", ""),
    "029": ("232C RATE", "0:4800bps, 1:9600bps, 2:19200bps, 3:38400bps", ""),
    "030": ("232C TOT", "0:10ms, 1:100ms, 2:1000ms, 3:3000", ""),
    "031": ("CAT RATE", "0:4800bps, 1:9600bps, 2:19200bps, 3:38400bps", ""),
    "032": ("CAT TIMEOUT", "0:10ms, 1:100ms, 2:1000ms, 3:3000ms", ""),
    "033": ("CAT RTS", "0:DISABLE, 1:ENABLE", ""),
    "034": ("MEM GROUP", "0:DISABLE, 1:ENABLE", ""),
    "035": ("QUICK SPLIT FREQ", "-20 to +20 kHz", ""),
    "036": ("TX TIMEOUT TIMER", "0-30min", ""),
    "037": ("MIC SCAN", "0:DISABLE, 1:ENABLE", ""),
    "038": ("MIC SCAN RESUME", "0:PAUSE, 1:TIME", ""),
    "039": ("REF FREQUENCY ADJUST", "-25 to +25 kHz", ""),
    "040": ("CLAR MODE SELECT", "0:RX, 1:TX, 2:TRX", ""),
    "041": ("Mode:AM LCUT Freq", "0:OFF, 1:100Hz - 19:1000Hz", ""),
    "042": ("Mode:AM LCUT Slope", "0:6dB/oct, 1:18dB/oct", ""),
    "043": ("Mode:AM HCUT Freq", "0:OFF, 1:700Hz - 67:4000Hz", ""),
    "044": ("Mode:AM HCUT Slope", "0:6dB/oct, 1:18dB/oct", ""),
    "045": ("Mode:AM MIC SEL", "0:MIC, 1:REAR", ""),
    "046": ("Mode:AM OUT LEVEL", "0-100", ""),
    "047": ("Mode:AM PTT SELECT", "0:DAKY, 1:RTS, 2:DTR", ""),
    "048": ("Mode:AM PORT SELECT", "0:DATA, 1:USB", ""),
    "049": ("Mode:AM DATA GAIN", "0-100", ""),
    "050": ("Mode:CW LCUT FREQ", "0:OFF, 1:100Hz - 19:1000Hz", ""),
    "051": ("Mode:CW LCUT SLOPE", "0:6dB/oct, 1:18dB/oct", ""),
    "052": ("Mode:CW HCUT FREQ", "0:OFF, 1:700Hz - 67:4000Hz", ""),
    "053": ("Mode:CW HCUT SLOPE", "0:6dB/oct, 1:18dB/oct", ""),
    "054": ("Mode:CW OUT LEVEL", "0-100", ""),
    "055": ("Mode:CW CW AUTO MODE", "0:OFF, 1:50MHz, 2:ON", ""),
    "056": ("Mode:CW CW BK-IN", "0:SEMI, 1:FULL", ""),
    "057": ("MODE:CW CW BK-IN DELAY", "30 - 3000", "msec"),
    "058": ("Mode:CW CW WAVE SHAPE", "0:1ms, 1:2ms, 2:4ms, 3:6ms", ""),
    "059": ("Mode:CW CW FREQ DISPLAY", "0:DIRECT, 1:OFFSET", ""),
    "060": ("Mode:CW PC KEYING", "0:OFF, 1:DAKY, 2:RTS, 3:DTR", ""),
    "061": ("Mode:CW QSK", "0:15ms, 1:20ms, 2:25ms, 3:30ms", ""),
    "062": ("Mode:DATA DATA MODE", "0:PSK, 1:OTHER", ""),
    "063": ("PSK TONE", "0:1000, 1:1500, 2:2000", ""),
    "064": ("Mode:DATA OTHER DISP SSB", "-3000 to +3000 kHz", ""),
    "065": ("Mode:DATA OTHER SHIFT SSB", "-3000 to +3000 kHz", ""),
    "066": ("Mode:DATA DATA LCUT FREQ", "0:OFF, 1:100Hz - 19:1000Hz", ""),
    "067": ("Mode:DATA DATA LCUT SLOPE", "0:6dB/oct, 1:18dB/oct", ""),
    "068": ("Mode:DATA DATA HCUT FREQ", "0:OFF, 1:700Hz - 67:4000Hz", ""),
    "069": ("Mode:DATA DATA HCUT SLOPE", "0:6dB/oct, 1:18dB/oct", ""),
    "070": ("Mode:DATA DATA IN SELECT", "0:MIC, 1:REAR", ""),
    "071": ("Mode:DATA PTT SELECT", "0:DAKY, 1:RTS, 2:DTR", ""),
    "072": ("Mode:DATA PORT SELECT", "0:DATA, 1:USB", ""),
    "073": ("Mode:DATA DATA OUT LEVEL", "0-100", ""),
    "074": ("Mode:FM FM MIC SEL", "0:MIC, 1:REAR", ""),
    "075": ("FM OUT LEVEL", "0-100", ""),
    "076": ("FM PKT PTT SELECT", "0:DAKY, 1:RTS, 2:DTR", ""),
    "077": ("FM PORT SELECT", "0:DATA, 1:USB", ""),
    "078": ("FM PKT TX GAIN", "0-100", ""),
    "079": ("FM PKT MODE", "0:1200, 1:9600", ""),
    "080": ("Mode:FM RPT SHIFT(28MHz)", "0-1000", ""),
    "081": ("Mode:FM RPT SHIFT(50MHz)", "0-4000", ""),
    "082": ("Mode:FM RPT SHIFT(144MHz)", "0-4000", ""),
    "083": ("Mode:FM RPT SHIFT(430MHz)", "0-10000", ""),
    "084": ("ARS 144MHz", "0:OFF, 1:ON", ""),
    "085": ("ARS 430MHz", "0:OFF, 1:ON", ""),
    "086": ("DCS POLARITY", "0:Tn-Rn, 1:Tn-Riv, 2:Tiv-Rn, 3:Tiv-Riv", ""),
    "087": ("Please set this at the radio", "0:6dB/oct, 1:18dB/oct", ""),
    "088": ("GM DISPLAY", "0:DISTANCE, 1:STRENGTH", ""),
    "089": ("DISTANCE", "0:KM, 1:MILE", ""),
    "090": ("AMS TX MODE", "0:AUTO, 1:MANUAL, 2:DN, 3:VW, 4:ANALOG", ""),
    "091": ("STANDBY BEEP", "0:OFF, 1:ON", ""),
    "092": ("Mode:RTTY LCUT FREQ", "0:OFF, 1:100Hz - 19:1000 50Hz STEPS", ""),
    "093": ("Mode:RTTY LCUT SLOPE", "0:6dB/oct, 1:18dB/oct", ""),
    "094": ("Mode:RTTY HCUT FREQ", "0:OFF, 1:700Hz - 67:4000Hz", ""),
    "095": ("Mode:RTTY HCUT SLOPE", "0:6dB/oct, 1:18dB/oct", ""),
    "096": ("RTTY SHIFT PORT", "0:SHIFT, 1:DTR, 2:RTS", ""),
    "097": ("Mode:RTTY POLARITY-R", "0:NOR, 1:REV", ""),
    "098": ("Mode:RTTY POLARITY-T", "0:NOR, 1:REV", ""),
    "099": ("Mode:RTTY OUT LEVEL", "0-100", ""),
    "100": ("Mode:RTTY RTTY SHIFT", "0:170, 1:200, 2:425, 3:850", ""),
    "101": ("Mode:RTTY MARK FREQ", "0:1275Hz, 1:2125Hz", ""),
    "102": ("Mode:SSB LCUT FREQ", "0:OFF, 1:100Hz - 19:1000Hz (50Hz steps)", ""),
    "103": ("Mode:SSB LCUT SLOPE", "0:6dB/oct, 1:18dB/oct", ""),
    "104": ("Mode:SSB HCUT FREQ", "0:OFF, 1:700Hz - 67:4000Hz (50Hz steps)", ""),
    "105": ("Mode:SSB HCUT SLOPE", "0:6dB/oct, 1:18dB/oct", ""),
    "106": ("Mode:SSB MIC SELECT", "0:MIC, 1:REAR", ""),
    "107": ("Mode:SSB OUT LEVEL", "0-100", ""),
    "108": ("Mode:SSB PTT SELECT", "0:DAKY, 1:RTS, 2:DTR", ""),
    "109": ("Mode:SSB PORT SELECT", "0:DATA, 1:USB", ""),
    "110": ("Mode:SSB TX BPF", "0:50-3000, 1:100-2900, 2:200-2800, 3:300-2700, 4:400-2600", ""),
    "111": ("APF WIDTH", "0:NARROW, 1:MEDIUM, 2:WIDE", ""),
    "112": ("CONTOUR LEVEL", "-40 to +20", ""),
    "113": ("CONTOUR WIDTH", "1-11", ""),
    "114": ("IF NOTCH WIDTH", "0:NARROW, 1:WIDE", ""),
    "115": ("SCOPE DISPLAY MODE", "0:SPECTRUM, 1:WATERFALL", ""),
    "116": ("SCOPE SPAN FREQ", "3:50kHz, 4:100kHz, 5:200kHz, 6:500kHz, 7:1000kHz", ""),
    "117": ("SPECTRUM COLOR", "0:BLUE, 1:GRAY, 2:GREEN, 3:ORANGE, 4:PURPLE, 5:RED, 6:SKY BLUE", ""),
    "118": ("WATERFALL COLOR", "0:BLUE, 1:GRAY, 2:GREEN, 3:ORANGE, 4:PURPLE, 5:RED, 6:SKY BLUE, 7:MULTI", ""),
    "119": ("PRMTRC EQ1 FREQ", "0:OFF, 1:100Hz, 2:200Hz, 3:300Hz, 4:400Hz, 5:500Hz, 6:600Hz, 7:700Hz", ""),
    "120": ("PRMTRC EQ1 LEVEL", "-20 to +10", ""),
    "121": ("PRMTRC EQ1 BWTH", "1-10", ""),
    "122": ("PRMTRC EQ2 FREQ", "0:OFF, 1:700Hz, 2:800Hz, 3:900Hz, 4:1000Hz, 5:1100Hz, 6:1200Hz, 7:1300Hz, 8:1400Hz, 9:1500Hz", ""),
    "123": ("PRMTRC EQ2 LEVEL", "-20 to +10", ""),
    "124": ("PRMTRC EQ2 BWTH", "1-10", ""),
    "125": ("PRMTRC EQ3 FREQ", "0:OFF, 1:1500Hz, 2:1600Hz, 3:1700Hz, 4:1800Hz, 5:1900Hz, 6:2000Hz-18:3200Hz", ""),
    "126": ("PRMTRC EQ3 LEVEL", "-20 to +10", ""),
    "127": ("PRMTRC EQ3 BWTH", "1-10", ""),
    "128": ("P-PRMTRC EQ1 FREQ", "0:OFF, 1:100Hz, 2:200Hz, 3:300Hz, 4:400Hz, 5:500Hz, 6:600Hz, 7:700Hz", ""),
    "129": ("P-PRMTRC EQ1 LEVEL", "-20 to +10", ""),
    "130": ("P-PRMTRC EQ1 BWTH", "1-10", ""),
    "131": ("P-PRMTRC EQ2 FREQ", "0:OFF, 1:700Hz, 2:800Hz, 3:900Hz, 4:1000Hz, 5:1100Hz, 6:1200Hz, 7:1300Hz, 8:1400Hz, 9:1500Hz", ""),
    "132": ("P-PRMTRC EQ2 LEVEL", "-20 to +10", ""),
    "133": ("P-PRMTRC EQ2 BWTH", "1-10", ""),
    "134": ("P-PRMTRC EQ3 FREQ", "0:OFF, 1:1500Hz, 2:1600Hz, 3:1700Hz, 4:1800Hz, 5:1900Hz, 6:2000Hz-18:3200Hz", ""),
    "135": ("P-PRMTRC EQ3 LEVEL", "-20 to +10", ""),
    "136": ("P-PRMTRC EQ3 BWTH", "1-10", ""),
    "137": ("HF TX MAX POWER", "5-100", "W"),
    "138": ("50M TX MAX POWER", "5-100", "W"),
    "139": ("144M TX MAX POWER", "5-50", "W"),
    "140": ("430M TX MAX POWER", "5-50", "W"),
    "141": ("TUNER SELECT", "0:OFF, 1:INTERNAL, 2:EXTERNAL, 3:ATAS, 4:LAMP", ""),
    "142": ("VOX SELECT", "0:MIC, 1:DATA", ""),
    "143": ("VOX GAIN", "0-100", ""),
    "144": ("VOX DELAY", "30-3000", "ms"),
    "145": ("ANTI VOX GAIN", "0-100", ""),
    "146": ("DATA VOX GAIN", "0-100", ""),
    "147": ("DATA VOX DELAY", "30-3000", "ms"),
    "148": ("ANTI DVOX GAIN", "0-100", ""),
    "149": ("EMERGENCY FREQ TX", "0:DISABLE, 1:ENABLE", ""),
    "150": ("PRT/WIRES FREQ", "0:MANUAL, 1:PRESET", ""),
    "151": ("PRESET FREQUENCY", "3000000-47000000", "Hz"),
    "152": ("SEARCH SETUP", "0:HISTORY, 1:ACTIVITY", ""),
    "153": ("WIRES DG-ID", "0:AUTO, 1-99:DG-ID", "")
}


class LEDIndicator(QFrame):
    def __init__(self, diameter=16, color_on="#FF4D4D", color_off="#30343A",
                 border="#8A8F99", label_text="TX"):
        super().__init__()
        self._diam = diameter
        self._on = False
        self._color_on = color_on
        self._color_off = color_off
        self._border = border

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.dot = QFrame(self)
        self.dot.setFixedSize(self._diam, self._diam)
        self.dot.setObjectName("txDot")
        lay.addWidget(self.dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel(label_text, self)
        self._label.setStyleSheet("color:#BEEAFF; font:600 12px 'Segoe UI'; letter-spacing:1px;")
        lay.addWidget(self._label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.glow = QGraphicsDropShadowEffect(self.dot)
        self.glow.setOffset(0, 0)
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor("#FF4D4D"))
        self.dot.setGraphicsEffect(self.glow)

        self._apply()

    def set_on(self, is_on: bool):
        if self._on != is_on:
            self._on = is_on
            self._apply()

    def _apply(self):
        base = self._color_on if self._on else self._color_off
        self.dot.setStyleSheet(
            f"QFrame#txDot {{"
            f"  background:{base};"
            f"  border:2px solid {self._border};"
            f"  border-radius:{self._diam // 2}px;"
            f"}}"
        )
        self.glow.setBlurRadius(18 if self._on else 0)


class FrequencyDisplayLabel(QLabel):
    def __init__(self, controller, parent_widget, adjust_callback):
        super().__init__(parent_widget)
        self.controller = controller
        self.adjust_callback = adjust_callback
        self.active_digit_index = None

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.digit_zones = [
            (62, 91, 0),
            (92, 119, 1),
            (120, 152, 2),
            (180, 211, 3),
            (212, 240, 4),
            (241, 273, 5),
            (301, 331, 6),
            (332, 361, 7),
            (362, 393, 8),
        ]

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        pos_x = event.position().x()
        prev = self.active_digit_index
        self.active_digit_index = None

        for x_start, x_end, index in self.digit_zones:
            if x_start <= pos_x <= x_end:
                self.active_digit_index = index
                print(f"[DEBUG] Digit at CAT index {index} selected.")
                break

        if self.active_digit_index is None:
            print("[DEBUG] No digit selected.")
        else:
            self.setFocus()

        if self.active_digit_index != prev:
            self.update()

    def wheelEvent(self, event):
        if self.active_digit_index is None:
            print("[DEBUG] No digit selected. Click first.")
            return

        if not self.controller.serial_conn or not self.controller.serial_conn.is_open:
            print("[ERROR] Serial connection not open.")
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        direction = 1 if delta > 0 else -1

        try:
            ser = self.controller.serial_conn
            ok = self.controller._ensure_vfo()
            if not ok:
                ser.reset_input_buffer()
                ser.write(b"VM0;")
                time.sleep(0.20)
                self.controller._ensure_vfo()

            self.controller._poll_inhibit_until = time.time() + 0.35

            hz = self.controller._read_fa_hz()
            if hz is None:
                print("[ERROR] Invalid FA response.")
                return

            s11 = f"{hz:011d}"
            head2, tail9 = s11[:2], s11[2:]

            if not (0 <= self.active_digit_index < len(tail9)):
                print("[ERROR] Digit index out of range.")
                return

            new_tail9 = self.adjust_specific_digit(tail9, self.active_digit_index, direction)
            new11 = head2 + new_tail9
            new_hz = int(new11)

            new_hz = self.controller._clip_rig_range(new_hz)
            cmd = f"FA{new_hz:011d};"
            ser.write(cmd.encode('ascii'))
            print(f"[DEBUG] Updated freq to: {cmd}")

            time.sleep(0.12)
            ser.reset_input_buffer()
            ser.write(b'FA;')
            fa = self.controller.read_until_semicolon()
            if fa.startswith('FA') and fa.endswith(';'):
                digits = ''.join(ch for ch in fa[2:-1] if ch.isdigit())
                if digits:
                    new_hz = int(digits[-11:].rjust(11, '0'))

            self.controller.freq_display.setText(self.controller._format_hz_for_display(new_hz))
            event.accept()

        except Exception as e:
            print(f"[ERROR] Failed during wheelEvent: {e}")

    @staticmethod
    def adjust_specific_digit(freq_str, digit_index, direction):
        if not (0 <= digit_index < len(freq_str)):
            return freq_str
        freq_list = list(freq_str)
        d = int(freq_list[digit_index])
        d = (d + direction) % 10
        freq_list[digit_index] = str(d)
        return ''.join(freq_list)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.active_digit_index is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 255, 255, 80))

            for x_start, x_end, index in self.digit_zones:
                if index == self.active_digit_index:
                    painter.drawRect(x_start, 0, x_end - x_start, self.height())
                    break


class RetroBarMeter(QWidget):
    def __init__(self, label, scale_points):
        super().__init__()
        self.label = str(label)
        self.scale_points = [(max(0, min(100, int(pos))), str(txt)) for pos, txt in scale_points]

        self.current_value = 50.0
        self.target_value = 50.0
        self.smoothing = 0.2
        self.snap_threshold = 0.5

        self.setFixedSize(500, 70)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_bar)
        self.timer.start(50)

    def set_value(self, val):
        try:
            v = float(val)
        except (TypeError, ValueError):
            return
        self.target_value = max(0.0, min(100.0, v))

    def animate_bar(self):
        diff = self.target_value - self.current_value
        if abs(diff) > self.snap_threshold:
            self.current_value += diff * self.smoothing
        else:
            self.current_value = self.target_value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        margin = 10
        bar_top = 10
        bar_height = 15
        bar_width = max(0, self.width() - 2 * margin)

        painter.setPen(QPen(QColor(0, 150, 255), 2))
        painter.drawRect(margin, bar_top, bar_width, bar_height)

        fill_width = int(round(bar_width * max(0.0, min(100.0, self.current_value)) / 100.0))
        if fill_width > 0:
            painter.fillRect(
                margin + 1, bar_top + 1,
                max(0, fill_width - 1), bar_height - 2,
                QColor(0, 255, 255)
            )

        painter.setPen(QPen(QColor(0, 150, 255), 1))
        painter.setFont(QFont("Arial", 8))
        baseline_y = bar_top + bar_height + 20
        for pos, label in self.scale_points:
            x = margin + int(bar_width * pos / 100)
            painter.drawLine(x, bar_top + bar_height + 2, x, bar_top + bar_height + 7)
            painter.drawText(x - 10, baseline_y, label)


class FT991AController(QWidget):
    RIG_MIN_HZ = 3_000_000
    RIG_MAX_HZ = 470_000_000

    BAUD = 38400
    SERIAL_TIMEOUT = 0.6
    SERIAL_WRITE_TIMEOUT = 0.6

    FREQ_POLL_MS = 500
    METER_POLL_MS = 200

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FT-991A Preset Control Panel")
        self.setFixedSize(1200, 1200)

        self.serial_conn = None
        self._poll_inhibit_until = 0.0
        self._cat_busy = False

        self.meter_timer = None
        self.freq_timer = None
        self._cat_lock = threading.RLock()
        self._cat_busy = False

        self.is_transmitting = False
        self.poll_counter = 0
        self.current_memory = 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar {
                background-color: transparent;
            }
            QTabBar::tab {
                background: #3a0ca3;
                color: white !important;
                padding: 6px 25px;
                min-width: 100px;
                font-weight: bold;
                font-size: 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #7209b7;
                color: white !important;
            }
            QTabBar::tab:hover {
                background: #560bad;
                color: white !important;
            }
        """)

        self.main_tab = QWidget()
        self.cat_tab = QWidget()
        self.tabs.addTab(self.main_tab, "Menu Reader")
        self.tabs.addTab(self.cat_tab, "CAT Terminal")

        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(33, 66, 109))
        gradient.setColorAt(1.0, QColor(0, 0, 0))
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        self.com_label = QLabel("Select Port:", self.main_tab)
        self.com_label.setGeometry(20, 26, 150, 30)
        self.com_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        self.com_label2 = QLabel("SIMPLEX FREQ DIRECT", self.main_tab)
        self.com_label2.setGeometry(200, 100, 150, 30)
        self.com_label2.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.com_label3 = QLabel("use with varafm", self.main_tab)
        self.com_label3.setGeometry(245, 230, 100, 30)
        self.com_label3.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 10px;
            }
        """)

        self.com_selector = QComboBox(self.main_tab)
        self.com_selector.setGeometry(130, 30, 150, 22)

        ports = [port.device for port in serial.tools.list_ports.comports()]
        print("[DEBUG] Available serial ports:", ports)

        if ports:
            self.com_selector.addItems(ports)
            # Prefer the FT-991A USB ports if present
            for preferred in ("/dev/ttyUSB0", "/dev/ttyUSB1"):
                if preferred in ports:
                    self.com_selector.setCurrentText(preferred)
                    break
        else:
            self.com_selector.addItem("No serial ports found")



        self.connect_btn = QPushButton("Connect", self.main_tab)
        self.connect_btn.setGeometry(310, 26, 120, 30)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #80ff80;
                color: black;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #70e070;
            }
            QPushButton:pressed {
                background-color: #60c060;
            }
        """)
        self.connect_btn.clicked.connect(self.connect_to_radio)

        self.disconnect_btn = QPushButton("Disconnect", self.main_tab)
        self.disconnect_btn.setGeometry(440, 26, 120, 30)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8080;
                color: black;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #e07070;
            }
            QPushButton:pressed {
                background-color: #c06060;
            }
        """)
        self.disconnect_btn.clicked.connect(self.disconnect_from_radio)

        self.main_tab.setGeometry(0, 0, 1200, 768)

        s_meter_scale = [
            (0, "1"), (10, "3"), (20, "5"), (30, "7"), (40, "9"),
            (55, "+10"), (70, "+20"), (85, "+30"), (100, "+60")
        ]
        self.s_meter = RetroBarMeter("S-METER", s_meter_scale)
        self.s_meter.setParent(self.main_tab)
        self.s_meter.setGeometry(650, 5, 500, 28)

        self.s_meter_label = QLabel("S-METER", self.main_tab)
        self.s_meter_label.setGeometry(650, 50, 500, 20)
        self.s_meter_label.setStyleSheet("color: cyan; font-weight: bold;")
        self.s_meter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pwr_meter_scale = [
            (0, "0"), (17, "25"), (33, "50"), (50, "75"),
            (67, "100"), (83, "125"), (100, "150")
        ]
        self.pwr_meter = RetroBarMeter("PWR METER", pwr_meter_scale)
        self.pwr_meter.setParent(self.main_tab)
        self.pwr_meter.setGeometry(650, 80, 500, 30)

        self.pwr_meter_label = QLabel("PWR METER", self.main_tab)
        self.pwr_meter_label.setGeometry(650, 123, 500, 20)
        self.pwr_meter_label.setStyleSheet("color: cyan; font-weight: bold;")
        self.pwr_meter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tx_led = LEDIndicator(diameter=14, label_text="TX")
        self.tx_led.setParent(self.main_tab)
        self.tx_led.setGeometry(600, 32, 60, 18)

        self.is_transmitting = False
        self.start_meter_polling()
        self.tx_timer = QTimer(self)
        self.tx_timer.setInterval(250)
        self.tx_timer.timeout.connect(self._poll_tx_status)
        self.tx_timer.start()

        btn_style = """
            QPushButton {
                background-color: #4cc9f0;
                color: black;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover { background-color: #3ab8df; }
            QPushButton:pressed { background-color: #3ab8df; }
        """

        self.btn_mem_059 = QPushButton("144.420 M059", self.main_tab)
        self.btn_mem_059.setGeometry(10, 70, 130, 30)
        self.btn_mem_059.setStyleSheet(btn_style)
        self.btn_mem_059.clicked.connect(lambda: self.recall_memory_channel("059"))

        self.btn_mem_060 = QPushButton("446.000 M060", self.main_tab)
        self.btn_mem_060.setGeometry(150, 70, 120, 30)
        self.btn_mem_060.setStyleSheet(btn_style)
        self.btn_mem_060.clicked.connect(lambda: self.recall_memory_channel("060"))

        self.btn_mem_061 = QPushButton("145.600 M061", self.main_tab)
        self.btn_mem_061.setGeometry(280, 70, 120, 30)
        self.btn_mem_061.setStyleSheet(btn_style)
        self.btn_mem_061.clicked.connect(lambda: self.recall_memory_channel("061"))

        self.btn_mem_062 = QPushButton("433.500 M062", self.main_tab)
        self.btn_mem_062.setGeometry(410, 70, 120, 30)
        self.btn_mem_062.setStyleSheet(btn_style)
        self.btn_mem_062.clicked.connect(lambda: self.recall_memory_channel("062"))

        self.btn_mem_darn3 = QPushButton("DARN 3", self.main_tab)
        self.btn_mem_darn3.setGeometry(20, 140, 120, 30)
        self.btn_mem_darn3.setStyleSheet(btn_style)
        self.btn_mem_darn3.clicked.connect(lambda: self.recall_memory_channel("004"))

        self.btn_mem_darn2 = QPushButton("DARN 2", self.main_tab)
        self.btn_mem_darn2.setGeometry(150, 140, 120, 30)
        self.btn_mem_darn2.setStyleSheet(btn_style)
        self.btn_mem_darn2.clicked.connect(lambda: self.recall_memory_channel("003"))

        self.preset_btn_default = QPushButton("Default", self.main_tab)
        self.preset_btn_default.setGeometry(20, 955, 100, 30)
        self.preset_btn_default.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_default.clicked.connect(
            partial(self.activate_default_memory, "defaultv002.xml")
        )

        self.preset_btn_ft8 = QPushButton("FT8", self.main_tab)
        self.preset_btn_ft8.setGeometry(130, 255, 100, 30)
        self.preset_btn_ft8.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_ft8.clicked.connect(
            partial(self.activate_ft8_memory, "FT8settings.xml")
        )

        self.preset_btn_winlink = QPushButton("Winlink", self.main_tab)
        self.preset_btn_winlink.setGeometry(240, 255, 100, 30)
        self.preset_btn_winlink.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_winlink.clicked.connect(
            partial(self.activate_winlink_memory, "WINLINK_APRS.xml")
        )

        self.preset_btn_aprs = QPushButton("APRS-pinpoint", self.main_tab)
        self.preset_btn_aprs.setGeometry(350, 255, 100, 30)
        self.preset_btn_aprs.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_aprs.clicked.connect(
            partial(self.activate_aprs_memory, "aprs.xml")
        )

        self.preset_btn_ssb = QPushButton("SSB", self.main_tab)
        self.preset_btn_ssb.setGeometry(460, 255, 100, 30)
        self.preset_btn_ssb.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_ssb.clicked.connect(
            partial(self.activate_ssb_memory, "SSB_setting.xml")
        )

        self.preset_btn_wiresx = QPushButton("WIRES-X", self.main_tab)
        self.preset_btn_wiresx.setGeometry(570, 255, 100, 30)
        self.preset_btn_wiresx.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_wiresx.clicked.connect(
            partial(self.activate_wiresx_memory, "WIRESX.xml")
        )

        self.preset_btn_default2 = QPushButton("Mic simplex", self.main_tab)
        self.preset_btn_default2.setGeometry(20, 220, 100, 30)
        self.preset_btn_default2.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_default2.clicked.connect(
            partial(self.activate_default2_memory, "overrides_only.xml")
        )

        self.preset_btn_mic_default_d3 = QPushButton("Mic darn3", self.main_tab)
        self.preset_btn_mic_default_d3.setGeometry(20, 255, 100, 30)
        self.preset_btn_mic_default_d3.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_mic_default_d3.clicked.connect(
            partial(self.activate_mic_default_d3, "overrides_only.xml")
        )

        self.save_btn = QPushButton("📥 Download From Radio to File", self.main_tab)
        self.save_btn.setGeometry(20, 305, 250, 30)
        self.save_btn.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.save_btn.clicked.connect(self.load_all_menus)

        self.load_btn = QPushButton("📤 Load From File to Radio", self.main_tab)
        self.load_btn.setGeometry(280, 305, 250, 30)
        self.load_btn.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.load_btn.clicked.connect(self.select_and_load_file)

        self.preset_btn_aprs_m059 = QPushButton("APRS simplex", self.main_tab)
        self.preset_btn_aprs_m059.setGeometry(350, 220, 100, 30)
        self.preset_btn_aprs_m059.setStyleSheet("background-color: #3a0ca3; color: white; font-weight: bold;")
        self.preset_btn_aprs_m059.clicked.connect(
            partial(self.activate_aprs_simplex59, "aprs.xml")
        )

        self.text_display = QTextEdit(self.main_tab)
        self.text_display.setGeometry(20, 350, 640, 200)
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet(
            "background-color: #0f0f3d; color: white; "
            "font-family: Consolas; font-size: 11px;"
        )

        self.status_label = QLabel("READY", self.main_tab)
        self.status_label.setGeometry(20, 550, 400, 30)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        self.progress_bar = QProgressBar(self.main_tab)
        self.progress_bar.setGeometry(20, 580, 1160, 25)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: rgb(165,97,201);
                width: 10px;
            }
        """)

        self.freq_display = FrequencyDisplayLabel(self, self.main_tab, self.adjust_frequency)
        self.freq_display.setGeometry(700, 210, 450, 140)
        freq_font = QFont("Digital-7 Mono", 48, QFont.Weight.Bold)
        self.freq_display.setFont(freq_font)
        self.freq_display.setStyleSheet("""
            color: cyan;
            background-color: transparent;
            border: 2px solid cyan;
        """)
        self.freq_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mem_plus_btn = QPushButton("+", self.main_tab)
        self.mem_plus_btn.setGeometry(700, 400, 40, 60)
        self.mem_plus_btn.setStyleSheet(
            "background-color: #4cc9f0; font-weight: bold; font-size: 20px;"
        )
        self.mem_plus_btn.clicked.connect(lambda: self.change_memory_channel(1))

        self.mem_minus_btn = QPushButton("-", self.main_tab)
        self.mem_minus_btn.setGeometry(700, 480, 40, 60)
        self.mem_minus_btn.setStyleSheet(
            "background-color: #4cc9f0; font-weight: bold; font-size: 20px;"
        )
        self.mem_minus_btn.clicked.connect(lambda: self.change_memory_channel(-1))

        self.freq_timer = QTimer(self)
        self.freq_timer.timeout.connect(self.update_frequency_display)
        self.freq_timer.start(500)

        self.ssb_sliders = {}
        self.ssb_toggles = {}

        ssb_filter_group = QGroupBox("SSB Filters", self.main_tab)
        ssb_filter_group.setGeometry(20, 620, 1160, 300)
        ssb_filter_group.setStyleSheet(
            "QGroupBox { color: white; font-weight: bold; font-size: 14px; "
            "border: 1px solid #80ff80; margin-top: 10px; } "
            "QGroupBox:title { subcontrol-origin: margin; subcontrol-position: top left; "
            "padding: 0 3px; }"
        )

        grid = QGridLayout()
        grid.setVerticalSpacing(20)

        def make_slider_row(label, min_, max_, default, tooltip=None,
                            show_toggle=False, unit=""):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(20)

            toggle = None
            if show_toggle:
                toggle = QCheckBox("ON")
                toggle.setChecked(True)
                toggle.setStyleSheet("color: lightgreen")
                self.ssb_toggles[label] = toggle

            lbl = QLabel(label)
            lbl.setStyleSheet("color: white")
            if tooltip:
                lbl.setToolTip(tooltip)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(min_ // 10)
            slider.setMaximum(max_ // 10)
            slider.setValue(default // 10)
            slider.setFixedWidth(800)
            self.ssb_sliders[label] = slider

            value_lbl = QLabel(str(default))
            value_lbl.setStyleSheet("color: white; min-width: 40px")

            unit_lbl = QLabel(unit)
            unit_lbl.setStyleSheet("color: white")

            def update_display_and_send(val):
                freq = val * 10
                value_lbl.setText(str(freq))
                if label == "Contour Freq HZ":
                    if self.ssb_toggles[label].isChecked():
                        self.cat_input.setText(f"CO01{freq:04d};")
                        self.send_cat_command()
                    else:
                        self.cat_input.setText("CO000000;")
                        self.send_cat_command()

            if show_toggle and label == "Contour Freq HZ":
                toggle.stateChanged.connect(
                    lambda _: update_display_and_send(slider.value())
                )
                toggle.stateChanged.connect(
                    lambda state: self.cat_input.setText(
                        "CO000001;" if state == Qt.CheckState.Checked else "CO000000;"
                    )
                )
                toggle.stateChanged.connect(lambda _: self.send_cat_command())

            slider.valueChanged.connect(update_display_and_send)

            row_layout.addWidget(lbl)
            if toggle:
                row_layout.addWidget(toggle)
            row_layout.addWidget(slider)
            row_layout.addWidget(value_lbl)
            row_layout.addWidget(unit_lbl)

            return row_widget

        contour_row = make_slider_row(
            "Contour Freq HZ", 10, 3200, 300,
            "Menu: CO (Contour)", show_toggle=True
        )
        grid.addWidget(contour_row, 0, 0, 1, 3)

        contour_width_row = make_slider_row(
            "Contour Width", 10, 110, 50, "Menu: EX113", show_toggle=False
        )
        contour_width_row.findChildren(QSlider)[0].setFixedWidth(800)
        grid.addWidget(contour_width_row, 1, 0, 1, 3)

        contour_level_row = make_slider_row(
            "Contour Level", -400, 200, 0, "Menu: EX112", show_toggle=False, unit="dB"
        )
        contour_level_row.findChildren(QSlider)[0].setFixedWidth(800)
        grid.addWidget(contour_level_row, 2, 0, 1, 3)

        width_row = make_slider_row("Width", 0, 4, 2, "Menu: EX110", unit="")
        shift_row = make_slider_row("Shift", -1200, 1200, 0, "Menu: IS", unit="Hz")
        nb_row = make_slider_row("NB Width", 0, 10, 2, "Menu: NB/NL", show_toggle=True)
        dnr_row = make_slider_row("DNR Level", 1, 15, 5, "Menu: NR/RL", show_toggle=True)
        notch_row = make_slider_row("Notch Width", 0, 3200, 1500, "Menu: BP",
                                    show_toggle=True, unit="Hz")
        apf_row = make_slider_row("APF Width", 0, 2, 1, "Menu: CO (APF)",
                                  show_toggle=True)

        grid.addWidget(width_row, 3, 0, 1, 3)
        grid.addWidget(shift_row, 4, 0, 1, 3)
        grid.addWidget(nb_row, 5, 0, 1, 3)
        grid.addWidget(dnr_row, 6, 0, 1, 3)
        grid.addWidget(notch_row, 7, 0, 1, 3)
        grid.addWidget(apf_row, 8, 0, 1, 3)

        ssb_filter_group.setLayout(grid)

        cat_layout = QVBoxLayout()
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("Enter CAT command (e.g., FA;)")
        cat_layout.addWidget(self.cat_input)

        self.cat_send_btn = QPushButton("Send CAT Command")
        self.cat_send_btn.clicked.connect(self.send_cat_command)
        cat_layout.addWidget(self.cat_send_btn)

        self.cat_response_display = QTextEdit()
        self.cat_response_display.setReadOnly(True)
        self.cat_response_display.setStyleSheet(
            "background-color: #1e1e1e; color: #90ee90; font-family: Consolas;"
        )
        cat_layout.addWidget(self.cat_response_display)
        self.cat_tab.setLayout(cat_layout)

    def _ensure_vfo(self, attempts: int = 4, check_delay: float = 0.16) -> bool:
        if not (self.serial_conn and self.serial_conn.is_open):
            return False

        ser = self.serial_conn

        def mc_is_vfo(s: str) -> bool:
            return s.startswith("MC") and len(s) >= 5 and s[2:5].isdigit() and s[2:5] == "000"

        for i in range(attempts):
            try:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                ser.write(b"MC;")
                resp = self.read_until_semicolon()
                if resp:
                    self.cat_response_display.append(f">> MC;\n<< {resp}")
                if mc_is_vfo(resp):
                    return True

                ser.reset_input_buffer()
                ser.write(b"VM0;")
                try:
                    ser.write(b"MT0;")
                except Exception:
                    pass

                time.sleep(check_delay + 0.06 * i)
                ser.reset_input_buffer()
                ser.write(b"MC;")
                resp2 = self.read_until_semicolon()
                if resp2:
                    self.cat_response_display.append(f">> MC;\n<< {resp2}")
                if mc_is_vfo(resp2):
                    return True

            except Exception as e:
                self.cat_response_display.append(f"[ensure_vfo error] {e}")

        return False

    def start_meter_polling(self, interval_ms: int = 200):
        t = getattr(self, "meter_timer", None)
        if t is None:
            self.meter_timer = QTimer(self)
            self.meter_timer.setTimerType(Qt.TimerType.CoarseTimer)
            self.meter_timer.timeout.connect(self.update_meters)
            self._meter_toggle = False

        self.meter_timer.stop()
        self.meter_timer.start(interval_ms)
        QTimer.singleShot(0, self.update_meters)

    def update_meters(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            return
        if hasattr(self, "_poll_inhibit_until") and time.time() < getattr(self, "_poll_inhibit_until"):
            return

        try:
            self._meter_toggle = not getattr(self, "_meter_toggle", False)

            if self._meter_toggle:
                self.serial_conn.reset_input_buffer()
                self.serial_conn.write(b'RM5;')
                resp = self.read_until_semicolon()
                if resp.startswith('RM5') and len(resp) >= 6 and resp[3:6].isdigit():
                    raw = int(resp[3:6])
                    val = max(0, min(100, int(round(raw * 100 / 255))))
                    self.pwr_meter.set_value(val)
            else:
                self.serial_conn.reset_input_buffer()
                self.serial_conn.write(b'RM1;')
                resp = self.read_until_semicolon()
                if resp.startswith('RM1') and len(resp) >= 6 and resp[3:6].isdigit():
                    raw = int(resp[3:6])
                    val = max(0, min(100, int(round(raw * 100 / 255))))
                    self.s_meter.set_value(val)

        except Exception as e:
            print(f"[ERROR] Meter update failed: {e}")

    def stop_meter_polling(self):
        t = getattr(self, "meter_timer", None)
        if t and t.isActive():
            t.stop()

    def recall_memory_channel(self, channel) -> bool:
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return False

        try:
            ch_int = int(str(channel).strip())
        except Exception:
            QMessageBox.warning(self, "Warning", f"Invalid memory '{channel}'.")
            return False
        if not (1 <= ch_int <= 124):
            QMessageBox.warning(self, "Warning", f"Memory {ch_int:03d} out of range.")
            return False
        ch = f"{ch_int:03d}"

        try:
            ser = self.serial_conn
            ser.reset_input_buffer()
            ser.write(b'VM1;')
            time.sleep(0.12)

            self._poll_inhibit_until = time.time() + 0.4

            ser.reset_input_buffer()
            ser.write(f'MC{ch};'.encode('ascii'))
            self.cat_response_display.append(f">> MC{ch};")
            time.sleep(0.15)

            ser.reset_input_buffer()
            ser.write(b'MC;')
            resp = self.read_until_semicolon()
            self.cat_response_display.append(f">> MC;\n<< {resp}")

            actual = ch
            ok = False
            if resp.startswith('MC') and len(resp) >= 5 and resp[2:5].isdigit():
                actual = resp[2:5]
                ok = (actual == ch)

            tag = None
            try:
                tag = self.read_memory_tag(int(actual))
            except Exception:
                pass

            nice = f"Memory {actual}" + (f" — {tag}" if tag else "")
            self.text_display.append(f"🔁 Recalled {nice}")
            self.status_label.setText(f"{nice} Active")

            QTimer.singleShot(350, self.update_frequency_display)
            return ok
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to recall memory channel {ch}:\n{e}")
            return False

    def read_until_semicolon(self):
        response = b""
        timeout = time.time() + 0.5
        while time.time() < timeout:
            part = self.serial_conn.read(1)
            if part:
                response += part
                if part == b';':
                    break
        return response.decode('ascii', errors='ignore').strip()

    def _clip_rig_range(self, hz):
        try:
            hz = int(hz)
        except Exception:
            return None
        return max(self.RIG_MIN_HZ, min(self.RIG_MAX_HZ, hz))

    def _format_hz_for_display(self, hz):
        if hz is None:
            return "---.---.---"
        mhz = hz // 1_000_000
        khz = (hz // 1_000) % 1000
        rhz = hz % 1000
        return f"{mhz}.{khz:03d}.{rhz:03d}"

    def _read_fa_hz(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            return None
        try:
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(b"FA;")
            resp = self.read_until_semicolon()
            if not (resp.startswith("FA") and resp.endswith(";")):
                return None
            digits = "".join(ch for ch in resp[2:-1] if ch.isdigit())
            if not digits:
                return None
            hz = int(digits[-11:].rjust(11, "0"))
            return self._clip_rig_range(hz)
        except Exception:
            return None

    def update_frequency_display(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            return
        try:
            if getattr(self, "_poll_inhibit_until", 0) > time.time():
                return

            hz = self._read_fa_hz()
            if hz is None:
                return

            if getattr(self, "_last_fa_hz", None) != hz:
                self._last_fa_hz = hz
                self.freq_display.setText(self._format_hz_for_display(hz))

        except Exception as e:
            print(f"[ERROR] Frequency read failed: {e}")

    def adjust_frequency(self, step_hz):
        if not (self.serial_conn and self.serial_conn.is_open):
            return
        try:
            self._ensure_vfo()

            step = int(step_hz)
            cur = self._read_fa_hz()
            if cur is None:
                return

            new_hz = self._clip_rig_range(cur + step)
            if new_hz == cur:
                return

            self._poll_inhibit_until = time.time() + 0.35

            self.serial_conn.write(f"FA{new_hz:011d};".encode("ascii"))
            time.sleep(0.12)
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(b"FA;")
            fa = self.read_until_semicolon()
            if fa.startswith("FA") and fa.endswith(";"):
                digits = "".join(ch for ch in fa[2:-1] if ch.isdigit())
                if digits:
                    new_hz = int(digits[-11:].rjust(11, "0"))

            self._last_fa_hz = new_hz
            self.freq_display.setText(self._format_hz_for_display(new_hz))
            print(f"[DEBUG] Frequency adjusted to: FA{new_hz:011d};")

        except Exception as e:
            print(f"[ERROR] Frequency adjust failed: {e}")

    def activate_winlink_memory(self, file):
        self.text_display.clear()

        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        try:
            ser = self.serial_conn
            self._poll_inhibit_until = time.time() + 0.6

            ser.reset_input_buffer()
            self._apply_settings_from_file(file)
            time.sleep(0.25)

            ser.write(b'VM1;')
            time.sleep(0.12)
            ser.write(b'MC053;')
            time.sleep(0.30)

            ser.reset_input_buffer()
            ser.write(b"MC;")
            resp = self.read_until_semicolon()
            actual = None
            if resp.startswith("MC") and len(resp) >= 5 and resp[2:5].isdigit():
                actual = int(resp[2:5])

            tag = self.read_memory_tag(actual) if actual else None

            port = self.com_selector.currentText()
            nice = f"📡 Winlink {(f'{actual:03d}' if actual else '???')}"
            if tag:
                nice += f" — {tag}"

            self.status_label.setText(f"{nice} on {port}")
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ Winlink activated: preset applied, memory recalled\n")

            QTimer.singleShot(400, self.update_frequency_display)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate Winlink:\n{e}")

    def read_current_memory_channel(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            return None
        try:
            ser = self.serial_conn
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(b"MC;")
            resp = self.read_until_semicolon()

            try:
                self.cat_response_display.append(f">> MC;\n<< {resp}")
            except Exception:
                pass

            if not (resp.startswith("MC") and resp.endswith(";")):
                return None

            payload = resp[2:-1]
            import re
            m = re.search(r"(\d{3})", payload)
            if not m:
                return None

            ch = int(m.group(1))
            if ch == 0:
                return None

            if 1 <= ch <= 124:
                return ch
            return ch
        except Exception as e:
            try:
                self.cat_response_display.append(f"[read_current_memory_channel error] {e}")
            except Exception:
                pass
            return None

    def activate_mic_default_d3(self, file):
        self.text_display.clear()
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            ser = self.serial_conn
            self._poll_inhibit_until = time.time() + 0.7
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            self._apply_settings_from_file(file)
            self.text_display.append(f"📤 Applied stripped defaults from: {file}\n")

            ser.reset_input_buffer()
            ser.write(b'VM1;')
            _ = self.read_until_semicolon()
            time.sleep(0.12)

            ser.reset_input_buffer()
            ser.write(b'MC004;')
            _ = self.read_until_semicolon()
            time.sleep(0.25)

            ser.reset_input_buffer()
            ser.write(b"MC;")
            state = self.read_until_semicolon() or ""
            actual = 4
            if state.startswith("MC") and len(state) >= 5 and state[2:5].isdigit():
                ch = int(state[2:5])
                if ch != 0:
                    actual = ch

            tag = self.read_memory_tag(actual)
            nice = f"🎙️ Mic default D3 (MC{actual:03d}" + (f" — {tag}" if tag else "") + ")"

            self.status_label.setText(nice)
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ Mic default D3 applied: stripped defaults + DARN 3 recalled\n")

            QTimer.singleShot(350, self.update_frequency_display)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate Mic default D3:\n{e}")

    def read_memory_tag(self, channel: int):
        if not (self.serial_conn and self.serial_conn.is_open):
            return None
        try:
            ser = self.serial_conn
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(f"MT{channel:03d};".encode("ascii"))
            resp = self.read_until_semicolon()

            try:
                self.cat_response_display.append(f">> MT{channel:03d};\n<< {resp}")
            except Exception:
                pass

            if not (resp.startswith("MT") and resp.endswith(";")):
                return None

            payload = resp[2:-1]
            if len(payload) >= 3 and payload[:3].isdigit():
                payload = payload[3:]

            import string
            tag = "".join(ch for ch in payload if ch in string.printable).strip()

            if len(tag) > 12:
                tag = tag[:12].rstrip()

            if not tag or tag == "---":
                return None

            return tag

        except Exception as e:
            try:
                self.cat_response_display.append(f"[read_memory_tag error] {e}")
            except Exception:
                pass
            return None

    def read_memory_summary(self, channel: int):
        if not (self.serial_conn and self.serial_conn.is_open):
            return None
        try:
            ser = self.serial_conn
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(f"MR{channel:03d};".encode("ascii"))
            resp = self.read_until_semicolon()

            if not resp:
                return None

            try:
                self.cat_response_display.append(f">> MR{channel:03d};\n<< {resp}")
            except Exception:
                pass

            return resp
        except Exception as e:
            try:
                self.cat_response_display.append(f"[read_memory_summary error] {e}")
            except Exception:
                pass
            return None

    def fetch_current_freq_mode(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            return None, None

        freq_str = None
        hz = self._read_fa_hz()
        if isinstance(hz, int):
            freq_str = f"{self._format_hz_for_display(hz)} MHz"

        mode_map = {
            '00': 'LSB', '01': 'USB', '02': 'CW',   '03': 'CWR',
            '04': 'AM',  '05': 'FM',  '06': 'RTTY-L','07': 'RTTY-U',
            '08': 'PKT-L','09': 'PKT-U','0A': 'FM-N','0B': 'DATA-L',
            '0C': 'DATA-U','0D': 'AM-N','0E': 'FM (DN/VW?)'
        }

        mode_h = None
        try:
            ser = self.serial_conn
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(b"MD;")
            md = self.read_until_semicolon()

            try:
                self.cat_response_display.append(f">> MD;\n<< {md or '[No Response]'}")
            except Exception:
                pass

            if md and md.startswith('MD') and len(md) >= 4:
                code = md[2:4]
                mode_h = mode_map.get(code, f"Unknown (MD{code})")
        except Exception as e:
            try:
                self.cat_response_display.append(f"[fetch_current_freq_mode error] {e}")
            except Exception:
                pass

        return freq_str, mode_h

    def is_memory_filled(self, ch: int) -> bool:
        try:
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            self.serial_conn.write(f"MR{ch:03d};".encode("ascii"))
            resp = self.read_until_semicolon() or ""
            if not (resp.startswith("MR") and resp.endswith(";")):
                return False

            payload = resp[2:-1]
            if len(payload) >= 3 and payload[:3].isdigit():
                payload = payload[3:]

            import re
            m = re.search(r"(\d{6,})", payload)
            return bool(m and any(c != "0" for c in m.group(1)))
        except Exception:
            return False

    def change_memory_channel(self, step):
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        try:
            ser = self.serial_conn
            cur = self.read_current_memory_channel()
            if cur is None:
                cur = max(1, int(getattr(self, "current_memory", 1)))

            lo, hi = 1, 124
            direction = 1 if int(step) >= 0 else -1

            self._poll_inhibit_until = time.time() + 0.4

            tries = 0
            candidate = cur
            found = None

            while tries < (hi - lo + 1):
                candidate += direction
                if candidate < lo:
                    candidate = hi
                if candidate > hi:
                    candidate = lo

                ser.reset_input_buffer()
                ser.reset_output_buffer()
                ser.write(b"VM1;")
                _ = self.read_until_semicolon()
                time.sleep(0.06)

                ser.reset_input_buffer()
                cmd = f"MC{candidate:03d};"
                ser.write(cmd.encode("ascii"))
                _ = self.read_until_semicolon()
                time.sleep(0.10)

                actual = self.read_current_memory_channel()
                if actual == candidate:
                    found = candidate
                    break

                tries += 1

            if found is None:
                self.text_display.append("⚠️ No additional programmed memories found.")
                return

            tag = self.read_memory_tag(found)
            self.current_memory = found
            nice = f"Memory {found:03d}" + (f" — {tag}" if tag else "")
            self.status_label.setText(nice)
            self.text_display.append(f"🔁 {nice}")

            QTimer.singleShot(350, self.update_frequency_display)
            return found

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change/read memory channel:\n{e}")

    def _cat(self, cmd: bytes, read_reply: bool = True, timeout_s: float = 0.8) -> str:
        if not (self.serial_conn and self.serial_conn.is_open):
            return ""

        with self._cat_lock:
            try:
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                self.serial_conn.write(cmd)
                if not read_reply:
                    return ""
                deadline = time.time() + timeout_s
                buf = bytearray()
                while time.time() < deadline:
                    ch = self.serial_conn.read(1)
                    if ch:
                        buf += ch
                        if ch == b';':
                            break
                return buf.decode("ascii", errors="ignore").strip()
            except Exception:
                return ""

    def activate_aprs_memory(self, file):
        self.text_display.clear()

        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        try:
            ser = self.serial_conn
            self._poll_inhibit_until = time.time() + 0.6

            ser.reset_input_buffer()
            ser.reset_output_buffer()
            self._apply_settings_from_file(file)
            self.text_display.append(f"📤 Preset applied from: {file}\n")
            time.sleep(0.25)

            ser.reset_input_buffer()
            ser.write(b'VM1;')
            vm_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> VM1;\n<< {vm_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.10)

            ser.reset_input_buffer()
            cmd = b'MC052;'
            ser.write(cmd)
            mc_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(
                    f">> {cmd.decode('ascii')}\n<< {mc_ack or '[No Response]'}"
                )
            except Exception:
                pass
            time.sleep(0.20)

            self.status_label.setText("📡 APRS memory 052 loaded + preset")
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ APRS activated: MC052 recalled and preset applied\n")

            QTimer.singleShot(350, self.update_frequency_display)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate APRS:\n{e}")

    def activate_aprs_simplex59(self, file):
        self.text_display.clear()

        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        try:
            ser = self.serial_conn
            self._poll_inhibit_until = time.time() + 0.7
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            self._apply_settings_from_file(file)
            self.text_display.append(f"📤 Preset applied from: {file}\n")
            time.sleep(0.25)

            ser.reset_input_buffer()
            ser.write(b'VM1;')
            vm_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> VM1;\n<< {vm_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.12)

            ser.reset_input_buffer()
            ser.write(b'MC059;')
            mc_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> MC059;\n<< {mc_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.25)

            ser.reset_input_buffer()
            ser.write(b"MC;")
            state = self.read_until_semicolon()

            actual = 59
            if state.startswith("MC") and len(state) >= 5 and state[2:5].isdigit():
                ch = int(state[2:5])
                if ch != 0:
                    actual = ch

            tag = self.read_memory_tag(actual)
            nice = f"📡 APRS preset → MC{actual:03d}" + (f" — {tag}" if tag else "")

            self.status_label.setText(nice)
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append(
                "✅ APRS (simplex) activated: preset applied + memory 059 recalled\n"
            )

            QTimer.singleShot(350, self.update_frequency_display)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate APRS → M059:\n{e}")

    def connect_to_radio(self):
        port = self.com_selector.currentText()

        if not port or port.startswith("No serial"):
            QMessageBox.warning(self, "Warning", "No valid serial port selected.")
            return

        try:
            self.serial_conn = serial.Serial(
                port,
                self.BAUD,
                timeout=self.SERIAL_TIMEOUT,
                write_timeout=self.SERIAL_WRITE_TIMEOUT
            )

            self.status_label.setText(f"Connected to {port}")
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            print(f"[DEBUG] Opened serial port {port} at {self.BAUD} baud")

            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #80ff80;
                    color: black;
                    font-weight: bold;
                    border-radius: 6px;
                }
            """)

            # 🔔 Immediately test CAT with ID;
            self.test_radio_response()

        except serial.SerialException as e:
            QMessageBox.critical(self, "Error", f"Unable to open {port}:\n{e}")
            print(f"[ERROR] Serial open failed for {port}: {e}")
            self.serial_conn = None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error opening {port}:\n{e}")
            print(f"[ERROR] Unexpected error opening {port}: {e}")
            self.serial_conn = None


    def activate_ft8_memory(self, file):
        self.text_display.clear()

        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        try:
            ser = self.serial_conn
            self._poll_inhibit_until = time.time() + 0.6

            ser.reset_input_buffer()
            ser.reset_output_buffer()
            self._apply_settings_from_file(file)
            self.text_display.append(f"📤 Preset applied from: {file}\n")

            ok = self._ensure_vfo()
            self.text_display.append(
                "✅ VFO confirmed.\n" if ok else "⚠️ Could not confirm VFO; continuing.\n"
            )

            ser.reset_input_buffer()
            ser.write(b"MD0C;")
            md_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> MD0C;\n<< {md_ack or '[No Response]'}")
            except Exception:
                pass

            self.status_label.setText("🎛️ FT8 preset loaded (DATA-U)")
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ FT8 activated: preset applied + DATA-U set\n")

            QTimer.singleShot(350, self.update_frequency_display)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate FT8:\n{e}")

    def activate_default_memory(self, file):
        self.text_display.clear()
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        try:
            ser = self.serial_conn
            self._poll_inhibit_until = time.time() + 0.7
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            self._apply_settings_from_file(file)
            self.text_display.append(f"📤 Preset applied from: {file}\n")

            ser.reset_input_buffer()
            ser.write(b'VM1;')
            vm_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> VM1;\n<< {vm_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.12)

            ser.reset_input_buffer()
            ser.write(b'MC004;')
            mc_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> MC004;\n<< {mc_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.25)

            ser.reset_input_buffer()
            ser.write(b"MC;")
            state = self.read_until_semicolon()

            actual = 4
            if state.startswith("MC") and len(state) >= 5 and state[2:5].isdigit():
                ch = int(state[2:5])
                if ch != 0:
                    actual = ch

            tag = self.read_memory_tag(actual)
            nice = f"🎛️ Default preset loaded (MC{actual:03d}" + (f" — {tag})" if tag else ")")

            self.status_label.setText(nice)
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ Default activated: preset applied and memory recalled\n")

            QTimer.singleShot(350, self.update_frequency_display)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate Default:\n{e}")

    def activate_default2_memory(self, file):
        self.text_display.clear()
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        try:
            ser = self.serial_conn
            self._poll_inhibit_until = time.time() + 0.7
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            self._apply_settings_from_file(file)
            self.text_display.append(f"📤 Preset applied from: {file}\n")

            ser.reset_input_buffer()
            ser.write(b'VM1;')
            vm_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> VM1;\n<< {vm_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.12)

            ser.reset_input_buffer()
            ser.write(b'MC059;')
            mc_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> MC058;\n<< {mc_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.25)

            ser.reset_input_buffer()
            ser.write(b"MC;")
            state = self.read_until_semicolon()

            actual = 58
            if state.startswith("MC") and len(state) >= 5 and state[2:5].isdigit():
                ch = int(state[2:5])
                if ch != 0:
                    actual = ch

            tag = self.read_memory_tag(actual)
            nice = f"🎛️ Default 2 preset loaded (MC{actual:03d}" + (f" — {tag})" if tag else ")")

            self.status_label.setText(nice)
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ Default 2 activated: preset applied and memory 058 recalled\n")

            QTimer.singleShot(350, self.update_frequency_display)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate Default 2:\n{e}")

    def _poll_tx_status(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            if hasattr(self, "tx_led"):
                self.tx_led.set_on(False)
            return

        try:
            ser = self.serial_conn

            ser.reset_input_buffer()
            ser.write(b"TX;")
            tx_reply = self.read_until_semicolon()

            is_tx = self._parse_tx_from_tx_reply(tx_reply)

            if is_tx is None:
                ser.reset_input_buffer()
                ser.write(b"IF;")
                if_reply = self.read_until_semicolon()
                is_tx = self._parse_tx_from_if(if_reply)

            if is_tx is None:
                ser.reset_input_buffer()
                ser.write(b"RM5;")
                rm = self.read_until_semicolon() or ""
                raw = 0
                if rm.startswith("RM5") and len(rm) >= 6 and rm[3:6].isdigit():
                    raw = int(rm[3:6])
                is_tx = (raw >= 10)

            self.tx_led.set_on(bool(is_tx))

        except Exception:
            self.tx_led.set_on(False)

    def _parse_tx_from_tx_reply(self, tx_reply: str):
        if not (isinstance(tx_reply, str) and tx_reply.startswith("TX") and tx_reply.endswith(";")):
            return None
        if len(tx_reply) >= 4 and tx_reply[2] in "01":
            return tx_reply[2] == "1"
        return None

    def _parse_tx_from_if(self, if_reply: str):
        if not (isinstance(if_reply, str) and if_reply.startswith("IF") and if_reply.endswith(";")):
            return None

        payload = if_reply[2:-1]
        candidates = []
        for idx in (27, 28, 29, 30, 31):
            if 0 <= idx < len(payload) and payload[idx] in "01":
                candidates.append(payload[idx])

        if candidates and all(c == candidates[0] for c in candidates):
            return candidates[0] == "1"

        bits = [ch for ch in payload if ch in "01"]
        if bits:
            return bits[-1] == "1"

        return None

    def activate_wiresx_memory(self, file):
        self.text_display.clear()
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        try:
            ser = self.serial_conn
            self._poll_inhibit_until = time.time() + 0.7
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            self._apply_settings_from_file(file)
            self.text_display.append(f"📤 Preset applied from: {file}\n")

            ser.reset_input_buffer()
            ser.write(b'VM1;')
            vm_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> VM1;\n<< {vm_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.12)

            ser.reset_input_buffer()
            ser.write(b'MC001;')
            mc_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> MC001;\n<< {mc_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.25)

            ser.reset_input_buffer()
            ser.write(b"MC;")
            state = self.read_until_semicolon()

            actual = 1
            if state.startswith("MC") and len(state) >= 5 and state[2:5].isdigit():
                ch = int(state[2:5])
                if ch != 0:
                    actual = ch

            tag = self.read_memory_tag(actual)
            nice = f"📡 WIRES-X memory MC{actual:03d}" + (f" — {tag}" if tag else "")

            self.status_label.setText(nice)
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ WIRES-X activated: memory recalled and preset applied\n")

            QTimer.singleShot(350, self.update_frequency_display)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate WIRES-X:\n{e}")

    def activate_ssb_memory(self, file):
        self.text_display.clear()
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            ser = self.serial_conn

            self._poll_inhibit_until = time.time() + 0.8
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            self._apply_settings_from_file(file)
            self.text_display.append(f"📤 Preset applied from: {file}\n")

            ser.reset_input_buffer()
            ser.write(b'VM1;')
            vm_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> VM1;\n<< {vm_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.12)

            ser.reset_input_buffer()
            ser.write(b'MC060;')
            mc_ack = self.read_until_semicolon()
            try:
                self.cat_response_display.append(f">> MC060;\n<< {mc_ack or '[No Response]'}")
            except Exception:
                pass
            time.sleep(0.25)

            ser.reset_input_buffer()
            ser.write(b"MD;")
            md = self.read_until_semicolon()
            if not (md.startswith("MD") and len(md) >= 4 and md[2:4] == "00"):
                ser.reset_input_buffer()
                ser.write(b"MD00;")
                md_ack = self.read_until_semicolon()
                try:
                    self.cat_response_display.append(f">> MD00;\n<< {md_ack or '[No Response]'}")
                except Exception:
                    pass
                time.sleep(0.12)

            ser.reset_input_buffer()
            ser.write(b"MC;")
            state = self.read_until_semicolon()
            actual = 60
            if state.startswith("MC") and len(state) >= 5 and state[2:5].isdigit():
                ch = int(state[2:5])
                if ch != 0:
                    actual = ch

            tag = self.read_memory_tag(actual)
            nice = f"🎙️ SSB preset loaded (MC{actual:03d})" + (f" — {tag}" if tag else "")
            self.status_label.setText(nice)
            self.status_label.setStyleSheet("color: white; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ SSB activated: preset applied and memory recalled\n")

            QTimer.singleShot(350, self.update_frequency_display)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate SSB:\n{e}")

    def send_cat_command(self):
        if not self.serial_conn:
            return
        cmd = self.cat_input.text().strip()
        if not cmd.endswith(";"):
            cmd += ";"
        self.serial_conn.write(cmd.encode())
        time.sleep(0.2)
        resp = self.serial_conn.read_all().decode(errors="ignore")
        self.cat_response_display.append(f">> {cmd}\n<< {resp if resp else '[No Response]'}")

    def connect_cat_send(self):
        self.cat_input.returnPressed.connect(
            lambda: self.send_cat_command()
        )

    def select_and_load_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load XML Preset File", "",
            "XML Files (*.xml)"
        )
        if filename:
            self._apply_settings_from_file(filename)

    def load_all_menus(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        was_meter_running = hasattr(self, "meter_timer") and self.meter_timer.isActive()
        was_freq_running = hasattr(self, "freq_timer") and self.freq_timer.isActive()
        try:
            if was_meter_running:
                self.meter_timer.stop()
            if was_freq_running:
                self.freq_timer.stop()

            total = len(MENU_DESCRIPTIONS)
            self.progress_bar.setValue(0)
            self.text_display.clear()

            root = ET.Element("YaesuMenuItems")

            for idx, (num, (desc, opt_range, unit)) in enumerate(MENU_DESCRIPTIONS.items()):
                cmd = f"EX{num};"

                self.serial_conn.reset_input_buffer()
                self.serial_conn.write(cmd.encode("ascii"))
                decoded = self.read_until_semicolon()

                menu = ET.SubElement(root, "YaesuFT991A_MenuItems")
                ET.SubElement(menu, "MENU_NUMBER").text = num
                ET.SubElement(menu, "DESCRIPTION").text = desc

                val = "----"
                if decoded.startswith(f"EX{num}") and decoded.endswith(";") and len(decoded) >= 6:
                    val = decoded[5:-1] or "----"

                ET.SubElement(menu, "MENU_VALUE").text = val

                unit_str = f" {unit}" if unit else ""
                line = f"{num}\t{val}{unit_str}  {desc}    ({opt_range})"
                self.text_display.append(line)

                pct = int((idx + 1) / total * 100)
                self.progress_bar.setValue(pct)
                QApplication.processEvents()

            self._last_menu_dump = root

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed while reading menus:\n{e}")
        finally:
            if was_meter_running:
                self.meter_timer.start(200)
            if was_freq_running:
                self.freq_timer.start(500)

        choice = QMessageBox.question(
            self,
            "Save Settings",
            "Do you want to save these settings to a file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if choice == QMessageBox.StandardButton.Yes:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Settings to File",
                "FT991A_Backup.xml", "XML Files (*.xml)"
            )
            if filename:
                tree = ET.ElementTree(root)
                tree.write(filename, encoding="utf-8", xml_declaration=True)
                self.text_display.append(f"\n📁 Settings saved to: {filename}")

    def disconnect_from_radio(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.serial_conn = None
            self.connect_btn.setStyleSheet(
                "QPushButton { background-color: white; color: black; font-weight: bold; }"
            )
            self.status_label.setStyleSheet("color: orange; font-weight: bold; padding: 4px;")
            self.status_label.setText("Disconnected")
            self.connect_btn.setText("Connect")
            self.disconnect_btn.setStyleSheet(
                "QPushButton { background-color: rgb(255, 85, 85); "
                "color: white; font-weight: bold; }"
            )

    def set_vm_mode(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        was_meter_running = hasattr(self, "meter_timer") and self.meter_timer.isActive()
        was_freq_running = hasattr(self, "freq_timer") and self.freq_timer.isActive()
        try:
            if was_meter_running:
                self.meter_timer.stop()
            if was_freq_running:
                self.freq_timer.stop()

            ser = self.serial_conn
            ser.reset_input_buffer()

            ser.write(b"MC;")
            before = self.read_until_semicolon() or ""
            in_vfo = before.startswith("MC") and len(before) >= 5 and before[2:5] == "000"

            target_cmd = b"VM1;" if in_vfo else b"VM0;"
            ser.reset_input_buffer()
            ser.write(target_cmd)
            time.sleep(0.12)

            ser.reset_input_buffer()
            ser.write(b"MC;")
            after = self.read_until_semicolon() or ""
            now_vfo = after.startswith("MC") and len(after) >= 5 and after[2:5] == "000"

            self.cat_response_display.append(f">> MC;\n<< {before}")
            self.cat_response_display.append(
                f">> {target_cmd.decode('ascii')}\n>> MC;\n<< {after}"
            )

            if now_vfo:
                self.status_label.setText("✔️ Now in VFO")
                mode_text = "VFO"
            else:
                ch = after[2:5] if after.startswith("MC") and len(after) >= 5 else "???"
                self.status_label.setText(f"✔️ Now in Memory (MC{ch})")
                mode_text = f"Memory (MC{ch})"

            self.status_label.setStyleSheet(
                "color: darkgreen; font-weight: bold; padding: 4px;"
            )
            self.text_display.append(f"\n🌀 Switched to {mode_text}\n")

            if in_vfo == now_vfo:
                self.text_display.append("⚠️ Could not confirm a mode change (state unchanged).")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to switch VFO/MEM: {e}")
        finally:
            if was_meter_running:
                self.meter_timer.start(200)
            if was_freq_running:
                self.freq_timer.start(500)

    def test_radio_response(self):
        if not (self.serial_conn and self.serial_conn.is_open):
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return False

        was_meter_running = hasattr(self, "meter_timer") and self.meter_timer.isActive()
        was_freq_running = hasattr(self, "freq_timer") and self.freq_timer.isActive()

        try:
            if was_meter_running:
                self.meter_timer.stop()
            if was_freq_running:
                self.freq_timer.stop()

            ser = self.serial_conn
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            ser.write(b'ID;')
            resp = self.read_until_semicolon()

            self.cat_response_display.append(f">> ID;\n<< {resp if resp else '[No Response]'}")

            if resp and resp.startswith('ID') and resp.endswith(';'):
                ident = resp[2:-1]
                self.text_display.append(f"✅ Test response from radio: {resp} (ID={ident})")
                self.status_label.setText("Radio responded to test command")
                self.status_label.setStyleSheet(
                    "color: darkgreen; font-weight: bold; padding: 4px;"
                )
                return True
            else:
                self.text_display.append("⚠️ No valid response to ID;")
                self.status_label.setText("No response to test")
                self.status_label.setStyleSheet(
                    "color: red; font-weight: bold; padding: 4px;"
                )
                return False

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Test failed: {e}")
            return False
        finally:
            if was_meter_running:
                self.meter_timer.start(200)
            if was_freq_running:
                self.freq_timer.start(500)

    def load_preset_from_xml(self, filename):
        self._apply_settings_from_file(filename)

    def load_preset_from_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load XML Preset File", "", "XML Files (*.xml)"
        )
        if filename:
            self._apply_settings_from_file(filename)

    def _apply_settings_from_file(self, file):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            path = Path(file)
            if not path.is_absolute():
                path = BASE_DIR / path

            tree = ET.parse(str(path))
            root = tree.getroot()
            items = root.findall("YaesuFT991A_MenuItems")
            total = len(items)
            self.progress_bar.setValue(0)
            self.text_display.append(
                f"\n📤 Uploading {total} menu settings from {path.name}...\n"
            )

            for idx, item in enumerate(items):
                num = item.find("MENU_NUMBER").text.strip().zfill(3)
                val = item.find("MENU_VALUE").text.strip()
                cmd = f"EX{num}{val};"
                self.serial_conn.write(cmd.encode())
                self.text_display.append(f"⏩ Sent: {num} → {val}")
                self.progress_bar.setValue(int((idx + 1) / total * 100))
                self.progress_bar.repaint()
                QApplication.processEvents()
                time.sleep(0.02)

            self.progress_bar.setValue(100)
            self.status_label.setText(f"✅ Preset loaded from {path.name}")
            self.status_label.setStyleSheet(
                "color: black; font-weight: bold; padding: 4px;"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preset: {e}")
            self.status_label.setText("Error loading preset")
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold; padding: 4px;"
            )

    def save_radio_to_file(self):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio before saving.")
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold; padding: 4px;"
            )
            self.status_label.setText("Not connected")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Radio Settings", "radio_preset.xml", "XML Files (*.xml)"
        )
        if not filename:
            return

        root = ET.Element("YaesuMenuItems.xml")
        total = len(MENU_DESCRIPTIONS)

        for idx, (num, (desc, _, _)) in enumerate(MENU_DESCRIPTIONS.items()):
            menu = ET.SubElement(root, "YaesuFT991A_MenuItems")
            ET.SubElement(menu, "MENU_NUMBER").text = num
            ET.SubElement(menu, "DESCRIPTION").text = desc

            cmd = f"EX{num};"
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(cmd.encode('ascii'))
            response = b""
            timeout = time.time() + 0.5
            while time.time() < timeout:
                part = self.serial_conn.read(1)
                if part:
                    response += part
                    if part == b';':
                        break
            decoded = response.decode(errors='ignore').strip()

            if decoded.startswith(f"EX{num}"):
                val = decoded[5:]
            else:
                val = "----"

            ET.SubElement(menu, "MENU_VALUE").text = val
            self.text_display.append(f"Read Menu {num} → {val} ({desc})")
            self.progress_bar.setValue(int((idx + 1) / total * 100))

        tree = ET.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)
        self.text_display.append(f"📁 Settings saved to: {filename}\n")
        self.status_label.setText("Radio settings saved to file")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(33, 66, 109))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(
        QPalette.ColorRole.Highlight,
        QColor(142, 45, 197).lighter()
    )
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(dark_palette)

    gui = FT991AController()
    gui.show()
    sys.exit(app.exec())
