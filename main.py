import os
import re
import math
import hashlib
import asyncio
import logging
import httpx

from collections import Counter
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ==============================
# 🧠 UTILS
# ==============================

def calculate_entropy(text: str) -> float:
    if not text:
        return 0
    freq = Counter(text)
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


# ==============================
# 🔍 ENGINES
# ==============================

class SecretEngine:
    name = "secrets"

    PATTERNS = [
        r"AKIA[0-9A-Z]{16}",
        r"ghp_[A-Za-z0-9]{36}",
        r"sk_live_[0-9a-zA-Z]{24}",
    ]

    def run(self, text: str):
        found = []

        for pattern in self.PATTERNS:
            found.extend(re.findall(pattern, text))

        tokens = re.findall(r"[A-Za-z0-9_\-]{20,}", text)
        strong = [t for t in tokens if calculate_entropy(t) > 4.5]

        found.extend(strong)
        return list(set(found))


class PatternEngine:
    name = "patterns"

    def run(self, text):
        return {
            "emails": re.findall(r"\S+@\S+\.\S+", text),
            "urls": re.findall(r"https?://\S+", text),
            "ips": re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
        }


class EntropyEngine:
    name = "entropy"

    def run(self, text):
        return {
            "entropy": round(calculate_entropy(text), 3),
            "length": len(text)
        }


class FileTypeEngine:
    name = "file_type"

    def run(self, text):
        if text.startswith("%PDF"):
            return "PDF"
        if text.startswith("{"):
            return "JSON"
        return "Unknown"


class PasswordEngine:
    name = "password"

    def analyze(self, password: str):
        score = 0

        if len(password) >= 8:
            score += 1
        if re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"[a-z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1
        if re.search(r"[!@#$%^&*]", password):
            score += 1

        levels = ["weak", "normal", "good", "strong", "insane"]

        return {
            "score": score,
            "level": levels[min(score, 4)]
        }

    def generate(self):
        words = ["Falcon", "Shadow", "Titan", "Nova", "Storm"]
        return f"{words[os.urandom(1)[0] % len(words)]}{os.urandom(1)[0]}!"


# ==============================
# ⚡ ANALYZER
# ==============================

class Analyzer:
    def __init__(self):
        self.engines = [
            SecretEngine(),
            PatternEngine(),
            EntropyEngine(),
            FileTypeEngine()
        ]
        self.password_engine = PasswordEngine()

    async def run(self, text):
        output = {}

        for e in self.engines:
            output[e.name] = e.run(text)

        score = (
            len(output["secrets"]) * 30 +
            len(output["patterns"]["emails"]) * 5 +
            output["entropy"]["entropy"] * 5
        )

        output["meta"] = {
            "risk_score": int(score),
            "risk_level": (
                "CRITICAL" if score > 80 else
                "HIGH" if score > 50 else
                "MEDIUM" if score > 25 else
                "LOW"
            ),
            "fingerprint": fingerprint(text)
        }

        return output


analyzer = Analyzer()

# ==============================
# 📂 PDF READER
# ==============================

def read_pdf(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return str(e)


# ==============================
# 🌐 API
# ==============================

@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    content = await file.read()
    text = read_pdf(content)

    result = await analyzer.run(text)

    return {
        "success": True,
        "analysis": result
    }


@app.get("/password/generate")
def generate_password():
    return {
        "password": analyzer.password_engine.generate()
    }


@app.get("/password/check")
def check_password(password: str):
    return analyzer.password_engine.analyze(password)


@app.get("/health")
def health():
    return {"status": "running"}


# ==============================
# 🚀 RUN
# ==============================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
