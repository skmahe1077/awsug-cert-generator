# AWS User Group — Certificate Generator

A local web application for AWS User Group organizers to generate **participation and speaker certificates** as PDFs or PNG images from a CSV file.

> **Trademark note:** AWS logos/marks are owned by Amazon. This repository does **not** ship AWS logos. You must provide your own logo files and follow [AWS trademark and brand guidelines](https://aws.amazon.com/trademark-guidelines/). This project is community-led and **not an official AWS product**.

---

## Features

- **Web UI** — browser-based form; no command-line knowledge required
- **Batch generation** — upload a CSV and generate all certificates in one click
- **Two certificate types** — Participation and Speaker (auto-detected from CSV `role` column)
- **PDF and PNG output** — download as a ZIP archive
- **Custom branding** — upload your own AWS User Group logo and organizer signature
- **Elegant typography** — Playfair Display Bold for participant names (auto-downloaded)
- **Watermark** — AWS User Groups badge subtly watermarked in the background
- **Docker support** — run with a single `docker compose up` command

---

## Project Structure

```
awsug-cert-generator/
├── app.py                      # Flask web application
├── cli.py                      # cert-generator CLI entry point
├── pyproject.toml              # Package config and CLI registration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Multi-stage Docker image
├── docker-compose.yml          # Docker Compose config
│
├── src/
│   ├── pdf.py                  # Certificate PDF drawing (ReportLab)
│   ├── generate.py             # Certificate ID and filename utilities
│   └── utils.py                # CSV reader
│
├── assets/
│   ├── logos/
│   │   ├── awsug_trichy.png             # Default left logo (replace with your group logo)
│   │   └── Usergroups_badges_member.png # AWS User Groups badge (watermark + right logo)
│   ├── signatures/
│   │   └── organizer_1.png              # Organizer signature image
│   └── fonts/
│       └── PlayfairDisplay-Bold.ttf     # Auto-downloaded on first run
│
├── templates/
│   └── index.html              # Web UI template
│
├── data/
│   ├── participants.csv         # Your participant list (edit this)
│   └── participants.sample.csv  # Example CSV for reference
│
└── config/
    └── certificate.yml         # Default certificate configuration
```

---

## Quick Start

### Option A — Local Python (Recommended for development)

#### 1. Requirements

- Python 3.9 or higher
- macOS / Linux / Windows
- For PNG output: `poppler-utils` (see [PNG output](#png-image-output) section)

#### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

#### 3. Install the CLI (optional but recommended)

```bash
pip install -e .
```

#### 4. Start the web server

Using the CLI command (after `pip install -e .`):

```bash
cert-generator start
```

Or directly with Python:

```bash
python app.py
```

#### 5. Open in your browser

```
http://localhost:8080
```

---

### Option B — Docker

#### 1. Build and run

```bash
docker compose up --build
```

#### 2. Open in your browser

```
http://localhost:8080
```

Generated certificates are saved to `./output/` on your host machine (volume-mounted).

#### Stop the container

```bash
docker compose down
```

---

## CLI Reference

```
cert-generator start [--port PORT] [--host HOST]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--port` | `8080` | Port to listen on |
| `--host` | `127.0.0.1` | Host to bind (use `0.0.0.0` to expose on LAN) |

**Examples:**

```bash
# Default: localhost:8080
cert-generator start

# Custom port
cert-generator start --port 9000

# Expose on local network
cert-generator start --host 0.0.0.0 --port 8080
```

---

## Using the Web UI

### Step 1 — Fill in Event Details

| Field | Description |
|-------|-------------|
| AWS User Group Name | Your group name (e.g., "AWS User Group Bangalore") |
| Event Title | Name of the event (e.g., "AWS Community Day 2026") |
| Event Date | Date shown on the certificate |
| Location | City / venue shown on the certificate |

### Step 2 — Upload Logos and Signature

| Upload | Description |
|--------|-------------|
| AWS User Group Logo | Your group logo (PNG/JPG). Falls back to the bundled default logo. |
| Organizer Signature | Signature image placed at the bottom-right of each certificate. |

### Step 3 — Upload Participants CSV

Upload a `.csv` file with the following columns:

| Column | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Participant's full name |
| `member_id` | No | Member ID shown on the certificate. Auto-generated if blank. |
| `role` | No | `participant` (default) or `speaker` |

**Example CSV:**

```csv
name,member_id,role
Anitha R,MEM001,participant
Suresh K,MEM002,speaker
Priya M,MEM003,participant
```

> You can download a sample CSV directly from the web UI by clicking **"Download Sample CSV"**.

### Step 4 — Choose Output Format

| Format | Description |
|--------|-------------|
| PDF | Print-ready PDF certificate (A4 landscape) |
| Image (PNG) | High-resolution PNG at 200 DPI (requires poppler — see below) |

### Step 5 — Generate

Click **"Generate Certificates"** to download a ZIP archive containing all certificates.

---

## Certificate Types

### Participation Certificate

- Title: **Certificate of Participation**
- Subtitle: "This certificate acknowledges participation in an AWS User Group Community-led Event"
- Body: "For participating in {Event Title}"

### Speaker Certificate

Automatically applied when `role` is `speaker` in the CSV.

- Title: **Certificate of Appreciation**
- Subtitle: "This certificate appreciates the valuable contribution as a Speaker at an AWS User Group Community-led Event"
- Body: "For speaking at {Event Title}"
- Visual badge: Purple **✦ SPEAKER ✦** badge displayed below the group name

---

## PNG Image Output

To enable PNG output, `poppler-utils` must be installed on your system.

**macOS:**

```bash
brew install poppler
```

**Ubuntu / Debian:**

```bash
sudo apt-get install poppler-utils
```

**Windows:**

Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases) and add the `bin/` folder to your `PATH`.

> PNG output is included automatically when using Docker — `poppler-utils` is installed in the image.

---

## Replacing Default Assets

### Group Logo (left logo)

Replace `assets/logos/awsug_trichy.png` with your own group logo, or upload it directly through the web UI. Transparent PNG is recommended.

### Organizer Signature

Replace `assets/signatures/organizer_1.png` with the organizer's signature image, or upload it through the web UI.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `Flask>=3.0.0` | Web framework |
| `reportlab>=4.2.5` | PDF generation |
| `Pillow>=10.4.0` | Image processing |
| `PyYAML>=6.0.2` | Config file parsing |
| `pdf2image>=1.17.0` | PDF to PNG conversion |

---

## Trademark & License

- This project is **community-led** and is **not affiliated with or endorsed by Amazon Web Services**.
- AWS, the AWS logo, and related marks are trademarks of Amazon.com, Inc. or its affiliates.
- You are responsible for complying with [AWS Trademark Guidelines](https://aws.amazon.com/trademark-guidelines/) when using any AWS branding in your certificates.

**MIT License** — see [LICENSE](LICENSE) for details.

---

Built by [Mahendran Selvakumar](https://github.com/mahendranselvakumar) · For AWS User Group Organizers Worldwide
