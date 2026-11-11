
from datetime import datetime, timezone

from app.extensions import db
from sqlalchemy import CheckConstraint

class FloodReportMedia(db.Model):
    __tablename__ = "flood_report_media"
    # Enforce valid image sizes and supported image MIME types.
    __table_args__ = (
        CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 5242880",
            name="check_report_media_file_size"
        ),
        CheckConstraint(
            "mime_type IN ('image/jpeg', 'image/png', 'image/webp')",
            name="check_report_media_mime_type"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    report_id = db.Column(
        db.Integer,
        db.ForeignKey("flood_reports.id"),
        nullable=False,
        index=True
    )

    file_path = db.Column(
        db.String(500),
        unique=True,
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    mime_type = db.Column(
        db.String(100),
        nullable=False
    )

    file_size_bytes = db.Column(
        db.Integer,
        nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    report = db.relationship(
        "FloodReport",
        backref=db.backref(
            "media_files",
            lazy=True,
            passive_deletes="all"
        )
    )
    def __repr__(self):
        return f"<FloodReportMedia {self.id}: {self.original_filename}>"
