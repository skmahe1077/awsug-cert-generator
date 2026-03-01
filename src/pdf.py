from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from reportlab.lib.pagesizes import A4, letter, landscape, portrait
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from PIL import Image

# ── Elegant name font (Playfair Display Bold) ────────────────────────────────
_FONT_DIR = Path(__file__).parents[1] / "assets" / "fonts"
_PLAYFAIR_PATH = _FONT_DIR / "PlayfairDisplay-Bold.ttf"
_PLAYFAIR_URL = (
    "https://fonts.gstatic.com/s/playfairdisplay/v40/"
    "nuFvD-vYSZviVYUb_rj3ij__anPXJzDwcbmjWBN2PKeiukDQ.ttf"
)
_NAME_FONT = "Times-BoldItalic"  # fallback until resolved


def _resolve_name_font() -> str:
    """Return the best available elegant font name for participant names."""
    global _NAME_FONT
    if _NAME_FONT != "Times-BoldItalic":
        return _NAME_FONT  # already resolved

    if not _PLAYFAIR_PATH.exists():
        try:
            _FONT_DIR.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(_PLAYFAIR_URL, _PLAYFAIR_PATH)
        except Exception:
            return "Times-BoldItalic"

    try:
        pdfmetrics.registerFont(TTFont("PlayfairDisplay-Bold", str(_PLAYFAIR_PATH)))
        _NAME_FONT = "PlayfairDisplay-Bold"
    except Exception:
        _NAME_FONT = "Times-BoldItalic"

    return _NAME_FONT


@dataclass
class CertificateTheme:
    page_size: str = "A4"
    orientation: str = "landscape"
    title: str = "Certificate of Participation"
    subtitle: str = "This certificate acknowledges participation in an AWS User Group Community-led Event"
    footer_note: str = "Community-led. Not an official AWS certification."
    id_label: str = "Member ID"
    font_name: str = "Helvetica"
    font_name_bold: str = "Helvetica-Bold"
    name_font_size: int = 38
    body_font_size: int = 14


def _pagesize(page_size: str, orientation: str):
    ps = A4 if page_size.upper() == "A4" else letter
    return landscape(ps) if orientation.lower() == "landscape" else portrait(ps)


def _load_pil(path: str | Path) -> Optional[Image.Image]:
    p = Path(path)
    if not p.exists():
        return None
    img = Image.open(p)
    # Keep alpha if present
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    return img


def _draw_image_fit(
    c: canvas.Canvas,
    pil_img: Image.Image,
    x: float,
    y: float,
    max_w: float,
    max_h: float,
) -> Tuple[float, float]:
    """Draw image inside max_w x max_h preserving aspect ratio. Returns (draw_w, draw_h)."""
    iw, ih = pil_img.size
    if iw <= 0 or ih <= 0:
        return (0.0, 0.0)
    scale = min(max_w / iw, max_h / ih)
    draw_w = iw * scale
    draw_h = ih * scale
    c.drawImage(ImageReader(pil_img), x, y, width=draw_w, height=draw_h, mask="auto")
    return (draw_w, draw_h)


def _rgb01(rgb_255) -> Tuple[float, float, float]:
    r, g, b = rgb_255
    return (r / 255.0, g / 255.0, b / 255.0)


def draw_certificate(
    out_pdf: str | Path,
    theme: CertificateTheme,
    group_name: str,
    participant_name: str,
    event_title: str,
    event_date: str,
    location: str,
    certificate_id: str,
    left_logo_path: str | Path,
    right_logo_path: str | Path,
    signature_1_path: str | Path | None = None,
    style: Optional[Dict[str, Any]] = None,
    watermark: Optional[Dict[str, Any]] = None,
    role: str = "participant",          # "participant" or "speaker"
) -> None:
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    page_w, page_h = _pagesize(theme.page_size, theme.orientation)
    c = canvas.Canvas(str(out_pdf), pagesize=(page_w, page_h))

    # Margins
    m = 48
    top = page_h - m
    left = m
    right = page_w - m
    bottom = m

    style = style or {}
    watermark = watermark or {}

    # --------------------
    # BACKGROUND COLOR
    # --------------------
    bg_cfg = (style.get("background") or {})
    if bg_cfg.get("enabled"):
        rgb = bg_cfg.get("rgb", [248, 250, 252])
        c.saveState()
        c.setFillColorRGB(*_rgb01(rgb))
        c.rect(0, 0, page_w, page_h, stroke=0, fill=1)
        c.restoreState()

    # --------------------
    # ACCENT BARS
    # --------------------
    bars_cfg = (style.get("accent_bars") or {})
    if bars_cfg.get("enabled"):
        bar_rgb = bars_cfg.get("rgb", [15, 23, 42])
        top_h = float(bars_cfg.get("top_height", 10))
        bot_h = float(bars_cfg.get("bottom_height", 10))

        c.saveState()
        c.setFillColorRGB(*_rgb01(bar_rgb))
        c.rect(0, page_h - top_h, page_w, top_h, stroke=0, fill=1)
        c.rect(0, 0, page_w, bot_h, stroke=0, fill=1)
        c.restoreState()

    # --------------------
    # BORDER
    # --------------------
    c.setLineWidth(2)
    c.rect(m - 12, m - 12, page_w - 2 * (m - 12), page_h - 2 * (m - 12), stroke=1, fill=0)
    c.setLineWidth(0.8)
    c.rect(m, m, page_w - 2 * m, page_h - 2 * m, stroke=1, fill=0)

    # --------------------
    # WATERMARK (AWS logo)
    # --------------------
    if watermark.get("enabled"):
        wm_path = watermark.get("image")
        wm_img = _load_pil(wm_path) if wm_path else None
        if wm_img:
            opacity = float(watermark.get("opacity", 0.08))
            max_w = float(watermark.get("max_width", 520))
            max_h = float(watermark.get("max_height", 320))

            # Compute centered placement
            iw, ih = wm_img.size
            scale = min(max_w / iw, max_h / ih)
            dw = iw * scale
            dh = ih * scale
            x = (page_w - dw) / 2
            y = (page_h - dh) / 2

            c.saveState()
            # ReportLab 4 supports alpha on canvas
            try:
                c.setFillAlpha(opacity)
                c.setStrokeAlpha(opacity)
            except Exception:
                # If alpha isn't available, it will just draw normally (still OK)
                pass
            c.drawImage(ImageReader(wm_img), x, y, width=dw, height=dh, mask="auto")
            c.restoreState()

    # --------------------
    # LOGOS (top corners) — bigger
    # --------------------
    logo_box_w = 240
    logo_box_h = 120
    logo_pad = 12  # inner gap between border and logo

    left_logo = _load_pil(left_logo_path)
    right_logo = _load_pil(right_logo_path)

    if left_logo:
        iw, ih = left_logo.size
        scale = min(logo_box_w / iw, logo_box_h / ih)
        dw = iw * scale
        dh = ih * scale
        c.drawImage(ImageReader(left_logo), left + logo_pad, top - dh - logo_pad, width=dw, height=dh, mask="auto")

    if right_logo:
        iw, ih = right_logo.size
        scale = min(logo_box_w / iw, logo_box_h / ih)
        dw = iw * scale
        dh = ih * scale
        c.drawImage(ImageReader(right_logo), right - dw - logo_pad, top - dh - logo_pad, width=dw, height=dh, mask="auto")

    # Header group name — AWS orange #FF9900, 28pt
    c.saveState()
    c.setFillColorRGB(*_rgb01([255, 153, 0]))  # AWS official orange
    c.setFont(theme.font_name_bold, 28)
    c.drawCentredString(page_w / 2, top - logo_pad - 36, group_name)
    c.restoreState()

    is_speaker = role.strip().lower() == "speaker"

    # Speaker badge — just below the group name, deep purple
    if is_speaker:
        c.saveState()
        badge_w, badge_h = 130, 24
        badge_x = (page_w - badge_w) / 2
        # Group name is at (top - logo_pad - 36); place badge 10pts below it
        badge_y = top - logo_pad - 36 - badge_h - 10
        c.setFillColorRGB(*_rgb01([91, 33, 182]))   # deep purple #5B21B6
        c.roundRect(badge_x, badge_y, badge_w, badge_h, 8, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)                  # white text
        c.setFont(theme.font_name_bold, 11)
        c.drawCentredString(page_w / 2, badge_y + 7, "✦  SPEAKER  ✦")
        c.restoreState()

    # Vertical positions — shift content block down for speaker to
    # compensate for the extra badge row in the header
    if is_speaker:
        y_title    = page_h * 0.55
        y_subtitle = page_h * 0.49
        y_name     = page_h * 0.41
        y_body     = page_h * 0.35
    else:
        y_title    = page_h * 0.60
        y_subtitle = page_h * 0.54
        y_name     = page_h * 0.46
        y_body     = page_h * 0.40

    # Title
    title_text = "Certificate of Appreciation" if is_speaker else theme.title
    c.setFont(theme.font_name_bold, 30)
    c.drawCentredString(page_w / 2, y_title, title_text)

    # Subtitle
    if is_speaker:
        subtitle_text = (
            "This certificate appreciates the valuable contribution as a"
            " Speaker at an AWS User Group Community-led Event"
        )
    else:
        subtitle_text = theme.subtitle
    c.setFont(theme.font_name, theme.body_font_size)
    c.drawCentredString(page_w / 2, y_subtitle, subtitle_text)

    # Participant name — Playfair Display Bold (elegant serif)
    name_font = _resolve_name_font()
    c.setFont(name_font, theme.name_font_size)
    c.drawCentredString(page_w / 2, y_name, participant_name)

    # Body text
    body_text = f"For speaking at {event_title}" if is_speaker else f"For participating in {event_title}"
    c.setFont(theme.font_name, theme.body_font_size)
    c.drawCentredString(page_w / 2, y_body, body_text)

    # Bottom row: Date | Location
    bottom_y = bottom + 28
    c.setFont(theme.font_name, 10.5)
    c.drawString(left + logo_pad, bottom_y, f"Date: {event_date}")
    c.drawRightString(right - logo_pad, bottom_y, f"Location: {location}")

    # Footer note — very bottom center, below date/location
    c.setFont(theme.font_name, 10)
    c.drawCentredString(page_w / 2, bottom + 8, theme.footer_note)

    # Organizer signature (bottom-right above bottom row, no label)
    sig_img = _load_pil(signature_1_path) if signature_1_path else None
    if sig_img:
        sig_box_w, sig_box_h = 220, 80
        iw, ih = sig_img.size
        scale = min(sig_box_w / iw, sig_box_h / ih)
        dw = iw * scale
        dh = ih * scale
        sig_x = right - dw - logo_pad
        sig_y = bottom + 55
        c.drawImage(ImageReader(sig_img), sig_x, sig_y, width=dw, height=dh, mask="auto")

    c.showPage()
    c.save()
