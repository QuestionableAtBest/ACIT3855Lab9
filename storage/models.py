from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, BigInteger, Float, func
import time

class Base(DeclarativeBase):
    pass

class Watch(Base):
    __tablename__ = "watch"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    user_id = mapped_column(String(50), nullable=False)
    exercise_type = mapped_column(String(50), nullable=False)
    distance = mapped_column(Float,nullable=False)
    duration = mapped_column(Float,nullable=False)
    avg_heart_rate = mapped_column(Float,nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    trace_id = mapped_column(BigInteger,nullable=False,default=time.time_ns())

class Scale(Base):
    __tablename__ = "scale"
    id = mapped_column(Integer, primary_key=True)
    scale_id = mapped_column(String(50), nullable=False)
    weight = mapped_column(Integer, nullable=False)
    age = mapped_column(Integer, nullable=False)
    gender = mapped_column(String(50), nullable=False)
    body_fat_percentage = mapped_column(Float,nullable=False)
    height = mapped_column(Float, nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    trace_id = mapped_column(BigInteger,nullable=False, default=time.time_ns())