"""
Test runner for executing pytest tests in the Pythonista iOS app.
"""

from pathlib import Path

import pytest


pytest.main([
    "-p", "no:faulthandler",
    "-rfE",
    "--disable-warnings", 
    str(Path(__file__).parent / "test")
])

