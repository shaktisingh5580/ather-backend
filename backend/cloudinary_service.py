"""
Cloudinary Image Upload Service
Uploads vehicle gate screenshots to Cloudinary and returns public URLs.
Used by Guardian Mode to attach gate photos to WhatsApp alerts.
"""

import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def upload_gate_image(image_path_or_url: str, plate_number: str, gate_id: str = "gate_main") -> str:
    """
    Upload a gate camera image to Cloudinary.

    Args:
        image_path_or_url: Local file path OR a URL to the image.
        plate_number: Vehicle plate for tagging/naming.
        gate_id: Which gate captured this image.

    Returns:
        Public URL of the uploaded image.
    """
    public_id = f"parking_scet/guardian/{plate_number}_{gate_id}_{int(__import__('time').time())}"

    result = cloudinary.uploader.upload(
        image_path_or_url,
        public_id=public_id,
        folder="parking_scet/guardian",
        tags=[plate_number, gate_id, "guardian_alert"],
        overwrite=True,
        resource_type="image",
    )

    return result.get("secure_url", result.get("url", ""))


def upload_gate_image_from_bytes(image_bytes: bytes, plate_number: str, gate_id: str = "gate_main") -> str:
    """
    Upload raw image bytes (e.g. from a camera frame) to Cloudinary.

    Args:
        image_bytes: Raw image data (JPEG/PNG bytes).
        plate_number: Vehicle plate for tagging.
        gate_id: Which gate captured this.

    Returns:
        Public URL of the uploaded image.
    """
    import io
    public_id = f"parking_scet/guardian/{plate_number}_{gate_id}_{int(__import__('time').time())}"

    result = cloudinary.uploader.upload(
        io.BytesIO(image_bytes),
        public_id=public_id,
        folder="parking_scet/guardian",
        tags=[plate_number, gate_id, "guardian_alert"],
        overwrite=True,
        resource_type="image",
    )

    return result.get("secure_url", result.get("url", ""))


def get_placeholder_image_url() -> str:
    """Return a placeholder image URL for mock/demo mode when no real camera is available."""
    return "https://res.cloudinary.com/dolt93yno/image/upload/v1772825066/Screenshot_2026-03-07_005322_y6iiw4.png"
