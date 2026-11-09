
import os
import uuid
from PIL import Image, UnidentifiedImageError
from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.report_media import FloodReportMedia


MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp"
}


def validate_image_file(uploaded_file):
    filename = uploaded_file.filename or ""
    extension = os.path.splitext(filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Only JPEG, PNG and WebP images are allowed")

    # Check the actual file size.
    uploaded_file.stream.seek(0, os.SEEK_END)
    file_size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0)

    if file_size == 0:
        raise ValueError("Uploaded image is empty")

    if file_size > MAX_FILE_SIZE:
        raise ValueError("Each image must be 5 MB or smaller")

    # Inspect the file signature.
    signature = uploaded_file.stream.read(12)
    uploaded_file.stream.seek(0)

    is_jpeg = signature.startswith(b"\xff\xd8\xff")
    is_png = signature.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = (
        signature.startswith(b"RIFF")
        and signature[8:12] == b"WEBP"
    )

    valid_signature = (
        (extension in {".jpg", ".jpeg"} and is_jpeg)
        or (extension == ".png" and is_png)
        or (extension == ".webp" and is_webp)
    )

    if not valid_signature:
        raise ValueError("File content does not match its image extension")
    # Ask Pillow to verify that the file is a readable image.
    try:
        image = Image.open(uploaded_file.stream)

        expected_formats = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".webp": "WEBP"
        }

        if image.format != expected_formats[extension]:
            raise ValueError("Image format does not match its extension")

        image.verify()

    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise ValueError("Uploaded file is not a valid image") from error

    finally:
        uploaded_file.stream.seek(0)


    return extension, file_size


def save_report_media(report, uploaded_files):
    upload_directory = os.path.join(
        current_app.instance_path,
        "uploads",
        "reports"
    )

    os.makedirs(upload_directory, exist_ok=True)

    saved_paths = []
    media_records = []

    try:
        for uploaded_file in uploaded_files:
            extension, file_size = validate_image_file(uploaded_file)

            # Generate a unique filename.
            unique_filename = f"{uuid.uuid4().hex}{extension}"

            absolute_path = os.path.join(
                upload_directory,
                unique_filename
            )

            uploaded_file.save(absolute_path)
            saved_paths.append(absolute_path)

            original_filename = secure_filename(
                uploaded_file.filename or "image"
            )[:255]

            relative_path = os.path.join(
                "uploads",
                "reports",
                unique_filename
            ).replace("\\", "/")

            media = FloodReportMedia(
                report_id=report.id,
                file_path=relative_path,
                original_filename=original_filename,
                mime_type=ALLOWED_EXTENSIONS[extension],
                file_size_bytes=file_size
            )

            db.session.add(media)
            media_records.append(media)

        # Save all media records in one transaction.
        db.session.commit()

        return media_records

    except Exception:
        db.session.rollback()

        # Remove files if the database operation fails.
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)

        raise

# to send requested report image to user from backend according to report
def get_report_media(report_id):
    media_records = (
        FloodReportMedia.query
        .filter_by(report_id=report_id)
        .order_by(FloodReportMedia.uploaded_at.asc())
        .all()
    )

    return [
        {
            "media_id": media.id,
            "report_id": media.report_id,
            "original_filename": media.original_filename,
            "mime_type": media.mime_type,
            "file_size_bytes": media.file_size_bytes,
            "image_url": (
                f"/api/reports/{report_id}/media/{media.id}"
            ),
            "uploaded_at": media.uploaded_at.isoformat()
        }
        for media in media_records
    ]

#to delete image direcly by user
def delete_report_media(report_id, media_id):
    media = FloodReportMedia.query.filter_by(
        id=media_id,
        report_id=report_id
    ).first()

    if media is None:
        return False

    upload_directory = os.path.join(
        current_app.instance_path,
        "uploads",
        "reports"
    )

    filename = os.path.basename(media.file_path)
    absolute_path = os.path.join(upload_directory, filename)

    try:
        # Delete the database record first.
        db.session.delete(media)
        db.session.commit()

        # Delete the corresponding physical image file.
        if os.path.exists(absolute_path):
            os.remove(absolute_path)

        return True

    except Exception:
        db.session.rollback()
        raise