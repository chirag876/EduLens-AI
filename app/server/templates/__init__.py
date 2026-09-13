from pathlib import Path


TEMPLATE_PATH = Path(__file__).parent / "system_prompt.txt"


def load_prompt_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")