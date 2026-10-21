import json
from pathlib import Path


# region best-valid
def valid_best(value):
    return type(value) is int and 0 <= value <= 9007199254740991
# endregion


# region best-load
def load_best(path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8')).get('best')
        return value if valid_best(value) else 0
    except (OSError, ValueError, AttributeError):
        return 0
# endregion


# region best-save
def save_best(path, value):
    if not valid_best(value):
        return False
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    try:
        temporary.write_text(json.dumps({'best': value}) + '\n', encoding='utf-8')
        temporary.replace(path)
        return True
    except OSError:
        return False
# endregion
