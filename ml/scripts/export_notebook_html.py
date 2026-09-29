"""Export executed notebooks to HTML under reports/pdf/notebooks_html/."""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbconvert import HTMLExporter

ML_ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ML_ROOT / "notebooks"
OUT_DIR = ML_ROOT / "reports" / "pdf" / "notebooks_html"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exporter = HTMLExporter()
    exporter.exclude_input_prompt = True
    for path in sorted(NB_DIR.glob("*.ipynb")):
        nb = nbformat.read(path, as_version=4)
        body, _ = exporter.from_notebook_node(nb)
        out = OUT_DIR / f"{path.stem}.html"
        out.write_text(body, encoding="utf-8")
        print("wrote", out)


if __name__ == "__main__":
    main()
