import random
import string
import re
import math
import hashlib
from collections import Counter

from fastapi import FastAPI, UploadFile, File
import fitz  # PyMuPDF

app = FastAPI()

# ==============================
# 🧠 PDF ANALYZER
# ==============================

def calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    freq = Counter(text)
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def read_pdf(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except:
        return ""


@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    content = await file.read()
    text = read_pdf(content)

    emails = re.findall(r"\S+@\S+\.\S+", text)
    urls = re.findall(r"https?://\S+", text)
    ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)

    entropy = calculate_entropy(text)
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
