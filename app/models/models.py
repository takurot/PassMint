from sqlalchemy import Column, String, Text, ForeignKey, CheckConstraint, TIMESTAMP, JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .base import Base

class Org(Base):
    __tablename__ = "orgs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    designs = relationship("Design", back_populates="org", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    line_user_id = Column(String(64), unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    passes = relationship("Pass", back_populates="user", cascade="all, delete-orphan")


class Design(Base):
    __tablename__ = "designs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID, ForeignKey("orgs.id", ondelete="CASCADE"))
    template_json = Column(JSONB, nullable=False)
    preview_url = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    org = relationship("Org", back_populates="designs")
    passes = relationship("Pass", back_populates="design")


class Pass(Base):
    __tablename__ = "passes"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
    design_id = Column(UUID, ForeignKey("designs.id", ondelete="SET NULL"))
    platform = Column(String(10))
    serial = Column(String(32), unique=True, nullable=False)
    deep_link = Column(Text, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True))
    issued_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "platform IN ('apple', 'google')",
            name="platform_type_check"
        ),
    )

    # Relationships
    user = relationship("User", back_populates="passes")
    design = relationship("Design", back_populates="passes") 