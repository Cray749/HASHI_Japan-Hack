"""Try the translation model through the running server: python scripts/try_translate.py
Prints a few translations in both directions so you can see the model is working."""
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")
CASES = [
    ("hi", "en", "नमस्ते, आप कैसे हैं?"),
    ("hi", "ja", "मुझे पानी चाहिए"),
    ("ta", "ja", "எனக்கு தண்ணீர் வேண்டும்"),
    ("th", "ja", "ขอผ้าห่มหน่อย"),
    ("ja", "ta", "少々お待ちください"),
    ("ja", "hi", "お水をお持ちします"),
    ("en", "th", "Where is the toilet?"),
    ("en", "km", "I need a doctor"),
]
for src, tgt, text in CASES:
    t = time.time()
    r = requests.post("http://127.0.0.1:8000/api/translate", json={"text": text, "src": src, "tgt": tgt}, timeout=600)
    print(f"{src}->{tgt} ({time.time() - t:.1f}s): {text}  =>  {r.json().get('text', r.text)}")
