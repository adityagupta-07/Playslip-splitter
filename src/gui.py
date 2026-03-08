import sys
import os
import tempfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QBrush
from utils.pdf_utils import split_payslip_pdf
from utils.zip_utils import create_zip


class GlowBackground(QWidget):
    """Full-window background with radial glows matching Ultra Tendency site."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#080C10"))

        # Teal glow — top right
        g1 = QRadialGradient(self.width() * 0.80, self.height() * 0.12, self.width() * 0.55)
        g1.setColorAt(0.0, QColor(32, 178, 170, 55))
        g1.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), QBrush(g1))

        # Red/warm glow — bottom left
        g2 = QRadialGradient(self.width() * 0.04, self.height() * 0.88, self.width() * 0.42)
        g2.setColorAt(0.0, QColor(180, 40, 30, 50))
        g2.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), QBrush(g2))


class PayslipSplitter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultra Payslip Pro")
        self._dot_count = 0

        # Must create bg BEFORE showMaximized — resizeEvent fires immediately
        self.bg = GlowBackground(self)
        self.bg.lower()

        self.setStyleSheet("""
            * { font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; }

            QFrame#topbar {
                background-color: rgba(8, 12, 16, 220);
                border-bottom: 1px solid rgba(255,255,255,0.07);
            }
            QLabel#logoMain {
                font-size: 16px; font-weight: 800;
                color: #FFFFFF; letter-spacing: 1px;
            }
            QLabel#logoSub {
                font-size: 10px; color: #4ECDC4; letter-spacing: 3px;
            }

            QFrame#card {
                background-color: rgba(10, 18, 28, 210);
                border: 1px solid rgba(78, 205, 196, 0.20);
                border-radius: 18px;
            }

            QLabel#tag {
                background-color: rgba(78, 205, 196, 0.12);
                color: #4ECDC4;
                font-size: 11px; font-weight: 600; letter-spacing: 3px;
                border-radius: 4px; padding: 4px 14px;
            }
            QLabel#h1 {
                font-size: 38px; font-weight: 800; color: #FFFFFF;
            }
            QLabel#h2 {
                font-size: 38px; font-weight: 800; color: #4ECDC4;
            }
            QLabel#body {
                font-size: 13px; color: rgba(255,255,255,0.40); line-height: 1.7;
            }

            QFrame#pill {
                background-color: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 8px;
            }
            QLabel#pillTxt { font-size: 12px; color: rgba(255,255,255,0.50); }
            QLabel#pillDot { font-size: 7px;  color: #4ECDC4; }

            QPushButton#uploadBtn {
                background-color: #4ECDC4;
                border: none; border-radius: 8px;
                padding: 0px 36px;
                font-size: 14px; font-weight: 700;
                color: #080C10; letter-spacing: 0.3px;
            }
            QPushButton#uploadBtn:hover { background-color: #62D9D1; }
            QPushButton#uploadBtn:disabled {
                background-color: rgba(78,205,196,0.22);
                color: rgba(8,12,16,0.35);
            }

            QLabel#statusIdle { font-size: 12px; color: rgba(255,255,255,0.18); }
            QLabel#statusBusy { font-size: 12px; color: #4ECDC4; }
            QLabel#statusOk   { font-size: 12px; color: #4ECDC4; font-weight: 600; }
            QLabel#statusErr  { font-size: 12px; color: #FF6B6B; font-weight: 600; }

            QPushButton#closeBtn {
                background: transparent;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 6px; padding: 6px 20px;
                font-size: 12px; color: rgba(255,255,255,0.25);
            }
            QPushButton#closeBtn:hover { border-color: #FF6B6B; color: #FF6B6B; }
        """)

        self.showFullScreen()

        # Root
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(66)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(48, 0, 48, 0)

        logo_label = QLabel()
        logo_label.setStyleSheet("background: transparent;")
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(42, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("ULTRA TENDENCY")
            logo_label.setStyleSheet("font-size:16px; font-weight:800; color:#FFFFFF;")
        tb.addWidget(logo_label)
        tb.addStretch()

        ver = QLabel("Payslip Pro  ·  v2.0")
        ver.setStyleSheet("font-size:12px; color:rgba(255,255,255,0.18); letter-spacing:1px;")
        tb.addWidget(ver)
        root.addWidget(topbar)

        # ── Centre ───────────────────────────────────────────────────
        root.addStretch()
        ch = QHBoxLayout()
        ch.addStretch()

        # Card
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(560)

        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(90)
        glow.setColor(QColor(78, 205, 196, 35))
        glow.setOffset(0, 12)
        card.setGraphicsEffect(glow)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(52, 48, 52, 48)
        cl.setSpacing(0)

        # Tag
        tag = QLabel("PAYROLL AUTOMATION")
        tag.setObjectName("tag")
        tag.setFixedWidth(200)
        cl.addWidget(tag)
        cl.addSpacing(22)

        # Heading
        h1 = QLabel("Split payslips,")
        h1.setObjectName("h1")
        cl.addWidget(h1)
        h2 = QLabel("instantly.")
        h2.setObjectName("h2")
        cl.addWidget(h2)
        cl.addSpacing(18)

        # Body text
        body = QLabel(
            "Upload your master PDF — we automatically split, rename\n"
            "and ZIP every payslip straight into your Downloads folder."
        )
        body.setObjectName("body")
        body.setWordWrap(True)
        cl.addWidget(body)
        cl.addSpacing(26)

        # Pills
        pill_row = QHBoxLayout()
        pill_row.setSpacing(10)
        for feat in ["Auto-detect name", "Month & year", "Employee ID"]:
            p = QFrame()
            p.setObjectName("pill")
            pl = QHBoxLayout(p)
            pl.setContentsMargins(10, 7, 12, 7)
            pl.setSpacing(7)
            dot = QLabel("●")
            dot.setObjectName("pillDot")
            txt = QLabel(feat)
            txt.setObjectName("pillTxt")
            pl.addWidget(dot)
            pl.addWidget(txt)
            pill_row.addWidget(p)
        pill_row.addStretch()
        cl.addLayout(pill_row)
        cl.addSpacing(34)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(255,255,255,0.07);")
        cl.addWidget(div)
        cl.addSpacing(30)

        # Button
        btn_row = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Master PDF  →")
        self.upload_btn.setObjectName("uploadBtn")
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.setFixedHeight(52)
        self.upload_btn.setFixedWidth(220)
        self.upload_btn.clicked.connect(self.handle_upload_and_process)
        btn_row.addWidget(self.upload_btn)
        btn_row.addStretch()
        cl.addLayout(btn_row)
        cl.addSpacing(18)

        # Status
        self.status_label = QLabel("Ready to process")
        self.status_label.setObjectName("statusIdle")
        cl.addWidget(self.status_label)

        ch.addWidget(card)
        ch.addStretch()
        root.addLayout(ch)
        root.addStretch()

        # ── Footer ───────────────────────────────────────────────────
        fl = QHBoxLayout()
        fl.setContentsMargins(48, 14, 48, 18)
        fl.addStretch()
        self.close_btn = QPushButton("Exit")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        fl.addWidget(self.close_btn)
        root.addLayout(fl)

        # Timer for dots
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def resizeEvent(self, event):
        self.bg.setGeometry(self.rect())
        super().resizeEvent(event)

    def _tick(self):
        self._dot_count = (self._dot_count + 1) % 4
        self.status_label.setText("Processing" + "." * self._dot_count)

    def _set_status(self, obj, text):
        self.status_label.setObjectName(obj)
        self.status_label.setText(text)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def handle_upload_and_process(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Master Payslip PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self._timer.start(380)
            self._set_status("statusBusy", "Processing")
            self.upload_btn.setEnabled(False)
            QApplication.processEvents()

            dl = os.path.join(os.path.expanduser("~"), "Downloads")
            save = os.path.join(dl, "Separate Payslips.zip")
            c = 1
            while os.path.exists(save):
                save = os.path.join(dl, f"Separate Payslips ({c}).zip")
                c += 1

            tmp = tempfile.mkdtemp()
            split_payslip_pdf(path, tmp)
            create_zip(tmp, save)

            self._timer.stop()
            self._set_status("statusOk", "✓  Done — check your Downloads folder")
        except Exception as e:
            self._timer.stop()
            self._set_status("statusErr", f"Error: {str(e)[:60]}")
        finally:
            self.upload_btn.setEnabled(True)


def start_gui():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = PayslipSplitter()
    w.show()
    sys.exit(app.exec())