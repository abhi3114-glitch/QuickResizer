# QuickResizer

QuickResizer is a bulk image processing utility designed for efficiency and high-quality output. It allows users to resize, format, and rename multiple images simultaneously through a clean web interface.

## Features

### Bulk Resizing
Process batches of images with predefined presets or custom dimensions.
- **1:1 Square**: 1080x1080 pixels (Optimized for social media)
- **1080p Full HD**: 1920x1080 pixels (Standard high definition)
- **Passport Size**: 35x45mm at 300 DPI (Standard document size)
- **Custom Dimensions**: User-defined width and height

### Resize Strategies
Choose how images fit into the target dimensions:
- **Fit (Contain)**: Resizes the image to fit within the target box while maintaining aspect ratio. Adds padding if necessary.
- **Fill (Cover)**: Resizes the image to cover the target box completely, cropping excess parts.
- **Stretch**: Forces the image to exact dimensions, potentially distorting the aspect ratio.

### Format Conversion
Convert images between common formats:
- JPEG
- PNG
- WEBP
- Original Format (Preserve input format)

### Batch Renaming
Systematically rename output files:
- Add custom prefixes
- Add custom suffixes
- Append sequential numbering

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/abhi3114-glitch/QuickResizer.git
   cd QuickResizer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Requirements

- Python 3.8 or higher
- Pillow
- Streamlit

## Usage Guide

1. Launch the application using the command above.
2. Use the sidebar to configure your processing settings (Preset, Mode, Format, Quality, Renaming).
3. Drag and drop your images into the upload area.
4. Review the file statistics.
5. Click "Start Batch Processing".
6. Download the resulting ZIP file containing your optimized images.
