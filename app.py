from __future__ import annotations

import io
import sys
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, send_file, flash, redirect, url_for

# Ensure project root is on sys.path so `src` package is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.pdf import draw_certificate, CertificateTheme
from src.utils import read_csv
from src.generate import make_cert_id, normalize_safe_filename, get_field

REPO_ROOT = Path(__file__).parent

app = Flask(__name__)
app.secret_key = "awsug-cert-gen-secret-2026"

ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_CSV_EXTS = {".csv"}

SAMPLE_CSV = (
    "name,member_id,role\n"
    "Mahendran,MEM001,participant\n"
    "Idhazhini,MEM002,speaker\n"
    "Arun,MEM003,participant\n"
)


def _allowed(filename: str, allowed: set[str]) -> bool:
    return Path(filename).suffix.lower() in allowed


def _save_upload(file_storage, dest: Path) -> bool:
    """Save a FileStorage to dest. Returns True on success."""
    try:
        file_storage.save(str(dest))
        return True
    except Exception:
        return False


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/sample-csv")
def sample_csv():
    buf = io.BytesIO(SAMPLE_CSV.encode("utf-8"))
    return send_file(
        buf,
        mimetype="text/csv",
        as_attachment=True,
        download_name="participants_sample.csv",
    )


@app.route("/generate", methods=["POST"])
def generate():
    # ── Form fields ──────────────────────────────────────────────────────────
    group_name = (request.form.get("group_name") or "AWS User Group").strip()
    event_title = (request.form.get("event_title") or "AWSUG Meetup").strip()
    event_date = (request.form.get("event_date") or "").strip()
    location = (request.form.get("location") or "").strip()
    id_prefix = "AWSUGTRY"
    output_format = request.form.get("output_format", "pdf").strip().lower()  # "pdf" or "image"

    # ── Uploaded files ────────────────────────────────────────────────────────
    csv_file = request.files.get("csv_file")
    left_logo_file = request.files.get("left_logo")
    signature_file = request.files.get("signature")

    # CSV is required
    if not csv_file or not csv_file.filename:
        flash("Please upload a participants CSV file.", "danger")
        return redirect(url_for("index"))

    if not _allowed(csv_file.filename, ALLOWED_CSV_EXTS):
        flash("Only .csv files are accepted for participants.", "danger")
        return redirect(url_for("index"))

    # ── Work inside a temp directory ──────────────────────────────────────────
    with tempfile.TemporaryDirectory() as _tmpdir:
        tmpdir = Path(_tmpdir)

        # Save CSV
        csv_path = tmpdir / "participants.csv"
        _save_upload(csv_file, csv_path)

        # Resolve logos (uploaded or fall back to bundled assets)
        def resolve_logo(file_storage, fallback_rel: str) -> Path:
            if file_storage and file_storage.filename and _allowed(
                file_storage.filename, ALLOWED_IMAGE_EXTS
            ):
                dest = tmpdir / ("upload_" + Path(file_storage.filename).name)
                _save_upload(file_storage, dest)
                return dest
            return REPO_ROOT / fallback_rel

        left_logo_path = resolve_logo(left_logo_file, "assets/logos/awsug_trichy.png")
        right_logo_path = REPO_ROOT / "assets/logos/Usergroups_badges_member.png"
        sig_path = resolve_logo(signature_file, "assets/signatures/organizer_1.png")

        # Read participants
        try:
            rows = read_csv(csv_path)
        except Exception as exc:
            flash(f"CSV error: {exc}", "danger")
            return redirect(url_for("index"))

        if not rows:
            flash("CSV has no participant rows.", "danger")
            return redirect(url_for("index"))

        # Build theme
        theme = CertificateTheme()

        style = {
            "background": {"enabled": True, "rgb": [248, 250, 252]},
            "accent_bars": {
                "enabled": True,
                "top_height": 10,
                "bottom_height": 10,
                "rgb": [15, 23, 42],
            },
        }
        watermark = {
            "enabled": right_logo_path.exists(),
            "image": str(right_logo_path),
            "opacity": 0.08,
            "max_width": 520,
            "max_height": 320,
        }

        # Output dir
        pdf_dir = tmpdir / "pdfs"
        pdf_dir.mkdir()

        year_month = datetime.now().strftime("%Y-%m")
        seq = 1
        errors: list[str] = []

        for i, row in enumerate(rows, start=1):
            full_name = get_field(row, "name")
            if not full_name:
                errors.append(f"Row {i}: missing 'name' — skipped")
                continue

            cert_id = (get_field(row, "member_id") or get_field(row, "member id")) or make_cert_id(id_prefix, year_month, seq, 3)
            seq += 1

            role = (get_field(row, "role") or "participant").lower()
            ev_title = event_title
            ev_date = event_date
            ev_loc = location

            safe_name = normalize_safe_filename(full_name)
            out_pdf = pdf_dir / f"{cert_id}-{safe_name}.pdf"

            try:
                draw_certificate(
                    out_pdf=out_pdf,
                    theme=theme,
                    group_name=group_name,
                    participant_name=full_name,
                    event_title=ev_title,
                    event_date=ev_date,
                    location=ev_loc,
                    certificate_id=cert_id,
                    left_logo_path=left_logo_path,
                    right_logo_path=right_logo_path,
                    signature_1_path=sig_path,
                    style=style,
                    watermark=watermark,
                    role=role,
                )
            except Exception as exc:
                errors.append(f"Row {i} ({full_name}): {exc}")

        pdfs = list(pdf_dir.glob("*.pdf"))
        if not pdfs:
            msg = "No certificates were generated."
            if errors:
                msg += " Errors: " + "; ".join(errors)
            flash(msg, "danger")
            return redirect(url_for("index"))

        # ── Convert to PNG if image format requested ──────────────────────
        zip_buffer = io.BytesIO()
        if output_format == "image":
            try:
                from pdf2image import convert_from_path
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for pdf in sorted(pdfs):
                        pages = convert_from_path(str(pdf), dpi=200)
                        img_buf = io.BytesIO()
                        pages[0].save(img_buf, format="PNG", optimize=True)
                        zf.writestr(pdf.stem + ".png", img_buf.getvalue())
            except Exception as exc:
                flash(f"Image conversion failed: {exc}. Install poppler-utils to enable PNG output.", "danger")
                return redirect(url_for("index"))
        else:
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for pdf in sorted(pdfs):
                    zf.write(pdf, pdf.name)

        zip_buffer.seek(0)
        zip_data = zip_buffer.read()

    # Temp dir is deleted here — zip_data is safely in memory
    suffix = "images" if output_format == "image" else "certificates"
    download_name = f"{suffix}-{event_title.replace(' ', '_')}.zip"
    return send_file(
        io.BytesIO(zip_data),
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_name,
    )


if __name__ == "__main__":
    print("Starting AWS UG Certificate Generator...")
    print("Open http://localhost:8080 in your browser")
    app.run(debug=False, host="0.0.0.0", port=8080)
