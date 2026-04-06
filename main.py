import os
import re
import math
import hashlib
import asyncio
import logging
import httpx

from collections import Counter
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTLMResponse
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
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>AI Analyzer</title>
        <style>
            body {
                background: #0f172a;
                color: white;
                font-family: Arial;
                text-align: center;
                padding: 50px;
            }
            h1 { font-size: 50px; }
            .box {
                margin-top: 40px;
                padding: 30px;
                background: #1e293b;
                border-radius: 12px;
                display: inline-block;
            }
            button {
                margin-top: 20px;
                padding: 10px 20px;
                background: #22c55e;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }
            pre {
                background: #020617;
                padding: 20px;
                margin-top: 30px;
                border-radius: 10px;
                text-align: left;
            }
        </style>
    </head>

    <body>
        <h1>🚀 AI Analyzer</h1>
        <p>Upload PDF and analyze</p>

        <div class="box">
            <input type="file" id="fileInput"><br>
            <button onclick="uploadFile()">Analyze</button>
        </div>

        <pre id="result"></pre>

        <script>
            async function uploadFile() {
                const fileInput = document.getElementById("fileInput");
                const result = document.getElementById("result");

                if (!fileInput.files.length) {
                    alert("اختر ملف");
                    return;
                }

                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                result.innerText = "⏳ جاري التحليل...";

                const response = await fetch("/analyze", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();
                result.innerText = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    """


# ==============================
# 🚀 RUN
# ==============================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
