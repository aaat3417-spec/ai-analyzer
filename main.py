from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
import random
import string
import re
import math
import hashlib
from collections import Counter
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

    return {
        "emails": emails,
        "urls": urls,
        "ips": ips,
        "entropy": round(entropy, 3),
        "length": len(text),
        "fingerprint": fingerprint(text)
    }


# ==============================
# 🔐 PASSWORD SYSTEM
# ==============================

generated_passwords = set()

def similarity(a: str, b: str) -> float:
    same = sum(1 for x, y in zip(a, b) if x == y)
    return same / max(len(a), len(b))


@app.get("/generate-password")
def generate_password():
    length = 12
    chars = string.ascii_letters + string.digits + "!@#$%^&*"

    while True:
        password = "".join(random.choice(chars) for _ in range(length))

        is_valid = True
        for old in generated_passwords:
            if similarity(password, old) > 0.2:
                is_valid = False
                break

        if is_valid:
            generated_passwords.add(password)
            return {"password": password}


@app.get("/password-check")
def check_password(password: str):
    score = 0

    if len(password) >= 8:
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*" for c in password):
        score += 1

    if score <= 2:
        strength = "weak"
    elif score == 3:
        strength = "medium"
    else:
        strength = "strong"

    return {"strength": strength}


# ==============================
# 🌐 FRONTEND
# ==============================

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
