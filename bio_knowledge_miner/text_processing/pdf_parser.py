import os
import fitz  # PyMuPDF
from typing import List
from .. import config
from .ocr_handler import extract_text_from_pdf as ocr_extract_text

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    주어진 PDF 파일 경로에서 모든 텍스트를 추출합니다.

    Args:
        pdf_path (str): 텍스트를 추출할 PDF 파일의 경로.

    Returns:
        str: PDF에서 추출된 전체 텍스트.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return ""

    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            # OCR fallback per page if no text layer
            if not page_text.strip():
                try:
                    page_text = ocr_extract_text(pdf_path, dpi=300, lang="korean").split("\n")[page_num]
                except Exception as ocr_e:
                    print(f"[PDF Parser] OCR fallback failed on page {page_num}: {ocr_e}")
                    page_text = ""
            full_text += page_text
    
        doc.close()
        return full_text
    except Exception as e:
        print(f"Error processing PDF file {pdf_path}: {e}")
        return ""

def process_all_pdfs_in_directory() -> List[dict]:
    """
    config.PDF_PATH에 있는 모든 PDF 파일을 처리하여 텍스트를 추출합니다.

    Returns:
        List[dict]: 각 파일의 경로와 추출된 텍스트를 담은 딕셔너리 리스트.
    """
    pdf_dir = config.PDF_PATH
    extracted_data = []

    print(f"Scanning for PDF files in '{pdf_dir}'...")

    if not os.path.exists(pdf_dir) or not os.listdir(pdf_dir):
        print("No PDF files found in the directory. Please add some PDF files to test.")
        return extracted_data

    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(pdf_dir, filename)
            print(f"  - Processing: {filename}")
            text_content = extract_text_from_pdf(filepath)
            
            if text_content:
                extracted_data.append({
                    "filename": filename,
                    "filepath": filepath,
                    "content": text_content
                })
    
    print(f"Finished processing. Extracted text from {len(extracted_data)} PDF files.")
    return extracted_data

if __name__ == '__main__':
    # 이 파일을 직접 실행할 경우 테스트 코드
    print("--- Testing PDF Parser ---")
    
    # 테스트를 위해 'data/pdfs' 폴더를 생성하고,
    # 그 안에 샘플 PDF 파일을 넣어주세요. (예: sample.pdf)
    # os.makedirs(config.PDF_PATH, exist_ok=True) # config.py에서 이미 처리
    
    results = process_all_pdfs_in_directory()
    
    if results:
        print("\n--- Sample of extracted text ---")
        # 첫 번째로 처리된 파일의 내용 일부만 출력
        sample_result = results[0]
        print(f"File: {sample_result['filename']}")
        print(f"Extracted Text (first 300 chars): \n{sample_result['content'][:300]}...") 