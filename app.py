"""
QuickResizer - Bulk Image Resizer & Converter
A Streamlit application for batch image processing.
"""

import streamlit as st
from image_processing import (
    ResizePreset,
    batch_process,
    create_zip,
    get_image_info,
    PRESET_DIMENSIONS
)
from PIL import Image
import io

# Page configuration
st.set_page_config(
    page_title="QuickResizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global styling */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }

    /* Headlines */
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Hero Section */
    .hero-container {
        padding: 2rem 0 3rem 0;
        text-align: center;
        background: linear-gradient(180deg, rgba(14, 17, 23, 0) 0%, rgba(38, 39, 48, 0.3) 100%);
        border-radius: 20px;
        margin-bottom: 2rem;
    }

    .main-title {
        font-size: 3.5rem;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        font-size: 1.2rem;
        color: #9CA3AF;
        max-width: 600px;
        margin: 0 auto;
    }

    /* Uploader */
    [data-testid="stFileUploader"] {
        background-color: #1A1C24;
        border: 1px dashed #374151;
        border-radius: 16px;
        padding: 2rem;
        transition: all 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #4facfe;
        background-color: #1F2937;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #11131A;
        border-right: 1px solid #1F2937;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: none;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s;
    }

    /* Primary Process Button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: #000;
        box-shadow: 0 4px 14px 0 rgba(0, 242, 254, 0.39);
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.23);
    }

    /* Cards/Containers */
    .card-container {
        background-color: #1A1C24;
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #4facfe;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Custom footer removal */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def main():
    # Sidebar
    with st.sidebar:
        st.write("## ⚙️ Configuration")
        
        # Preset Selection
        st.caption("TARGET SIZE")
        preset_option = st.selectbox(
            "Select Preset",
            ["1:1 Square", "1080p Full HD", "Passport Size", "Custom Dimensions"],
            label_visibility="collapsed"
        )
        
        preset_map = {
            "1:1 Square": ResizePreset.SQUARE_1080,
            "1080p Full HD": ResizePreset.HD_1080P,
            "Passport Size": ResizePreset.PASSPORT,
            "Custom Dimensions": ResizePreset.CUSTOM
        }
        selected_preset = preset_map[preset_option]

        # Dynamic Dimensions Info
        custom_size = None
        if selected_preset == ResizePreset.CUSTOM:
            c1, c2 = st.columns(2)
            with c1: custom_width = st.number_input("Width (px)", min_value=1, value=800)
            with c2: custom_height = st.number_input("Height (px)", min_value=1, value=600)
            custom_size = (custom_width, custom_height)
        else:
            w, h = PRESET_DIMENSIONS[selected_preset]
            st.info(f"Output Resolution: **{w} x {h} px**")

        st.divider()

        # Resizing Logic
        st.caption("RESIZE STRATEGY")
        resize_mode = st.radio(
            "Mode",
            ["Fit (Contain)", "Fill (Cover)", "Stretch"],
            index=0,
            label_visibility="collapsed"
        )
        maintain_aspect = resize_mode == "Fit (Contain)"
        crop_to_fit = resize_mode == "Fill (Cover)"

        st.divider()

        # Format & Quality
        st.caption("OUTPUT FORMAT")
        target_format_opt = st.selectbox(
            "Convert To",
            ["Original Format", "JPEG", "PNG", "WEBP"],
            label_visibility="collapsed"
        )
        target_format = None if target_format_opt == "Original Format" else target_format_opt

        quality = 95
        if target_format in ["JPEG", "WEBP"] or (target_format is None):
            quality = st.slider("Quality Optimization", 1, 100, 95)

        st.divider()

        # Renaming
        with st.expander("📝 File Naming"):
            prefix = st.text_input("Prefix", placeholder="optimized_")
            suffix = st.text_input("Suffix", placeholder="_v1")
            use_numbering = st.toggle("Append Sequential Numbers", value=False)

    # Main Area
    st.markdown('<div class="hero-container"><h1 class="main-title">QuickResizer</h1><p class="subtitle">The professional bulk image processor. Resize, convert, and optimize batches in seconds.</p></div>', unsafe_allow_html=True)

    # Upload Section
    
    uploaded_files = st.file_uploader(
        "Drop your images here to begin processing",
        type=["jpg", "png", "webp", "bmp", "gif"],
        accept_multiple_files=True
    )

    if uploaded_files:
        # Stats Bar
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        total_mb = sum(f.size for f in uploaded_files) / (1024 * 1024)
        
        with c1:
            st.markdown(f'<div class="card-container"><div class="metric-value">{len(uploaded_files)}</div><div class="metric-label">Images Selected</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card-container"><div class="metric-value">{total_mb:.1f} MB</div><div class="metric-label">Total Size</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card-container"><div class="metric-value">{selected_preset.value if selected_preset != ResizePreset.CUSTOM else "Custom"}</div><div class="metric-label">Target Preset</div></div>', unsafe_allow_html=True)

        # Action Button
        col_main, col_pad = st.columns([1, 2])
        process = False
        with col_main:
            st.markdown("<br>", unsafe_allow_html=True)
            process = st.button("⚡ Start Batch Processing", type="primary", use_container_width=True)

        # Processing Logic
        if process:
            progress_bar = st.progress(0)
            status = st.empty()
            
            # Prepare data
            raw_images = [{'data': f.getvalue(), 'name': f.name} for f in uploaded_files]
            
            try:
                def update_bar(curr, total):
                    progress_bar.progress(curr/total)
                    status.text(f"Processing image {curr}/{total}...")

                processed = batch_process(
                    raw_images,
                    selected_preset,
                    custom_size=custom_size,
                    target_format=target_format,
                    maintain_aspect=maintain_aspect,
                    crop_to_fit=crop_to_fit,
                    quality=quality,
                    prefix=prefix,
                    suffix=suffix,
                    use_numbering=use_numbering,
                    progress_callback=update_bar
                )

                # Finalizing
                zip_bytes = create_zip(processed)
                progress_bar.empty()
                status.empty()

                st.success("✨ Processing Complete!")
                
                # Result Area
                st.download_button(
                    label=f"📥 Download ZIP ({len(zip_bytes)/1024/1024:.1f} MB)",
                    data=zip_bytes,
                    file_name="processed_images.zip",
                    mime="application/zip",
                    type="primary"
                )

                # Visual Confirmation
                st.markdown("### Preview Results")
                cols = st.columns(4)
                for idx, (p_bytes, p_name) in enumerate(processed[:4]):
                    with cols[idx]:
                        st.image(io.BytesIO(p_bytes), caption=p_name, use_container_width=True)
                
                if len(processed) > 4:
                    st.caption(f"And {len(processed)-4} more images...")

            except Exception as e:
                st.error(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    main()
