"""
QuickResizer - Image Processing Utilities
Provides resize, format conversion, and batch processing functions.
"""

from PIL import Image
import io
import zipfile
from typing import Tuple, Optional, List, Dict
from enum import Enum


class ResizePreset(Enum):
    """Predefined resize presets."""
    SQUARE_1080 = "1:1"
    HD_1080P = "1080p"
    PASSPORT = "Passport (35x45mm)"
    CUSTOM = "Custom"


# Preset dimensions (width, height)
PRESET_DIMENSIONS = {
    ResizePreset.SQUARE_1080: (1080, 1080),
    ResizePreset.HD_1080P: (1920, 1080),
    ResizePreset.PASSPORT: (413, 531),  # 35x45mm at 300 DPI
}


def get_preset_dimensions(preset: ResizePreset, custom_size: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
    """Get dimensions for a given preset."""
    if preset == ResizePreset.CUSTOM:
        if custom_size is None:
            raise ValueError("Custom size must be provided for CUSTOM preset")
        return custom_size
    return PRESET_DIMENSIONS[preset]


def resize_image(
    image: Image.Image,
    preset: ResizePreset,
    custom_size: Optional[Tuple[int, int]] = None,
    maintain_aspect: bool = True
) -> Image.Image:
    """
    Resize an image to the specified preset or custom dimensions.
    
    Args:
        image: PIL Image object
        preset: ResizePreset enum value
        custom_size: Tuple of (width, height) for custom preset
        maintain_aspect: If True, maintains aspect ratio and fits within dimensions
        
    Returns:
        Resized PIL Image object
    """
    target_width, target_height = get_preset_dimensions(preset, custom_size)
    
    # Convert to RGB if necessary (for JPEG compatibility)
    if image.mode in ('RGBA', 'P', 'LA'):
        # Create a white background for transparent images
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if 'A' in image.mode:
            background.paste(image, mask=image.split()[-1])
            image = background
        else:
            image = image.convert('RGB')
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    if maintain_aspect:
        # Calculate the ratio to fit within target dimensions
        original_width, original_height = image.size
        ratio = min(target_width / original_width, target_height / original_height)
        new_size = (int(original_width * ratio), int(original_height * ratio))
        
        # Resize with high quality
        resized = image.resize(new_size, Image.LANCZOS)
        
        # Create a new image with target dimensions and paste centered
        result = Image.new('RGB', (target_width, target_height), (255, 255, 255))
        paste_x = (target_width - new_size[0]) // 2
        paste_y = (target_height - new_size[1]) // 2
        result.paste(resized, (paste_x, paste_y))
        return result
    else:
        # Stretch to exact dimensions
        return image.resize((target_width, target_height), Image.LANCZOS)


def crop_to_aspect(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """
    Crop image to target aspect ratio (center crop) then resize.
    """
    target_ratio = target_width / target_height
    original_width, original_height = image.size
    original_ratio = original_width / original_height
    
    if original_ratio > target_ratio:
        # Image is wider, crop width
        new_width = int(original_height * target_ratio)
        left = (original_width - new_width) // 2
        image = image.crop((left, 0, left + new_width, original_height))
    else:
        # Image is taller, crop height
        new_height = int(original_width / target_ratio)
        top = (original_height - new_height) // 2
        image = image.crop((0, top, original_width, top + new_height))
    
    return image.resize((target_width, target_height), Image.LANCZOS)


def convert_format(image: Image.Image, target_format: str) -> Tuple[Image.Image, str]:
    """
    Convert image to target format.
    
    Args:
        image: PIL Image object
        target_format: Target format ('JPEG', 'PNG', 'WEBP')
        
    Returns:
        Tuple of (converted image, file extension)
    """
    format_map = {
        'JPEG': ('.jpg', 'RGB'),
        'JPG': ('.jpg', 'RGB'),
        'PNG': ('.png', 'RGBA'),
        'WEBP': ('.webp', 'RGBA'),
    }
    
    target_upper = target_format.upper()
    if target_upper not in format_map:
        raise ValueError(f"Unsupported format: {target_format}")
    
    extension, mode = format_map[target_upper]
    
    # Handle mode conversion
    if mode == 'RGB' and image.mode in ('RGBA', 'P', 'LA'):
        # Create white background for transparent images
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if 'A' in image.mode:
            background.paste(image, mask=image.split()[-1])
            image = background
        else:
            image = image.convert('RGB')
    elif mode == 'RGBA' and image.mode not in ('RGBA', 'LA'):
        if image.mode == 'P':
            image = image.convert('RGBA')
        elif image.mode == 'RGB':
            image = image.convert('RGBA')
    
    return image, extension


def generate_filename(
    original_name: str,
    index: int,
    prefix: str = "",
    suffix: str = "",
    use_numbering: bool = False,
    extension: Optional[str] = None
) -> str:
    """
    Generate a new filename based on options.
    
    Args:
        original_name: Original filename (without extension)
        index: Index for numbering
        prefix: Prefix to add
        suffix: Suffix to add
        use_numbering: Whether to add sequential numbers
        extension: New file extension (including dot)
        
    Returns:
        New filename
    """
    # Remove original extension from name
    if '.' in original_name:
        name_parts = original_name.rsplit('.', 1)
        base_name = name_parts[0]
        orig_ext = '.' + name_parts[1]
    else:
        base_name = original_name
        orig_ext = ''
    
    # Build new name
    new_name = prefix + base_name + suffix
    
    if use_numbering:
        new_name = f"{new_name}_{index:04d}"
    
    # Determine extension
    final_ext = extension if extension else orig_ext
    
    return new_name + final_ext


def process_image(
    image_data: bytes,
    filename: str,
    preset: ResizePreset,
    custom_size: Optional[Tuple[int, int]] = None,
    target_format: Optional[str] = None,
    maintain_aspect: bool = True,
    crop_to_fit: bool = False,
    quality: int = 95
) -> Tuple[bytes, str]:
    """
    Process a single image with resize and/or format conversion.
    
    Args:
        image_data: Raw image bytes
        filename: Original filename
        preset: Resize preset
        custom_size: Custom dimensions for CUSTOM preset
        target_format: Target format (None to keep original)
        maintain_aspect: Maintain aspect ratio when resizing
        crop_to_fit: Crop to fit exact dimensions (overrides maintain_aspect)
        quality: JPEG/WEBP quality (1-100)
        
    Returns:
        Tuple of (processed image bytes, new filename)
    """
    # Open image
    image = Image.open(io.BytesIO(image_data))
    
    # Get target dimensions
    target_width, target_height = get_preset_dimensions(preset, custom_size)
    
    # Resize
    if crop_to_fit:
        # Handle transparency first
        if image.mode in ('RGBA', 'P', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if 'A' in image.mode:
                background.paste(image, mask=image.split()[-1])
                image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        processed = crop_to_aspect(image, target_width, target_height)
    else:
        processed = resize_image(image, preset, custom_size, maintain_aspect)
    
    # Determine output format
    if target_format:
        processed, extension = convert_format(processed, target_format)
        save_format = target_format.upper()
        if save_format == 'JPG':
            save_format = 'JPEG'
    else:
        # Keep original format
        orig_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
        extension = '.' + orig_ext
        save_format = orig_ext.upper()
        if save_format == 'JPG':
            save_format = 'JPEG'
    
    # Save to bytes
    output = io.BytesIO()
    save_kwargs = {'format': save_format}
    
    if save_format in ('JPEG', 'WEBP'):
        save_kwargs['quality'] = quality
        save_kwargs['optimize'] = True
    elif save_format == 'PNG':
        save_kwargs['optimize'] = True
    
    # Ensure correct mode for format
    if save_format == 'JPEG' and processed.mode != 'RGB':
        processed = processed.convert('RGB')
    
    processed.save(output, **save_kwargs)
    
    return output.getvalue(), extension


def batch_process(
    images: List[Dict],
    preset: ResizePreset,
    custom_size: Optional[Tuple[int, int]] = None,
    target_format: Optional[str] = None,
    maintain_aspect: bool = True,
    crop_to_fit: bool = False,
    quality: int = 95,
    prefix: str = "",
    suffix: str = "",
    use_numbering: bool = False,
    progress_callback=None
) -> List[Tuple[bytes, str]]:
    """
    Process multiple images in batch.
    
    Args:
        images: List of dicts with 'data' (bytes) and 'name' (filename)
        preset: Resize preset
        custom_size: Custom dimensions for CUSTOM preset
        target_format: Target format (None to keep original)
        maintain_aspect: Maintain aspect ratio
        crop_to_fit: Crop to fit dimensions
        quality: Output quality
        prefix: Filename prefix
        suffix: Filename suffix
        use_numbering: Add sequential numbers to filenames
        progress_callback: Optional callback function(current, total)
        
    Returns:
        List of tuples (processed_bytes, new_filename)
    """
    results = []
    total = len(images)
    
    for idx, img_dict in enumerate(images):
        # Process image
        processed_data, extension = process_image(
            image_data=img_dict['data'],
            filename=img_dict['name'],
            preset=preset,
            custom_size=custom_size,
            target_format=target_format,
            maintain_aspect=maintain_aspect,
            crop_to_fit=crop_to_fit,
            quality=quality
        )
        
        # Generate new filename
        new_filename = generate_filename(
            original_name=img_dict['name'],
            index=idx + 1,
            prefix=prefix,
            suffix=suffix,
            use_numbering=use_numbering,
            extension=extension
        )
        
        results.append((processed_data, new_filename))
        
        if progress_callback:
            progress_callback(idx + 1, total)
    
    return results


def create_zip(processed_images: List[Tuple[bytes, str]]) -> bytes:
    """
    Create a ZIP file from processed images.
    
    Args:
        processed_images: List of tuples (image_bytes, filename)
        
    Returns:
        ZIP file as bytes
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for image_data, filename in processed_images:
            zip_file.writestr(filename, image_data)
    
    return zip_buffer.getvalue()


def get_image_info(image_data: bytes) -> Dict:
    """
    Get information about an image.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Dict with width, height, format, mode, size_kb
    """
    image = Image.open(io.BytesIO(image_data))
    return {
        'width': image.width,
        'height': image.height,
        'format': image.format,
        'mode': image.mode,
        'size_kb': len(image_data) / 1024
    }
