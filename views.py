import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QLineEdit, QTextEdit, QSplitter, 
    QSizePolicy, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont, QPdfWriter
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from utils import (
    get_pdf_page_image, extract_text_from_pdf_page, 
    correct_text_with_groq, get_pdf_page_count,
    convert_docx_to_pdf, save_text_to_docx
)

class CorrectionThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, text, api_key):
        super().__init__()
        self.text = text
        self.api_key = api_key

    def run(self):
        corrected = correct_text_with_groq(self.text, self.api_key)
        self.finished_signal.emit(corrected)

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update_pixmap()

    def update_pixmap(self):
        if self._pixmap and not self._pixmap.isNull():
            scaled_pixmap = self._pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled_pixmap)
        else:
            super().setPixmap(QPixmap())

    def resizeEvent(self, event):
        self.update_pixmap()
        super().resizeEvent(event)

class DigitalBookWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.original_path = None
        self.render_path = None # For docx, this will be the temp pdf
        self.total_pages = 0
        self.current_left_page = 0
        self.view_mode = 2 # 1 = single page, 2 = double page
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Digital Book - AI Document Editor')
        self.setGeometry(100, 100, 1280, 800)
        
        # Cyberpunk / Dark Mode Style
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #1F1F1F;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px 16px;
                color: #00FFCC;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333333;
                border: 1px solid #00FFCC;
            }
            QPushButton:pressed {
                background-color: #00FFCC;
                color: #121212;
            }
            QPushButton:disabled {
                color: #555555;
                border: 1px solid #222222;
                background-color: #1A1A1A;
            }
            QLineEdit, QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
                color: #FFF;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #00FFCC;
            }
            QLabel {
                font-size: 14px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- Top Bar ---
        top_bar = QHBoxLayout()
        self.btn_open = QPushButton("📂 Buka File")
        self.btn_open.clicked.connect(self.open_file)
        top_bar.addWidget(self.btn_open)
        
        self.btn_view_mode = QPushButton("📖 Mode: 2 Halaman")
        self.btn_view_mode.clicked.connect(self.toggle_view_mode)
        top_bar.addWidget(self.btn_view_mode)
        
        self.lbl_file = QLabel("Belum ada file terpilih")
        self.lbl_file.setStyleSheet("color: #888; font-style: italic;")
        top_bar.addWidget(self.lbl_file)
        
        top_bar.addStretch()
        
        lbl_api = QLabel("🔑 Groq API Key:")
        self.input_api = QLineEdit()
        self.input_api.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api.setPlaceholderText("gsk_...")
        self.input_api.setFixedWidth(200)
        
        self.btn_save_api = QPushButton("💾 Simpan")
        self.btn_save_api.setStyleSheet("padding: 6px 12px; font-size: 12px;")
        self.btn_save_api.clicked.connect(self.save_api_key)
        
        top_bar.addWidget(lbl_api)
        top_bar.addWidget(self.input_api)
        top_bar.addWidget(self.btn_save_api)
        
        main_layout.addLayout(top_bar)
        
        # --- Main Splitter ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Book View (Left)
        book_widget = QWidget()
        book_layout = QVBoxLayout(book_widget)
        book_layout.setContentsMargins(0, 15, 0, 0)
        
        pages_layout = QHBoxLayout()
        pages_layout.setSpacing(10)
        
        self.lbl_page_left = ImageLabel()
        self.lbl_page_left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lbl_page_left.setStyleSheet("background-color: transparent;")
        
        self.lbl_page_right = ImageLabel()
        self.lbl_page_right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lbl_page_right.setStyleSheet("background-color: transparent;")
        
        pages_layout.addWidget(self.lbl_page_left)
        pages_layout.addWidget(self.lbl_page_right)
        
        book_layout.addLayout(pages_layout)
        
        # Navigation
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 15, 0, 0)
        self.btn_prev = QPushButton("◄ Sebelumnya")
        self.btn_prev.clicked.connect(self.prev_page)
        
        self.lbl_page_info = QLabel("Halaman: 0 / 0")
        self.lbl_page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_page_info.setStyleSheet("font-weight: bold; color: #FFF;")
        
        self.btn_next = QPushButton("Selanjutnya ►")
        self.btn_next.clicked.connect(self.next_page)
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_page_info)
        nav_layout.addWidget(self.btn_next)
        book_layout.addLayout(nav_layout)
        
        splitter.addWidget(book_widget)
        
        # Sidebar for AI Editor (Right)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 15, 0, 0)
        
        ai_title = QLabel("🤖 AI Editor & Koreksi")
        ai_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FFCC; margin-bottom: 10px;")
        sidebar_layout.addWidget(ai_title)
        
        btns_layout = QHBoxLayout()
        self.btn_sum_left = QPushButton("Koreksi Kiri")
        self.btn_sum_left.clicked.connect(lambda: self.correct_page(self.current_left_page))
        self.btn_sum_right = QPushButton("Koreksi Kanan")
        self.btn_sum_right.clicked.connect(lambda: self.correct_page(self.current_left_page + 1))
        
        btns_layout.addWidget(self.btn_sum_left)
        btns_layout.addWidget(self.btn_sum_right)
        sidebar_layout.addLayout(btns_layout)
        
        self.txt_editor = QTextEdit()
        # Set to False so user can do CRUD manually
        self.txt_editor.setReadOnly(False)
        self.txt_editor.setPlaceholderText("Teks akan diekstrak ke sini. Anda dapat mengetik, mengedit, atau menghapus teks di area ini secara manual...")
        self.txt_editor.setStyleSheet("margin-top: 10px; font-size: 15px; line-height: 1.5;")
        sidebar_layout.addWidget(self.txt_editor)
        
        self.btn_save = QPushButton("💾 Simpan Ke... (Save As)")
        self.btn_save.setStyleSheet("background-color: #2E7D32; color: #FFF; border-color: #1B5E20; margin-top: 10px;")
        self.btn_save.clicked.connect(self.save_as)
        sidebar_layout.addWidget(self.btn_save)
        
        splitter.addWidget(sidebar)
        
        # Set splitter sizes
        splitter.setSizes([900, 350])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
        self.load_api_key()
        self.update_ui_state()

    def load_api_key(self):
        try:
            if os.path.exists("config.json"):
                import json
                with open("config.json", "r") as f:
                    config = json.load(f)
                    key = config.get("groq_api_key", "")
                    if key:
                        self.input_api.setText(key)
        except Exception:
            pass

    def save_api_key(self):
        import json
        key = self.input_api.text().strip()
        try:
            with open("config.json", "w") as f:
                json.dump({"groq_api_key": key}, f)
            QMessageBox.information(self, "Sukses", "API Key berhasil disimpan di sistem!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal menyimpan API Key: {e}")

    def update_ui_state(self):
        has_file = self.render_path is not None
        self.btn_prev.setEnabled(has_file and self.current_left_page > 0)
        if self.view_mode == 2:
            self.btn_next.setEnabled(has_file and (self.current_left_page + 2) < self.total_pages)
        else:
            self.btn_next.setEnabled(has_file and (self.current_left_page + 1) < self.total_pages)
        self.btn_save.setEnabled(True) # Can save empty or edited text anytime
        
    def toggle_view_mode(self):
        if self.view_mode == 2:
            self.view_mode = 1
            self.btn_view_mode.setText("📄 Mode: 1 Halaman")
            self.lbl_page_right.setVisible(False)
            self.btn_sum_right.setVisible(False)
        else:
            self.view_mode = 2
            self.btn_view_mode.setText("📖 Mode: 2 Halaman")
            self.lbl_page_right.setVisible(True)
            self.btn_sum_right.setVisible(True)
        self.render_pages()

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "Buka File", 
            "", 
            "Semua File (*.pdf *.docx *.png *.jpg *.jpeg);;PDF (*.pdf);;Word (*.docx);;Images (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.original_path = file_name
            self.lbl_file.setText(file_name.split('/')[-1])
            self.lbl_file.setStyleSheet("color: #00FFCC; font-weight: bold;")
            
            ext = os.path.splitext(file_name)[1].lower()
            
            if ext == '.docx':
                self.lbl_page_info.setText("Mengonversi Word ke tampilan buku... Mohon tunggu.")
                # Update UI to show message before blocking thread
                self.repaint()
                temp_pdf = convert_docx_to_pdf(file_name)
                if temp_pdf:
                    self.render_path = temp_pdf
                else:
                    QMessageBox.warning(self, "Error", "Gagal merender DOCX. Pastikan Microsoft Word terinstal.")
                    return
            else:
                self.render_path = file_name

            self.total_pages = get_pdf_page_count(self.render_path)
            self.current_left_page = 0
            self.render_pages()

    def render_pages(self):
        if not self.render_path: return
        
        if self.view_mode == 2:
            left_display = self.current_left_page + 1
            right_display = self.current_left_page + 2
            
            if right_display > self.total_pages:
                self.lbl_page_info.setText(f"Halaman: {left_display} / {self.total_pages}")
            else:
                self.lbl_page_info.setText(f"Halaman: {left_display}-{right_display} / {self.total_pages}")
            
            self._render_single_page(self.current_left_page, self.lbl_page_left)
            self._render_single_page(self.current_left_page + 1, self.lbl_page_right)
            self.btn_sum_left.setText("Koreksi Kiri")
        else:
            left_display = self.current_left_page + 1
            self.lbl_page_info.setText(f"Halaman: {left_display} / {self.total_pages}")
            self._render_single_page(self.current_left_page, self.lbl_page_left)
            self.lbl_page_right.clear()
            self.btn_sum_left.setText("Koreksi Halaman")
            
        self.update_ui_state()

    def _render_single_page(self, page_num, label):
        if page_num < self.total_pages:
            img_data, w, h = get_pdf_page_image(self.render_path, page_num, zoom=2.0)
            if img_data:
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                label.setPixmap(pixmap)
            else:
                label.clear()
        else:
            label.clear()

    def prev_page(self):
        step = self.view_mode
        if self.current_left_page >= step:
            self.current_left_page -= step
            self.render_pages()
        elif self.current_left_page > 0:
            self.current_left_page = 0
            self.render_pages()

    def next_page(self):
        step = self.view_mode
        if self.current_left_page + step < self.total_pages:
            self.current_left_page += step
            self.render_pages()

    def correct_page(self, page_num):
        if not self.render_path or page_num >= self.total_pages:
            self.txt_editor.setText("Halaman tidak tersedia.")
            return
            
        api_key = self.input_api.text()
        if not api_key:
            self.txt_editor.setText("Silakan masukkan Groq API Key di atas terlebih dahulu.")
            return

        self.txt_editor.setText(f"Mengekstrak teks dari halaman {page_num+1}...\n")
        text = extract_text_from_pdf_page(self.render_path, page_num)
        
        if not text.strip():
            self.txt_editor.setText("Halaman ini tidak memiliki teks yang bisa dikoreksi (mungkin berupa gambar tanpa teks).")
            return
            
        self.txt_editor.setText(f"--- Teks Asli ---\n{text}\n\nMemperbaiki teks menggunakan Groq AI (llama-3.3-70b-versatile)... Mohon tunggu.\n")
        
        self.thread = CorrectionThread(text, api_key)
        self.thread.finished_signal.connect(self.on_correction_finished)
        self.thread.start()

    def on_correction_finished(self, corrected_text):
        self.txt_editor.clear()
        self.txt_editor.setText(corrected_text)

    def save_as(self):
        text_to_save = self.txt_editor.toPlainText()
        if not text_to_save.strip():
            QMessageBox.warning(self, "Peringatan", "Tidak ada teks untuk disimpan!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan File Ke",
            "",
            "Word Files (*.docx);;PDF Files (*.pdf);;Text Files (*.txt)"
        )
        
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            try:
                if ext == '.docx':
                    success = save_text_to_docx(text_to_save, file_path)
                    if success:
                        QMessageBox.information(self, "Sukses", f"Berhasil disimpan ke:\n{file_path}")
                    else:
                        QMessageBox.critical(self, "Error", "Gagal menyimpan ke file Word.")
                elif ext == '.pdf':
                    writer = QPdfWriter(file_path)
                    self.txt_editor.document().print(writer)
                    QMessageBox.information(self, "Sukses", f"Berhasil disimpan ke:\n{file_path}")
                else: # .txt
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text_to_save)
                    QMessageBox.information(self, "Sukses", f"Berhasil disimpan ke:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan file:\n{e}")