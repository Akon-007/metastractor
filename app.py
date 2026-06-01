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
            # Basic info
            metadata['Format'] = img.format
            metadata['Width'] = img.width
            metadata['Height'] = img.height
            metadata['Mode'] = img.mode
            
            # EXIF data
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    
                    # --- CRASH FIX HERE ---
                    # Handle custom Pillow data structures (IFDRational, bytes, etc.)
                    if isinstance(value, bytes):
                        value = value.decode(errors='replace')
                    elif hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                        # Convert fractional structures safely to float or string
                        if value.denominator != 0:
                            value = float(value.numerator) / value.denominator
                        else:
                            value = str(value)
                    elif type(value).__name__ in ['IFDRational', 'TiffImagePlugin.IFDRational']:
                        value = str(value)
                    # ----------------------
                    
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


def main():
    st.set_page_config(page_title="Metadata Extractor", page_icon="🔍", layout="centered")
    st.title("🔍 Media Metadata Extractor")
    st.write("Upload an image or video file to view and download embedded metadata.")

    uploaded_file = st.file_uploader(
        "Choose an image or video file",
        type=[ext.lstrip(".") for ext in sorted(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS)]
    )

    if uploaded_file is None:
        st.info("Supported image types: JPG, JPEG, PNG, WEBP, TIFF, BMP. Supported video types: MP4, MOV, AVI, MKV, WEBM.")
        return

    file_name = uploaded_file.name
    st.success(f"Uploaded file: **{file_name}**")

    suffix = file_name.lower().rsplit('.', 1)[-1] if '.' in file_name else ''
    extension = f".{suffix}"

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        temp_path = tmp_file.name

    try:
        if extension in IMAGE_EXTENSIONS:
            metadata_results = get_image_metadata(temp_path)
        elif extension in VIDEO_EXTENSIONS:
            metadata_results = get_video_metadata(temp_path)
        else:
            metadata_results = {"Error": "Unsupported file extension for metadata extraction."}
    finally:
        try:
            tmp_file.close()
        except Exception:
            pass
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

    if metadata_results:
        st.subheader("📋 Extracted Metadata")
        
        # 1. Isolate the standard, generic image properties if they exist
        core_keys = ['Format', 'Width', 'Height', 'Mode']
        core_props = {k: metadata_results[k] for k in core_keys if k in metadata_results}
        
        # 2. Keep all other complex/deep hardware artifacts separate
        exif_props = {k: v for k, v in metadata_results.items() if k not in core_keys}
        
        # 3. Always display basic properties cleanly
        st.markdown("#### 🖼️ Core File Properties")
        st.json(core_props)
        
        # 4. Elegantly handle if deep data is missing (stripped) or present
        st.markdown("#### 🔐 Deep Hardware & Timeline Data")
        if exif_props:
            st.json(exif_props)
        else:
            st.info("No deep EXIF tags found in this file header. This file has likely been stripped or optimized by a web platform.")
        
    else:
        st.warning("No metadata could be extracted from this file.")

    # --- THIS PART SITS OUTSIDE THE IF/ELSE BLOCKS ---
    st.subheader("💾 Download Metadata")
    json_string = json.dumps(metadata_results, indent=2)
    st.download_button(
        label="Download Metadata as JSON",
        data=json_string,
        file_name=f"{file_name.rsplit('.', 1)[0]}_metadata.json",
        mime="application/json"
    )

if __name__ == "__main__":
    main()