
from datetime import datetime, timezone

from app.extensions import db


class FloodReportMedia(db.Model):
    __tablename__ = "flood_report_media"

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
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):
        return f"<FloodReportMedia {self.id}: {self.original_filename}>"
