from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Time,
    Boolean,
    Text,
    Numeric,
    func,
    UniqueConstraint
)
from typing import Optional
from . import Base

class CaseMain(Base):
    __tablename__ = "case_main"
    __table_args__ = (
        UniqueConstraint('source_ack_no', name='case_main_source_ack_no_key'),
    )

    case_id = Column(Integer, primary_key=True, index=True)
    case_type = Column(String(50))
    source_ack_no = Column(String(50), unique=True)
    source_bene_accno = Column(String(18))
    acc_num = Column(String(18))
    cust_id = Column(String(50))
    creation_date = Column(Date, server_default=func.current_date())
    creation_time = Column(Time, server_default=func.current_time())
    closing_date = Column(Date, nullable=True)  # New field for tracking when case is closed
    is_operational = Column(Boolean, server_default="false")
    status = Column(String(20))
    short_dn = Column(String(100))
    long_dn = Column(Text)
    decision_type = Column(String(50))
    created_by = Column(String(50))
    decided_by = Column(String(50))
    location = Column(String(100))
    disputed_amount = Column(Numeric(15, 2))

# Add CRUD operations and other functions as needed.

if __name__ == "__main__":
    from . import create_tables
    create_tables() 