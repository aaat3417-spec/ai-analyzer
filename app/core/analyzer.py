import re
import math
import hashlib
from collections import Counter


def calculate_entropy(text: str) -> float:
    if not text:
        return 0.0

    freq = Counter(text)
    length = len(text)

    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def find_patterns(text: str):
    return {
        "emails": re.findall(r"\S+@\S+\.\S+", text),
        "urls": re.findall(r"https?://\S+", text),
        "ips": re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    }


class Analyzer:
    async def run(self, text: str):
        patterns = find_patterns(text)
        entropy = calculate_entropy(text)

        return {
            "patterns": patterns,
            "entropy": round(entropy, 3),
            "length": len(text),
            "fingerprint": fingerprint(text)
        }


analyzer = Analyzer()
