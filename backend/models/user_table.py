from sqlalchemy import (
    Column,
    String,
    func
)
from typing import List, Optional
from . import Base

class UserTable(Base):
    __tablename__ = "user_table"

    user_id = Column(String(255), primary_key=True, index=True)
    user_name = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False, server_default="others")
    dept = Column(String(50))

# CRUD operations and other functions can be added as needed.

if __name__ == "__main__":
    from . import create_tables
    create_tables()