import os
import sys
import urllib.request

PORT = os.environ.get("PORT", 3040)

try:
    urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=5)
    sys.exit(0)
except Exception:
    sys.exit(1)
