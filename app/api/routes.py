from fastapi import APIRouter, UploadFile, File
from app.core.analyzer import analyzer
from app.core.pdf_reader import read_pdf

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "running"}


@router.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    content = await file.read()
    text = read_pdf(content)
    result = await analyzer.run(text)

    return {"success": True, "analysis": result}
