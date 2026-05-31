# Media Metadata Extractor

A small Streamlit app to extract metadata from images and videos and download it as JSON.

## Setup

1. (Optional) Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser if it doesn't open automatically.

## Files

- `app.py` - Main Streamlit application.
- `requirements.txt` - Python dependencies.

## Notes

- The app uses Pillow to read image EXIF data and Hachoir to extract video metadata.
- For large files or unsupported formats, extraction may return limited or no metadata.# Metadata Extractor

A lightweight Streamlit app that extracts metadata from images and videos and lets users download the results as JSON.

## Requirements

- Python 3.8+
- `streamlit`
- `pillow`
- `hachoir`

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

## Usage

1. Open the app in your browser.
2. Upload an image or video file.
3. View the extracted metadata.
4. Download the metadata as a JSON file.
