"""Root entrypoint for Enterprise AI Agent."""
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.main import main

if __name__ == "__main__":
    main()
