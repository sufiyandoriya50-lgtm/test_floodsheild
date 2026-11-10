
from datetime import datetime, timezone

from app.extensions import db


"""
    Stores location-specific flood-risk assessments,
    including the score and individual risk-factor details.
    """
class RiskAssessment(db.Model):

    __tablename__ = "risk_assessments"

    # Unique database ID for each risk assessment.
    id = db.Column(db.Integer, primary_key=True)

    # Geographic location where flood risk was assessed.
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Final risk classification: low, moderate, high, severe,
    # or insufficient_data.
    risk_level = db.Column(db.String(30), nullable=False)

    # Numerical combined risk score, from 0 to 100.
    # Nullable because an assessment may have insufficient data.
    risk_score = db.Column(db.Float, nullable=True)

    # Stores individual factor results as structured JSON.
    # Example: rainfall score, community report score,
    # historical flood score and historical weather context.
    factor_details = db.Column(db.JSON, nullable=True)

    # Percentage of weighted risk factors available for assessment.
    data_completeness = db.Column(db.Float, nullable=True)

    # Human-readable explanation of the assessment.
    description = db.Column(db.Text, nullable=True)

    # Date and time when the assessment was created.
    assessed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return (
            f"<RiskAssessment {self.id}: "
            f"{self.risk_level} ({self.risk_score})>"
        )
