"""Map helpers for district priority."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from fra_dss.config import FIGURES_DIR, ensure_dirs


def save_priority_map_html(rows: list[dict], path: Path | None = None) -> Path:
    ensure_dirs()
    path = path or (FIGURES_DIR / "30_district_priority_map.html")
    try:
        import folium

        m = folium.Map(location=[22.5, 80.0], zoom_start=5)
        for r in rows:
            if r.get("latitude") is None or r.get("longitude") is None:
                continue
            folium.CircleMarker(
                location=[r["latitude"], r["longitude"]],
                radius=6,
                popup=f"{r['district']}: {r.get('priority_score')}",
                color="#0072B2",
                fill=True,
            ).add_to(m)
        m.save(str(path))
    except Exception:
        path.write_text("<html><body>Map unavailable</body></html>", encoding="utf-8")
    return path
