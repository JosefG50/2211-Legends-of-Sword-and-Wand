from sqlalchemy import Column, String, Integer, ForeignKey # Add ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database import Base

class PartyModel(Base):
    __tablename__ = "parties"
    # This flag is important since PvE also touches this table
    __table_args__ = {'extend_existing': True} 

    id = Column(Integer, primary_key=True, index=True)
    
    # 1. Add the ForeignKey link to the users table
    
    name = Column(String)

    # 2. Add the back-reference to match the one in UserModel
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", back_populates="parties")