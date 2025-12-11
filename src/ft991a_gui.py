import sys
import xml.etree.ElementTree as ET
import time
import serial
import serial.tools.list_ports
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QHBoxLayout, QMessageBox, QProgressBar, QTextEdit,
    QTabWidget, QFileDialog, QLineEdit
)
from PyQt5.QtGui import QPalette, QColor, QLinearGradient, QBrush

# MENU_DESCRIPTIONS dictionary remains unchanged for brevity...

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


class FT991AController(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FT-991A Preset Control Panel")
        self.setGeometry(300, 300, 1100, 700)
        self.serial_conn = None

        # Tabs
        self.tabs = QTabWidget()
        self.main_tab = QWidget()
        self.cat_tab = QWidget()
        self.tabs.addTab(self.main_tab, "Menu Reader")
        self.tabs.addTab(self.cat_tab, "CAT Terminal")

        # 🌌 Background container with gradient support
        self.main_tab_background = QWidget()
        self.main_tab_background.setObjectName("main_tab_background")
        self.main_tab_layout = QVBoxLayout(self.main_tab_background)

        # COM port selector
        self.com_selector = QComboBox()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_selector.addItems(ports)
        if "COM3" in ports:
            self.com_selector.setCurrentText("COM3")
        self.main_tab_layout.addWidget(QLabel("Select COM Port:"))
        self.main_tab_layout.addWidget(self.com_selector)

        # Connect/Disconnect buttons
        connect_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_to_radio)
        self.connect_btn.setStyleSheet("QPushButton { background-color: white; color: black; font-weight: bold; }")
        connect_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_from_radio)
        self.disconnect_btn.setStyleSheet("QPushButton { background-color: white; color: black; font-weight: bold; }")
        connect_layout.addWidget(self.disconnect_btn)
        self.main_tab_layout.addLayout(connect_layout)

        # Simplex Frequency Buttons
        simplex_layout = QHBoxLayout()
        self.add_simplex_button(simplex_layout, "144.420 MHz", "144420000")
        self.add_simplex_button(simplex_layout, "446.000 MHz", "446000000")
        self.add_simplex_button(simplex_layout, "145.600 MHz", "145600000")
        self.add_simplex_button(simplex_layout, "433.500 MHz", "433500000")
        self.main_tab_layout.addLayout(simplex_layout)

        # Preset Buttons
        btn_layout = QHBoxLayout()
        presets = {
            "Default": "defaultv002.xml",
            "FT8": "FT8settings.xml",
            "Winlink": "WINLINK_APRS.xml",
            "APRS": "aprs.xml",
            "SSB": "SSB_setting.xml",
            "WIRES-X": "WIRESX.xml"
        }

        for label, file in presets.items():
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a0ca3;
                    color: white;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: #7209b7;
                }
            """)
            if label.lower() == "winlink":
                btn.clicked.connect(partial(self.activate_winlink_memory, file))
            elif label.lower() == "aprs":
                btn.clicked.connect(partial(self.activate_aprs_memory, file))
            elif label.lower() == "wires-x":
                btn.clicked.connect(partial(self.activate_wiresx_memory, file))
            elif label.lower() == "ssb":
                btn.clicked.connect(partial(self.activate_ssb_memory, file))
            elif label.lower() == "default":
                btn.clicked.connect(partial(self.activate_default_memory, file))
            elif label.lower() == "ft8":
                btn.clicked.connect(partial(self.activate_default_memory, file))
            else:
                btn.clicked.connect(partial(self.load_preset_from_file, file))

            btn.setToolTip(f"Load {label} preset from {file}")
            btn_layout.addWidget(btn)
        self.main_tab_layout.addLayout(btn_layout)

        # Save/Load Buttons
        io_layout = QHBoxLayout()
        self.save_btn = QPushButton("📥 Download From Radio to File")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a0ca3;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #7209b7;
            }
        """)
        self.save_btn.clicked.connect(self.load_all_menus)
        io_layout.addWidget(self.save_btn)

        self.load_btn = QPushButton("📤 Load From File to Radio")
        self.load_btn.clicked.connect(self.select_and_load_file)
        io_layout.addWidget(self.load_btn)
        self.main_tab_layout.addLayout(io_layout)

        # Text Display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("background-color: #0f0f3d; color: white; font-family: Consolas; font-size: 11px;")
        self.main_tab_layout.addWidget(self.text_display)

        # Progress Bar
        self.progress_bar = QProgressBar()
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
        self.main_tab_layout.addWidget(self.progress_bar)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: lightgreen; font-weight: bold; padding: 4px;")
        self.main_tab_layout.addWidget(self.status_label)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #3a0ca3;
                color: white;
                padding: 6px 25px;
                min-width: 100px;
                font-weight: bold;
                font-size: 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #7209b7;
            }
            QTabBar::tab:hover {
                background: #560bad;
            }
        """)
        # Put background into main_tab
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.main_tab_background)
        self.main_tab.setLayout(container_layout)

        # Add tabs to the main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        # 🔥 Finally apply the gradient style
        self.apply_custom_style()
###
    def apply_custom_style(self):   
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(33, 66, 109))  # Dark blue
        gradient.setColorAt(1.0, QColor(0, 0, 0))      # Black

        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(gradient))

        # 🔥 This is the correct widget!
        self.main_tab_background.setAutoFillBackground(True)
        self.main_tab_background.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.setStyleSheet("""
            QWidget {
                background-color: #0f0f3d;  /* Dark navy blue everywhere */
                color: white;
            }

            QTabWidget::pane {
                background: #0f0f3d;  /* Pane behind the tabs */
                border: none;
            }

            QTabBar::tab {
            background-color: #3a0ca3;
            color: white;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: bold;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin: 1px;
            }

            QTabBar::tab:selected {
                background-color: #7209b7;
            }

            QTabBar::tab:hover {
                background-color: #560bad;
            }

            QLabel {
                color: white;
            }
        """)

        # CAT tab
        cat_layout = QVBoxLayout()
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("Enter CAT command (e.g., FA;)")
        cat_layout.addWidget(self.cat_input)

        self.cat_send_btn = QPushButton("Send CAT Command")
        self.cat_send_btn.clicked.connect(self.send_cat_command)
        cat_layout.addWidget(self.cat_send_btn)

        self.cat_response_display = QTextEdit()
        self.cat_response_display.setReadOnly(True)
        self.cat_response_display.setStyleSheet("background-color: #1e1e1e; color: #90ee90; font-family: Consolas;")
        cat_layout.addWidget(self.cat_response_display)
        self.cat_tab.setLayout(cat_layout)


    ###WINLINK BUTTON

    def activate_winlink_memory(self, file):
        self.text_display.clear()  # ← this line clears screen
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            self.serial_conn.reset_input_buffer()
            self._apply_settings_from_file(file)
            time.sleep(0.3)
            self.serial_conn.write(b'VM;')  # V/M mode

            time.sleep(0.3)
            self.serial_conn.write(b'MC053;')  # Memory channel 53
            time.sleep(0.5)
            ##self.serial_conn.write(b'MD0A;')  # MODE DATA-FM
            ##self._apply_settings_from_file(file)

            self.status_label.setText("📡 Winlink memory 53 loaded + preset")
            self.status_label.setStyleSheet("color: black; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ Winlink activated: DATA-FM + MC053 + preset applied\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate Winlink:\n{e}")


    ###APRS BUTTON

    def activate_aprs_memory(self, file):
        self.text_display.clear()  # ← this line clears screen
        print(f"[DEBUG] _apply_settings_from_file() loading: {file}")

        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            self.serial_conn.reset_input_buffer()
            self._apply_settings_from_file(file)
            print(f"Trying to apply settings from: {file}")
            time.sleep(0.3)
            self.serial_conn.write(b'VM;')  # V/M mode
            time.sleep(0.3)
            self.serial_conn.write(b'MC052;')  # Memory channel 52
            time.sleep(0.3)
            ##self.serial_conn.write(b'MD0A;')  # MODE DATA-FM
            ##time.sleep(0.2)
            

            self.status_label.setText("📡 APRS memory 52 loaded + preset")
            self.status_label.setStyleSheet("color: black; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ APRS activated: DATA-FM + MC052 + preset applied\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate APRS:\n{e}")

    def connect_to_radio(self):
        port = self.com_selector.currentText()
        try:
            self.serial_conn = serial.Serial(port, 38400, timeout=1)
            self.status_label.setText(f"Connected to {port}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unable to open {port}: {e}")

    #FT8 BUTTON
    def activate_ft8_memory(self, file):
        self.text_display.clear()  # ← this line clears screen
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            self.serial_conn.reset_input_buffer()
            self._apply_settings_from_file(file)
            

            self.status_label.setText("🎛️ FT8 preset loaded")
            self.status_label.setStyleSheet("color: lightblue; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ FT8 activated: Preset applied\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate FT8:\n{e}")

    #Default BUTTON
    def activate_default_memory(self, file):
        self.text_display.clear()  # ← this line clears screen
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            self.serial_conn.reset_input_buffer()
            self._apply_settings_from_file(file)
            time.sleep(0.3)
            self.serial_conn.write(b'VM;')  # V/M mode
            time.sleep(0.3)
            self.serial_conn.write(b'MC038;')  # Memory channel 38
            time.sleep(0.3)
            ##self.serial_conn.write(b'MD0A;')  # MODE DATA-FM
            ##time.sleep(0.2)

            self.status_label.setText("🎛️ Default preset loaded")
            self.status_label.setStyleSheet("color: lightblue; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ Default activated: Preset applied\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate Default:\n{e}")



    ### WIRES-X BUTTON

    def activate_wiresx_memory(self, file):
        self.text_display.clear()  # ← this line clears screen
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            
            self.serial_conn.reset_input_buffer()
            
            self._apply_settings_from_file(file)
            time.sleep(0.3)
            self.serial_conn.write(b'VM;')  # V/M mode
            time.sleep(0.3)
            self.serial_conn.write(b'MC001;')  # Memory channel 001
            time.sleep(0.3)
            ##self.serial_conn.write(b'MD0E;')  # MODE FM (voice, not data)
            ##time.sleep(0.2)

            self.status_label.setText("📡 WIRES-X memory 001 loaded + preset")
            self.status_label.setStyleSheet("color: deepskyblue; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ WIRES-X activated: FM + MC001 + preset applied\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate WIRES-X:\n{e}")


    ### SSB 40 meter band 
    def activate_ssb_memory(self, file):
        self.text_display.clear()  # ← this line clears screen
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            self.serial_conn.reset_input_buffer()
            self._apply_settings_from_file(file)
            time.sleep(0.3)
            self.serial_conn.write(b'VM;')       # Switch to memory mode
            time.sleep(0.3)
            self.serial_conn.write(b'MC060;')    # Memory channel 002
            time.sleep(0.3)
        ##self.serial_conn.write(b'MD01;')     # MODE = USB (01 = USB)
        ##time.sleep(0.2)

            self.status_label.setText("🎙️ SSB memory 002 loaded + preset")
            self.status_label.setStyleSheet("color: orange; font-weight: bold; padding: 4px;")
            self.text_display.append("✅ SSB activated: USB + MC002 + preset applied\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to activate SSB:\n{e}")


#disconnect button 
    def disconnect_from_radio(self):
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
            self.status_label.setText("Disconnected")

#simplex bttons 
    def add_simplex_button(self, layout, label, freq_str):
        btn = QPushButton(label)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4cc9f0;
                color: black;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4895ef;
            }
        """)
        btn.clicked.connect(lambda: self.set_simplex(freq_str, label))
        layout.addWidget(btn)

## SIMPLEX
    def set_simplex(self, freq, label):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            self.serial_conn.write(f"FA{freq};".encode())  # Frequency
            self.serial_conn.write(b"MD04;")                # FM mode
            self.serial_conn.write(b"FT0;")                # Simplex (no split)
            self.text_display.append(f"🔊 Set to {label} (FM Simplex)")
            self.status_label.setText(f"Active: {label}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set frequency: {e}")

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

    
    def select_and_load_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load XML Preset File", "", "XML Files (*.xml)")
        if filename:
            self._apply_settings_from_file(filename)

    def _apply_settings_from_file(self, filename):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Please connect to the radio first.")
            return
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            menus = root.findall('YaesuFT991A_MenuItems')
            for menu in menus:
                num = menu.find('MENU_NUMBER').text.strip().zfill(3)
                val = menu.find('MENU_VALUE').text.strip()
                if num and val:
                    cmd = f"EX{num}{val};"
                    self.serial_conn.write(cmd.encode('ascii'))
                    self.text_display.append(f"Menu {num} → {val}")
                    time.sleep(0.02)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preset: {e}")

    def save_radio_to_file(self):
        QMessageBox.information(self, "Not Implemented", "Saving radio settings is not yet implemented.")

#load all menus
    def load_all_menus(self):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return

        total = len(MENU_DESCRIPTIONS)
        self.progress_bar.setValue(0)
        self.text_display.clear()
        root = ET.Element("YaesuMenuItems.xml")

        for idx, (num, (desc, opt_range, unit)) in enumerate(MENU_DESCRIPTIONS.items()):
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
            menu = ET.SubElement(root, "YaesuFT991A_MenuItems")
            ET.SubElement(menu, "MENU_NUMBER").text = num
            ET.SubElement(menu, "DESCRIPTION").text = desc
            if decoded.startswith(f"EX{num}"):
                val = decoded[5:].rstrip(';')

            ET.SubElement(menu, "MENU_VALUE").text = val
            unit_str = f" {unit}" if unit else ""
            line = f"{num}\t{val}{unit_str}  {desc}    ({opt_range})"
            self.text_display.append(line)
            self.progress_bar.setValue(int((idx + 1) / total * 100))
            QApplication.processEvents()

# Ask the user if they want to save the settings
        choice = QMessageBox.question(
            self,
            "Save Settings",
            "Do you want to save these settings to a file?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if choice == QMessageBox.Yes:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Settings to File", "FT991A_Backup.xml", "XML Files (*.xml)"
            )
            if filename:
                tree = ET.ElementTree(root)
                tree.write(filename, encoding="utf-8", xml_declaration=True)
                self.text_display.append(f"\n📁 Settings saved to: {filename}")



    
    # Existing methods unchanged...


    def connect_to_radio(self):
        port = self.com_selector.currentText()
        try:
            self.serial_conn = serial.Serial(port, 38400, timeout=1)
            self.connect_btn.setText("Connected")
            self.connect_btn.setStyleSheet("QPushButton { background-color: rgb(125,239,140); color: black; font-weight: bold; }")
            self.disconnect_btn.setStyleSheet("QPushButton { background-color: white; color: black; font-weight: bold; }")
            self.status_label.setStyleSheet("color: darkgreen; font-weight: bold; padding: 4px;")
            self.status_label.setText(f"Connected to {port}")
        except serial.SerialException:
            QMessageBox.critical(self, "Error", f"Unable to open {port}")
            self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 4px;")
            self.status_label.setText("Connection failed")
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet("QPushButton { background-color: white; color: black; font-weight: bold; }")

    #DISCONNECT BTN
    def disconnect_from_radio(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.serial_conn = None
            self.connect_btn.setStyleSheet("QPushButton { background-color: white; color: black; font-weight: bold; }")
            self.status_label.setStyleSheet("color: orange; font-weight: bold; padding: 4px;")
            self.status_label.setText("Disconnected")
            self.connect_btn.setText("Connect")
            self.disconnect_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgb(255, 60, 60);
                    color: white;
                    font-weight: bold;
                }
                """)
            self.disconnect_btn.setStyleSheet("QPushButton { background-color: rgb(255, 85, 85); color: white; font-weight: bold; }")

    
    ### V/M mode      

    def set_vm_mode(self):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            self.serial_conn.write(b'MC;')  # Switch to V/M mode
            self.status_label.setText("✔️ VFO/MEM mode command sent")
            self.status_label.setStyleSheet("color: darkgreen; font-weight: bold; padding: 4px;")
            self.text_display.append("\n🌀 V/M Mode command issued (MC;)\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send V/M command: {e}")

    def test_radio_response(self):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(b'ID;')  # Standard CAT query command
            time.sleep(0.3)
            response = self.serial_conn.read_all().decode('ascii', errors='ignore').strip()
            if response:
                self.text_display.append(f"✅ Test response from radio: {response}")
                self.status_label.setText("Radio responded to test command")
                self.status_label.setStyleSheet("color: darkgreen; font-weight: bold; padding: 4px;")
            else:
                self.text_display.append("⚠️ No response from radio to test command.")
                self.status_label.setText("No response to test")
                self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 4px;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Test failed: {e}")




##  Load from XML file
    def load_preset_from_xml(self, filename):
        self._apply_settings_from_file(filename)

    def load_preset_from_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load XML Preset File", "", "XML Files (*.xml)")
        if filename:
            self._apply_settings_from_file(filename)

    def _apply_settings_from_file(self, file):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio first.")
            return
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            items = root.findall("YaesuFT991A_MenuItems")
            total = len(items)
            self.progress_bar.setValue(0)
            self.text_display.append(f"\n📤 Uploading {total} menu settings from {file}...\n")

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
            self.status_label.setText(f"✅ Preset loaded from {file.split('/')[-1]}")
            self.status_label.setStyleSheet("color: black; font-weight: bold; padding: 4px;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preset: {e}")
            self.status_label.setText("Error loading preset")
            self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 4px;")
    
    def save_radio_to_file(self):
        if not self.serial_conn or not self.serial_conn.is_open:
            QMessageBox.warning(self, "Warning", "Connect to the radio before saving.")
            self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 4px;")
            self.status_label.setText("Not connected")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save Radio Settings", "radio_preset.xml", "XML Files (*.xml)")
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
    gui = FT991AController()
    gui.show()
    sys.exit(app.exec_())
