from fastapi import APIRouter, UploadFile, File
from app.ocr.ocr_engine import OCREngine

router = APIRouter()

@router.post("/scan")
async def scan_invoice(
    file: UploadFile = File(...)
):
    """
    Accepts PO / supplier invoice image and extracts structured order details using OCR.
    """
    contents = await file.read()
    extracted_fields = OCREngine.extract_invoice_fields(file.filename, contents)
    return {
        "success": True,
        "filename": file.filename,
        "data": extracted_fields
    }
