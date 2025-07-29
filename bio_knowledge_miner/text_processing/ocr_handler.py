from __future__ import annotations

"""bio_knowledge_miner.text_processing.ocr_handler

이 모듈은 스캔 PDF나 이미지에서 텍스트를 추출하기 위한 OCR 유틸리티를 제공합니다.
PaddleOCR 모델을 lazily 로드하여 메모리 사용량을 최소화하며, 기존 `pdf_parser.extract_text_from_pdf`의
fallback 용도로 사용할 수 있습니다.

주요 기능
---------
1. `extract_text_from_image(path_or_pil)`
   - 이미지 파일 경로 또는 PIL.Image 를 받아 한글 포함 텍스트를 추출합니다.

2. `extract_text_from_pdf(pdf_path, dpi=300, lang='korean')`
   - PyMuPDF 를 사용해 각 페이지를 이미지로 렌더링한 뒤 OCR 을 수행합니다.
   - 페이지에 이미 텍스트 레이어가 존재하면 OCR 을 건너뜁니다.

사용 예
-------
>>> from bio_knowledge_miner.text_processing.ocr_handler import extract_text_from_pdf
>>> text = extract_text_from_pdf('sample_scanned.pdf')
"""

import io
import os
from typing import List, Optional, Union

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from tqdm import tqdm

# PaddleOCR 를 선택적으로 import – 가벼운 테스트 환경에서도 모듈 미존재 에러 방지
try:
    from paddleocr import PaddleOCR
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "PaddleOCR 가 설치되어 있지 않습니다. `pip install paddleocr paddlepaddle-gpu`(또는 cpu 버전) 를 실행하세요."
    ) from e

# ---------------------------------------------------------------------------
# 내부 싱글톤 – 모델은 한 번만 로드한다.
# ---------------------------------------------------------------------------

_ocr_instance: Optional["PaddleOCR"] = None


def _get_ocr(lang: str = "korean", use_gpu: bool | None = None) -> "PaddleOCR":
    """글로벌 PaddleOCR 인스턴스를 반환(필요 시 로드).

    Args:
        lang: 모델 언어(영어 only PDF 는 'en', 한국어는 'korean').
        use_gpu: None → 환경 자동 감지, True/False 로 강제 지정 가능.
    """
    global _ocr_instance

    if _ocr_instance is None:
        # GPU 사용 여부 자동 감지: GPU 환경 + paddlepaddle-gpu 설치 시 True
        if use_gpu is None:
            use_gpu = os.getenv("OCR_USE_GPU", "auto").lower() != "false"
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            use_gpu=use_gpu,
            show_log=False,
        )
    return _ocr_instance


# ---------------------------------------------------------------------------
# 공개 함수
# ---------------------------------------------------------------------------

def extract_text_from_image(image: Union[str, Image.Image], *, lang: str = "korean") -> str:
    """단일 이미지(경로 또는 PIL)에서 텍스트를 추출.

    Args:
        image: 이미지 파일 경로(str) 또는 PIL.Image.Image 객체.
        lang: PaddleOCR 언어 설정.

    Returns:
        추출된 텍스트(줄바꿈으로 구분).
    """
    ocr = _get_ocr(lang=lang)

    # PaddleOCR 는 파일 경로나 ndarray 를 입력으로 받음
    if isinstance(image, str):
        result = ocr.ocr(image, cls=True)
    else:
        # PIL.Image → ndarray(BGR)
        if image.mode != "RGB":
            image = image.convert("RGB")
        img_arr = np.array(image)[:, :, ::-1]  # RGB → BGR
        result = ocr.ocr(img_arr, cls=True)

    texts: List[str] = []
    for line in result:  # type: ignore[assignment]
        # PaddleOCR 2.x: list[list[Tuple, ((text, conf))]] 구조
        if isinstance(line, list):
            for seg in line:
                texts.append(seg[1][0])
        else:
            # 호환성 고려: (box, (text, conf)) 형태일 수도 있음
            texts.append(line[1][0])
    return "\n".join(texts)


def extract_text_from_pdf(pdf_path: str, *, dpi: int = 300, lang: str = "korean") -> str:
    """스캔 PDF 에서 텍스트를 추출.

    1) 페이지에 텍스트 레이어가 존재하면 해당 텍스트 사용.
    2) 비어있다면 이미지를 렌더링하여 OCR 수행.

    Args:
        pdf_path: 대상 PDF 파일 경로.
        dpi: 렌더링 해상도(Dots Per Inch).
        lang: PaddleOCR 언어 설정.

    Returns:
        전체 추출 텍스트.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"[OCR] PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    full_text_parts: List[str] = []

    for page_index in tqdm(range(len(doc)), desc="OCR", unit="page"):
        page = doc.load_page(page_index)
        # 1) 텍스트 레이어 우선 사용
        text = page.get_text().strip()
        if text:
            full_text_parts.append(text)
            continue

        # 2) OCR 수행
        # 페이지를 이미지로 렌더링
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_bytes))
        ocr_text = extract_text_from_image(pil_img, lang=lang)
        full_text_parts.append(ocr_text)

    doc.close()
    return "\n".join(full_text_parts) 