from sqlalchemy import Column, Date, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import date
from app.core.database import Base


class ApiKeyUsageDaily(Base):
    __tablename__ = "api_key_usage_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False, index=True)
    usage_date = Column(Date, nullable=False, default=date.today)
    request_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("api_key_id", "usage_date", name="uq_api_key_usage_daily"),
    )

    api_key = relationship("ApiKey")
