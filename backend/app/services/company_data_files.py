from __future__ import annotations

from pathlib import Path

RESOURCES_DIR = Path(__file__).resolve().parents[1] / "resources"
COMPANY_DATA_DIR = RESOURCES_DIR / "company_data"
DEMO_REGISTRY_PATH = COMPANY_DATA_DIR / "company_registry_demo.json"
DEFAULT_COMPANY_IMPORT_CSV_PATH = COMPANY_DATA_DIR / "export-base_demo_takbup.csv"
