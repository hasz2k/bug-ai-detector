from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,64}")
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
CSV_HEADER = ["Timestamp", "Label", "Confidence", "Top", "Left", "Width", "Height"]
BBOX_KEYS = ("top", "left", "width", "height")

PDF_TABLE_HEADER = ["Label", "Confidence", "Position (Top, Left)"]
PDF_COLUMN_RATIOS = (0.42, 0.21, 0.37)

Detection = dict[str, Any]


def _report_path(session_id: str, extension: str, reports_dir: Path) -> Path:
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError(
            "session_id może zawierać tylko litery, cyfry, '-' i '_' (maks. 64 znaki)"
        )
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir / f"report_{session_id}.{extension}"


def _csv_safe(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(CSV_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def generate_csv_report(
    session_id: str,
    detections: list[Detection],
    reports_dir: Path = REPORTS_DIR,
) -> Path:
    path = _report_path(session_id, "csv", reports_dir)
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)
        for det in detections:
            bbox = det.get("bbox", {})
            row = [
                timestamp,
                det.get("label", ""),
                det.get("confidence", 0.0),
                *(bbox.get(key, "") for key in BBOX_KEYS),
            ]
            writer.writerow([_csv_safe(value) for value in row])

    return path


def _build_detections_table(detections: list[Detection], available_width: float) -> Table:
    rows = [PDF_TABLE_HEADER]
    for det in detections:
        bbox = det.get("bbox", {})
        rows.append([
            det.get("label", "Unknown"),
            f"{det.get('confidence', 0):.0%}",
            f"{bbox.get('top', '0%')}, {bbox.get('left', '0%')}",
        ])
    if not detections:
        rows.append(["No detections", "", ""])

    column_widths = [available_width * ratio for ratio in PDF_COLUMN_RATIOS]
    table = Table(rows, colWidths=column_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    return table


def generate_pdf_report(
    session_id: str,
    target_url: str,
    detections: list[Detection],
    reports_dir: Path = REPORTS_DIR,
) -> Path:
    path = _report_path(session_id, "pdf", reports_dir)
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=12,
    )

    metadata = [
        ("Session ID", session_id),
        ("Target URL", target_url),
        ("Date", datetime.now().strftime(TIMESTAMP_FORMAT)),
    ]

    story: list[Any] = [Paragraph("Bug AI Detector — Executive Report", title_style)]
    story.extend(
        Paragraph(f"<b>{name}:</b> {escape(value)}", styles["Normal"])
        for name, value in metadata
    )
    story.append(Spacer(1, 16))
    story.append(_build_detections_table(detections, doc.width))

    doc.build(story)
    return path
