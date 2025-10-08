from sqlalchemy import Column, Integer, String, Text
from . import Base

class InvestigationReviewReasonList(Base):
    __tablename__ = "investigation_review_reason_list"

    id = Column(Integer, primary_key=True, index=True)
    reason = Column(String(255), nullable=False)
    reason_description = Column(Text)
