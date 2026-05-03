import fitz
import requests
import os
import tempfile
from docx2pdf import convert
from docx import Document

def convert_docx_to_pdf(docx_path: str) -> str:
    """Konversi docx ke pdf sementara untuk dirender oleh PyMuPDF."""
    try:
        temp_dir = tempfile.gettempdir()
        base_name = os.path.basename(docx_path)
        pdf_name = os.path.splitext(base_name)[0] + "_temp.pdf"
        temp_pdf_path = os.path.join(temp_dir, pdf_name)
        
        # docx2pdf requires absolute paths and word installed
        convert(os.path.abspath(docx_path), os.path.abspath(temp_pdf_path))
        return temp_pdf_path
    except Exception as e:
        print(f"Error converting docx to pdf: {e}")
        return ""

def save_text_to_docx(text: str, file_path: str):
    """Simpan teks ke file Word (.docx)."""
    try:
        doc = Document()
        for line in text.split('\n'):
            doc.add_paragraph(line)
        doc.save(file_path)
        return True
    except Exception as e:
        print(f"Error saving docx: {e}")
        return False

def extract_text_from_pdf_page(file_path: str, page_num: int) -> str:
    """Ekstrak teks dari satu halaman PDF/Gambar tertentu."""
    try:
        doc = fitz.open(file_path)
        if 0 <= page_num < len(doc):
            page = doc.load_page(page_num)
            return page.get_text()
        return ""
    except Exception as e:
        print(f'Error extracting text: {e}')
        return ''

def get_pdf_page_image(file_path: str, page_num: int, zoom: float = 2.0):
    """Merender halaman PDF/Gambar menjadi gambar (bytes) dan dimensi."""
    try:
        doc = fitz.open(file_path)
        if 0 <= page_num < len(doc):
            page = doc.load_page(page_num)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            return pix.tobytes("ppm"), pix.width, pix.height
        return None, 0, 0
    except Exception as e:
        print(f'Error rendering page: {e}')
        return None, 0, 0

def correct_text_with_groq(text: str, api_key: str) -> str:
    """Koreksi teks dengan Groq API menggunakan model Llama terbaru."""
    if not text.strip():
        return "Tidak ada teks untuk dikoreksi."
    if not api_key.strip():
        return "API Key belum diisi."
        
    try:
        url = 'https://api.groq.com/openai/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'llama-3.3-70b-versatile',
            'messages': [
                {'role': 'system', 'content': 'Anda adalah asisten editor dokumen profesional. Tugas Anda adalah memperbaiki tata bahasa, ejaan (typo), tanda baca, dan struktur kalimat pada teks berikut agar menjadi bahasa Indonesia yang baku, rapi, dan mudah dibaca, TANPA mengubah makna aslinya. Hanya kembalikan teks hasil perbaikannya saja tanpa komentar tambahan.'},
                {'role': 'user', 'content': text}
            ],
            'max_tokens': 2048,
            'temperature': 0.3
        }
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()
        
        if response.status_code == 200:
            return response_json['choices'][0]['message']['content']
        else:
            return f"Error dari Groq API: {response_json.get('error', {}).get('message', 'Unknown error')}"
            
    except Exception as e:
        print(f'Error: {e}')
        return f"Terjadi kesalahan saat memanggil API: {e}"

def get_pdf_page_count(file_path: str) -> int:
    try:
        doc = fitz.open(file_path)
        return len(doc)
    except:
        return 0