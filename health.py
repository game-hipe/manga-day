import sys
import urllib.request

from src.core import config

PORT = config.api.backend_port

try:
    urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=5)
    sys.exit(0)
except Exception:
    sys.exit(1)
