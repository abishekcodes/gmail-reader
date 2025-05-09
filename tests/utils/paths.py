from pathlib import Path
import os

EMAIL_FILE = Path(os.environ['PY_EMAIL_FILE_PATH'])
RULES_FILE = EMAIL_FILE.parent / Path('rules.json')
