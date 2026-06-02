import json
import os
import tempfile
import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from hachoir.core import config as hachoir_config

# Disable Hachoir logging to keep the UI clean
hachoir_config.quiet = True

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def _normalize_value(value):
    if isinstance(value, bytes):
        try:
            return value.decode(errors="replace")
        except Exception:
            return str(value)
    if isinstance(value, (list, tuple)):
        return [ _normalize_value(v) for v in value ]
    return value


def get_image_metadata(file_path):
    """Extracts EXIF metadata from an image file."""
    metadata = {}
    try:
        with Image.open(file_path) as img:
            metadata['Format'] = img.format
            metadata['Width'] = img.width
            metadata['Height'] = img.height
            metadata['Mode'] = img.mode
            
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    
                    if isinstance(value, bytes):
                        value = value.decode(errors='replace')
                    elif hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                        if value.denominator != 0:
                            value = float(value.numerator) / value.denominator
                        else:
                            value = str(value)
                    elif type(value).__name__ in ['IFDRational', 'TiffImagePlugin.IFDRational']:
                        value = str(value)
                    
                    metadata[str(tag_name)] = value
                    
    except Exception as e:
        metadata['Error'] = f"Could not extract image metadata: {str(e)}"
    return metadata


def _flatten_metadata(data, parent_key=""):
    flat = {}
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}.{key}" if parent_key else str(key)
            flat.update(_flatten_metadata(value, new_key))
    elif isinstance(data, (list, tuple)):
        for index, item in enumerate(data):
            flat.update(_flatten_metadata(item, f"{parent_key}[{index}]"))
    else:
        flat[parent_key] = _normalize_value(data)
    return flat


def get_video_metadata(file_path):
    metadata = {}
    try:
        parser = createParser(file_path)
        if not parser:
            return {"Error": "Unable to parse video file format."}

        with parser:
            extracted = extractMetadata(parser)
            if not extracted:
                return {"Error": "Metadata extraction failed or returned empty."}

            try:
                raw = extracted.exportDictionary()
                metadata = _flatten_metadata(raw)
            except Exception:
                for line in extracted.exportPlainString().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
    except Exception as error:
        metadata["Error"] = f"Could not extract video metadata: {error}"
    return metadata


# --- HIGH-END UI ROW RENDERING ---
def render_metadata_row(key, value, category):
    """Renders a sleek database-style record row with 4.5+:1 contrast safety."""
    color_map = {
        "structure": "#00E5FF",  # Tech Cyan
        "hardware": "#FFB300",   # Muted Amber
        "identity": "#00E676",   # System Emerald
        "location": "#FF007F"    # Forensic Magenta
    }
    accent_color = color_map.get(category, "#888888")
    
    html_string = f"""
    <div style="display: grid; grid-template-columns: 240px 1fr; border-bottom: 1px solid #1A1F2C; padding: 10px 16px; font-family: 'SF Mono', 'Roboto Mono', monospace; font-size: 12px; align-items: baseline; background-color: #0D1117;">
        <span style="color: {accent_color}; font-weight: 600; letter-spacing: 0.2px;">{key}</span>
        <span style="color: #5B90AB; word-break: break-all; white-space: pre-wrap; line-height: 1.5;">{value}</span>
    </div>
    """
    st.markdown(html_string, unsafe_allow_html=True)


def main():
    # 1. Premium Dark Architecture Page Init
    st.set_page_config(page_title="METASTRACTOR // Pro Forensics Engine", page_icon="🔍", layout="wide")
    
    # Injection of comprehensive web-app product layout styles
    st.markdown("""
        <style>
        /* Main application background reset */
        .main { background-color: #07090E !important; }
        [data-testid="stSidebar"] { background-color: #0B0E14 !important; border-right: 1px solid #1A1F2C; }
        
        /* Premium Core Font Rules */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
        
        /* File Uploader UI Overhaul */
        div[data-testid="stFileUploader"] { background-color: #0D1117; border: 1px dashed #2A3447; border-radius: 6px; padding: 20px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3); }
        div[data-testid="stFileUploader"] section { background-color: transparent !important; }
        
        /* Metric Card Overhaul */
        div[data-testid="stMetric"] { background-color: #0D1117; border: 1px solid #1A1F2C; padding: 14px 18px; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        div[data-testid="stMetricValue"] { color: #4A7E9F !important; font-family: 'SF Mono', monospace !important; font-size: 22px !important; font-weight: 700 !important; }
        div[data-testid="stMetricLabel"] { color: #5B90AB !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.75px; }
        
        /* Download Button Customizing */
        div.stButton > button { background-color: #10B981 !important; color: #ffffff !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important; font-size: 13px !important; border: none !important; border-radius: 4px !important; padding: 12px 24px !important; transition: all 0.2s ease-in-out; width: 100%; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2); }
        div.stButton > button:hover { background-color: #059669 !important; transform: translateY(-1px); box-shadow: 0 6px 16px rgba(16, 185, 129, 0.3); }
        </style>
    """, unsafe_allow_html=True)

    # 2. Sidebar Navigation Panel
    with st.sidebar:
        st.markdown("<div style='padding: 10px 0;'><span style='font-family: monospace; font-size: 11px; color: #475569; letter-spacing: 1px;'>SYSTEM INSTANCE</span></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #2F6B8C; font-size: 16px; margin-top:-5px; font-weight:600;'>📊 METASTRACTOR PRO</h2>", unsafe_allow_html=True)
        st.markdown("<div style='border-bottom: 1px solid #1A1F2C; margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        st.markdown("CORE STATUS: <span style='color:#10B981; font-family:monospace; font-weight:600; font-size:12px; margin-left:5px;'>● ACTIVE</span>", unsafe_allow_html=True)
        st.markdown("SECURITY MODEL: <span style='color:#94A3B8; font-family:monospace; font-size:12px; margin-left:5px;'>ISOLATED_ENV</span>", unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 30px;'><span style='font-family: monospace; font-size: 11px; color: #475569; letter-spacing: 1px;'>LAYER SCHEMATIC</span></div>", unsafe_allow_html=True)
        st.markdown("<div style='background-color: #07090E; padding: 12px; border-radius: 6px; border: 1px solid #1A1F2C; margin-top:5px;'>"
                    "<div style='margin-bottom: 8px;'><span style='color:#00E5FF; font-size:14px; margin-right:8px;'>■</span><span style='color:#E2E8F0; font-size:12px;'>File Architecture</span></div>"
                    "<div style='margin-bottom: 8px;'><span style='color:#FFB300; font-size:14px; margin-right:8px;'>■</span><span style='color:#E2E8F0; font-size:12px;'>EXIF Sensor Hardware</span></div>"
                    "<div style='margin-bottom: 8px;'><span style='color:#00E676; font-size:14px; margin-right:8px;'>■</span><span style='color:#E2E8F0; font-size:12px;'>Identity & Timestamps</span></div>"
                    "<div><span style='color:#FF007F; font-size:14px; margin-right:8px;'>■</span><span style='color:#E2E8F0; font-size:12px;'>GPS Telemetry Maps</span></div>"
                    "</div>", unsafe_allow_html=True)

    # 3. Main Dashboard Header
    st.markdown("<h1 style='color: #4A7E9F; font-size: 26px; font-weight: 700; margin-bottom: 4px; letter-spacing: -0.5px;'>File Stream Metadata Inspector</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #5B90AB; font-size: 14px; margin-bottom: 25px;'>Enterprise digital forensics platform for deep packet byte-signature parsing and immutable file-layer verification.</p>", unsafe_allow_html=True)
    st.markdown("<div style='border-bottom: 1px solid #1A1F2C; margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # Split workspace into an clean unbalanced 1:2 column grid layout
    col1, col2 = st.columns([5, 11], gap="large")

    with col1:
        st.markdown("<h3 style='color: #2F6B8C; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;'>📥 Asset Ingestion</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Target File",
            type=[ext.lstrip(".") for ext in sorted(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS)],
            label_visibility="collapsed"
        )
        
        if uploaded_file is None:
            st.markdown("<div style='background-color: #0D1117; padding: 20px; border-radius: 6px; border: 1px solid #1A1F2C; text-align: center;'><span style='color:#475569; font-family: monospace; font-size: 12px;'>STANDBY // CONNECT FILE STREAM TARGET</span></div>", unsafe_allow_html=True)
            return

        file_name = uploaded_file.name
        suffix = file_name.lower().rsplit('.', 1)[-1] if '.' in file_name else ''
        extension = f".{suffix}"
        
        st.markdown(f"<div style='background-color:#0D1117; padding:12px 16px; border-radius: 4px; border: 1px solid #10B981; font-family:monospace; font-size:12px; color:#4A7E9F; font-weight: 500; box-shadow: 0 4px 12px rgba(16,185,129,0.05);'>📄 READY: {file_name}</div>", unsafe_allow_html=True)

    # 4. Processing Engine Block
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        temp_path = tmp_file.name

    try:
        if extension in IMAGE_EXTENSIONS:
            metadata_results = get_image_metadata(temp_path)
        elif extension in VIDEO_EXTENSIONS:
            metadata_results = get_video_metadata(temp_path)
        else:
            metadata_results = {"Error": "Unsupported system format."}
    finally:
        try: tmp_file.close()
        except: pass
        try:
            if os.path.exists(temp_path): os.remove(temp_path)
        except: pass

    # 5. Categorized UI Output Dashboard Display
    with col2:
        if metadata_results:
            st.markdown("<h3 style='color: #2F6B8C; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;'>📊 Analysis Real-Time Manifest</h3>", unsafe_allow_html=True)
            
            # Telemetry metrics resolution filters
            fmt_val = str(metadata_results.get('Format', extension.upper().replace('.', '')))
            w_val = str(metadata_results.get('Width', metadata_results.get('Metadata.Image width', '—'))).replace(' pixels', '')
            h_val = str(metadata_results.get('Height', metadata_results.get('Metadata.Image height', '—'))).replace(' pixels', '')

            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1: st.metric(label="Container MIME", value=fmt_val)
            with m_col2: st.metric(label="Dimension Width", value=w_val)
            with m_col3: st.metric(label="Dimension Height", value=h_val)

            st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

            # Functional Categorization Layer Arrays
            structure_data = {}
            hardware_data = {}
            identity_data = {}
            location_data = {}

            # Strict architecture target routing filters
            struct_targets = {'Format', 'Width', 'Height', 'Mode', 'BitsPerSample', 'Compression', 'ImageWidth', 'ImageLength'}
            hardware_targets = {'Make', 'Model', 'Software', 'FNumber', 'ExposureTime', 'ISOSpeedRatings', 'FocalLength', 'LensModel', 'WhiteBalance', 'Flash', 'ResolutionUnit', 'XResolution', 'YResolution'}
            identity_targets = {'DateTime', 'DateTimeOriginal', 'DateTimeDigitized', 'Artist', 'Copyright', 'ImageDescription', 'OffsetTime', 'OffsetTimeOriginal', 'OffsetTimeDigitized'}
            location_targets = {'GPSInfo', 'GPSLatitude', 'GPSLongitude', 'GPSPosition'}

            for k, v in metadata_results.items():
                if k in struct_targets or "width" in k.lower() or "height" in k.lower() or "mime" in k.lower() or "duration" in k.lower() or "endian" in k.lower():
                    structure_data[k] = v
                elif k in hardware_targets or "codec" in k.lower():
                    hardware_data[k] = v
                elif k in identity_targets or "date" in k.lower() or "comment" in k.lower():
                    identity_data[k] = v
                elif k in location_targets or "gps" in k.lower():
                    location_data[k] = v
                else:
                    structure_data[k] = v

            # Premium Outer Frame Data Matrix Container Block
            st.markdown("<div style='border: 1px solid #1A1F2C; border-radius: 6px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>", unsafe_allow_html=True)
            
            # --- SECTION 1: ARCHITECTURE ---
            if structure_data:
                st.markdown("<div style='background-color: #111622; padding: 10px 16px; font-size: 11px; font-weight: 700; color: #00E5FF; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #1A1F2C;'>[01] // File Structure Layer</div>", unsafe_allow_html=True)
                for k, v in structure_data.items():
                    render_metadata_row(k, v, "structure")

            # --- SECTION 2: HARDWARE ---
            if hardware_data:
                st.markdown("<div style='background-color: #111622; padding: 10px 16px; font-size: 11px; font-weight: 700; color: #FFB300; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #1A1F2C; border-top: 1px solid #1A1F2C;'>[02] // EXIF Sensor Hardware Layer</div>", unsafe_allow_html=True)
                for k, v in hardware_data.items():
                    render_metadata_row(k, v, "hardware")

            # --- SECTION 3: TIMELINE / IDENTITY ---
            if identity_data:
                st.markdown("<div style='background-color: #111622; padding: 10px 16px; font-size: 11px; font-weight: 700; color: #00E676; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #1A1F2C; border-top: 1px solid #1A1F2C;'>[03] // Identity & Temporal Stamps</div>", unsafe_allow_html=True)
                for k, v in identity_data.items():
                    render_metadata_row(k, v, "identity")

            # --- SECTION 4: GPS TELEMETRY ---
            if location_data:
                st.markdown("<div style='background-color: #111622; padding: 10px 16px; font-size: 11px; font-weight: 700; color: #FF007F; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #1A1F2C; border-top: 1px solid #1A1F2C;'>[04] // Geolocation Tracking Matrix</div>", unsafe_allow_html=True)
                for k, v in location_data.items():
                    render_metadata_row(k, v, "location")
            elif extension in IMAGE_EXTENSIONS and not location_data:
                st.markdown("<div style='background-color: #111622; padding: 10px 16px; font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #1A1F2C; border-top: 1px solid #1A1F2C;'>[04] // Geolocation Tracking Matrix</div>", unsafe_allow_html=True)
                st.markdown("<div style='padding: 14px 16px; font-family: monospace; font-size: 11px; color: #475569; background-color:#0D1117;'>No embedded GPS layers found inside this metadata block structure.</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # 6. Action Export Manifest Generation System
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            json_string = json.dumps(metadata_results, indent=2)
            st.download_button(
                label="📥 EXPORT FORENSIC JSON MANIFEST",
                data=json_string,
                file_name=f"{file_name.rsplit('.', 1)[0]}_forensic_manifest.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.markdown("<div style='background-color: #1A0D11; border: 1px solid #4C1D24; padding: 16px; border-radius: 4px; color: #F87171; font-family: monospace; font-size:12px; font-weight:600;'>[MALFORMED_STREAM_FAILURE] Cannot isolate byte boundary partitions within target source.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()