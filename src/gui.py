import sys
import os
import tempfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, 
    QHBoxLayout, QFileDialog, QFrame
)
from PySide6.QtCore import Qt
from utils.pdf_utils import split_payslip_pdf
from utils.zip_utils import create_zip

class PayslipSplitter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultra Payslip Pro")
        self.showMaximized() 
        
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QFrame#card { background-color: #1e1e1e; border-radius: 15px; border: 1px solid #333; }
            QPushButton#uploadBtn { 
                background-color: #0078d4; border: none; border-radius: 8px; 
                padding: 20px 40px; font-weight: bold; font-size: 18px; 
            }
            QPushButton#uploadBtn:hover { background-color: #2b88d8; }
            QPushButton#closeBtn { background-color: transparent; color: #555; border: 1px solid #333; padding: 5px 15px; }
            QPushButton#closeBtn:hover { color: #ff4d4d; border-color: #ff4d4d; }
            QLabel#status { color: #00ff88; font-size: 14px; margin-top: 10px; }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.addStretch()

        h_layout = QHBoxLayout()
        h_layout.addStretch()

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setFixedWidth(500)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        self.title_label = QLabel("Payslip Processor")
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.title_label)

        self.info_label = QLabel("Select Master PDF. ZIP will save to Downloads.")
        self.info_label.setStyleSheet("color: #888; font-size: 14px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.info_label)

        self.upload_btn = QPushButton("📂 UPLOAD MASTER PDF")
        self.upload_btn.setObjectName("uploadBtn")
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.clicked.connect(self.handle_upload_and_process)
        card_layout.addWidget(self.upload_btn)

        self.status_label = QLabel("System Ready")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.status_label)
        
        h_layout.addWidget(self.card)
        h_layout.addStretch()
        outer_layout.addLayout(h_layout)
        outer_layout.addStretch()

        exit_layout = QHBoxLayout()
        exit_layout.addStretch()
        self.close_btn = QPushButton("Exit Application")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.clicked.connect(self.close)
        exit_layout.addWidget(self.close_btn)
        outer_layout.addLayout(exit_layout)

    def handle_upload_and_process(self):
        input_path, _ = QFileDialog.getOpenFileName(self, "Select Master Payslip", "", "PDF Files (*.pdf)")
        if not input_path:
            return

        try:
            self.status_label.setText("⚡ PROCESSING...")
            self.upload_btn.setEnabled(False)
            QApplication.processEvents()

            # 1. Logic to find the Downloads folder automatically (Works on Win/Linux)
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            save_path = os.path.join(downloads_path, "Separate Payslips.zip")

            # 2. Handle potential file name conflicts (Optional: adds (1), (2) if file exists)
            counter = 1
            original_save_path = save_path
            while os.path.exists(save_path):
                save_path = os.path.join(downloads_path, f"Separate Payslips ({counter}).zip")
                counter += 1

            # 3. Process
            temp_dir = tempfile.mkdtemp()
            split_payslip_pdf(input_path, temp_dir)
            create_zip(temp_dir, save_path)

            self.status_label.setText(f"✅ SUCCESS! Check your Downloads folder.")
            
        except Exception as e:
            self.status_label.setText(f"❌ ERROR: {str(e)}")
        finally:
            self.upload_btn.setEnabled(True)

def start_gui():
    app = QApplication(sys.argv)
    window = PayslipSplitter()
    window.show()
    sys.exit(app.exec())