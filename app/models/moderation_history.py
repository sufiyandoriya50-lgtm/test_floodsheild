from datetime import datetime, timezone

from app.extensions import db
from sqlalchemy import CheckConstraint

class ModerationHistory(db.Model):
    __tablename__ = "moderation_history"
        # Enforce valid moderation statuses at the database level.
    __table_args__ = (
        CheckConstraint(
            "previous_status IN ('pending', 'verified', 'rejected')",
            name="check_moderation_previous_status"
        ),
        CheckConstraint(
            "new_status IN ('pending', 'verified', 'rejected')",
            name="check_moderation_new_status"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    report_id = db.Column(
        db.Integer,
        db.ForeignKey("flood_reports.id"),
        nullable=False,
        index=True
    )

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    previous_status = db.Column(
        db.String(20),
        nullable=False
    )

    new_status = db.Column(
        db.String(20),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    report = db.relationship(
        "FloodReport",
        backref=db.backref(
            "moderation_history",
            lazy=True,
            passive_deletes="all"
        )
    )
    admin = db.relationship("User")

    def __repr__(self):
        return (
            f"<ModerationHistory report={self.report_id} "
            f"{self.previous_status}->{self.new_status}>"
        )