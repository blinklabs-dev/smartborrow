from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from ..core.database import Base

class SnowflakeConnection(Base):
    __tablename__ = "snowflake_connections"

    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String, index=True, nullable=False)
    username = Column(String, nullable=False)
    encrypted_password = Column(LargeBinary, nullable=False) # Storing encrypted data
    role = Column(String, nullable=True)
    warehouse = Column(String, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="snowflake_connections")
