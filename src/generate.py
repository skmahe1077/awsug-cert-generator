from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Any, List

import yaml

from src.utils import read_csv, ensure_dir
from src.pdf import draw_certificate, CertificateTheme


def repo_root() -> Path:
    # .../awsug-trichy-certificate-generator/src/generate.py -> repo root is parent of src
    return Path(__file__).resolve().parents[1]


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def get_field(row: Dict[str, str], key: str, default: str = "") -> str:
    return (row.get(key) or default).strip()


def normalize_safe_filename(name: str) -> str:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in (" ", "-", "_")).strip()
    return safe.replace(" ", "_")


def make_cert_id(prefix: str, year_month: str, number: int, width: int) -> str:
    # AWSUGTRY-2026-02-001
    return f"{prefix}-{year_month}-{number:0{width}d}"


def resolve_from_root(root: Path, p: str | Path) -> Path:
    pp = Path(p)
    return pp if pp.is_absolute() else (root / pp).resolve()


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate AWS User Group participation certificates (PDF).")
    ap.add_argument("--csv", required=True, help="Path to participants.csv (relative paths allowed)")
    ap.add_argument("--config", required=True, help="Path to certificate.yml (relative paths allowed)")
    ap.add_argument("--verbose", action="store_true", help="Print detailed logs")
    args = ap.parse_args()

    root = repo_root()

    cfg_path = resolve_from_root(root, args.config)
    csv_path = resolve_from_root(root, args.csv)

    cfg = load_config(cfg_path)

    group_name = cfg.get("group_name", "AWS User Group")

    # Theme
    theme_cfg = cfg.get("certificate", {}) or {}
    theme = CertificateTheme(
        page_size=theme_cfg.get("page_size", "A4"),
        orientation=theme_cfg.get("orientation", "landscape"),
        title=theme_cfg.get("title", "Certificate of Participation"),
        subtitle=theme_cfg.get("subtitle", "This certificate acknowledges participation in an AWS User Group Community-led Event"),
        footer_note=theme_cfg.get("footer_note", "Community-led. Not an official AWS certification."),
        id_label=theme_cfg.get("id_label", "Member ID"),
        font_name=theme_cfg.get("font_name", "Helvetica"),
        font_name_bold=theme_cfg.get("font_name_bold", "Helvetica-Bold"),
        name_font_size=int(theme_cfg.get("name_font_size", 38)),
        body_font_size=int(theme_cfg.get("body_font_size", 14)),
    )

    defaults = cfg.get("event_defaults", {}) or {}
    assets = cfg.get("assets", {}) or {}
    out_cfg = cfg.get("output", {}) or {}

    # NEW: Style + watermark configs
    style_cfg = cfg.get("style", {}) or {}
    watermark_cfg = cfg.get("watermark", {}) or {}

    # ID format
    id_cfg = cfg.get("id_format", {}) or {}
    id_prefix = str(id_cfg.get("prefix", "AWSUGTRY")).strip() or "AWSUGTRY"
    year_month = str(id_cfg.get("year_month", "2026-02")).strip() or "2026-02"
    start = int(id_cfg.get("start", 1))
    width = int(id_cfg.get("width", 3))

    # Output directory
    pdf_dir = resolve_from_root(root, out_cfg.get("pdf_dir", "output/pdfs"))
    ensure_dir(pdf_dir)

    rows: List[Dict[str, str]] = read_csv(csv_path)

    print("Repo root:       ", root)
    print("Config used:     ", cfg_path)
    print("CSV used:        ", csv_path)
    print("PDF output dir:  ", pdf_dir)
    print("Rows in CSV:     ", len(rows))

    seq = start
    created = 0

    for i, row in enumerate(rows, start=1):
        full_name = get_field(row, "full_name")
        if not full_name:
            raise ValueError(f"Row {i}: missing 'full_name'")

        certificate_id = get_field(row, "certificate_id")
        if not certificate_id:
            certificate_id = make_cert_id(id_prefix, year_month, seq, width)
            seq += 1

        event_title = get_field(row, "event_title", defaults.get("event_title", "AWS User Group Meetup"))
        event_date = get_field(row, "event_date", defaults.get("event_date", ""))
        location = get_field(row, "location", defaults.get("location", "Tiruchirappalli, Tamil Nadu"))

        safe_name = normalize_safe_filename(full_name)
        out_pdf = (pdf_dir / f"{certificate_id}-{safe_name}.pdf").resolve()

        if args.verbose:
            print(f"Writing ({i}): {out_pdf}")

        draw_certificate(
            out_pdf=out_pdf,
            theme=theme,
            group_name=group_name,
            participant_name=full_name,
            event_title=event_title,
            event_date=event_date,
            location=location,
            certificate_id=certificate_id,
            left_logo_path=resolve_from_root(root, assets.get("left_logo", "assets/logos/awsug_trichy.png")),
            right_logo_path=resolve_from_root(root, assets.get("right_logo", "assets/logos/aws_logo.png")),
            signature_1_path=resolve_from_root(root, assets.get("signature_1", "assets/signatures/organizer_1.png")),
            # NEW: pass styling controls
            style=style_cfg,
            watermark=watermark_cfg,
        )

        created += 1

    print(f"✅ Generated {created} PDFs in: {pdf_dir}")
    print(f"Certificate ID format: {id_prefix}-{year_month}-{'0'*width} (starting at {start})")


if __name__ == "__main__":
    main()
