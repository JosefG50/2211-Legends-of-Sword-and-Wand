from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship # Add this
from sqlalchemy.sql import func
from infrastructure.database import Base

class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True} 

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add this so we can access user.parties
    parties = relationship("PartyModel", back_populates="user", foreign_keys="[PartyModel.user_id]")