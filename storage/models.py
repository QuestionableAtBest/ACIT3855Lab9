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

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "exercise_type": self.exercise_type,
            "distance": self.distance,
            "duration": self.duration,
            "avg_heart_rate": self.avg_heart_rate,
            "timestamp": self.timestamp,
            "date_created": self.date_created,
            "trace_id": self.trace_id
            }

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

    def to_dict(self):
        return {
            "id": self.id,
            "scale_id": self.scale_id,
            "weight": self.weight,
            "age": self.age,
            "gender": self.gender,
            "body_fat_percentage": self.body_fat_percentage,
            "height": self.height,
            "timestamp": self.timestamp,
            "date_created": self.date_created,
            "trace_id": self.trace_id
            }