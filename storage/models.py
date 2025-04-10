import time
import random
from pykafka import KafkaClient
from pykafka.common import OffsetType
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, BigInteger, Float, func
from  pykafka.exceptions import KafkaException 
import logging

logger = logging.getLogger(__name__)
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
class KafkaConsumer:
    def __init__(self, hostname, topic):
        self.hostname = hostname
        self.topic = topic
        self.client = None
        self.consumer = None
        self.connect()

    def connect(self):
        """Infinite loop: will keep trying"""
        while True:
            logger.debug("Trying to connect to Kafka...")
            if self.make_client():
                if self.make_consumer():
                    break
            # Sleeps for a random amount of time (0.5 to 1.5s)
            time.sleep(random.randint(500, 1500) / 1000)

    def make_client(self):
        """
        Runs once, makes a client and sets it on the instance.
        Returns: True (success), False (failure)
        """
        if self.client is not None:
            return True
        try:
            self.client = KafkaClient(hosts=self.hostname)
            logger.info("Kafka client created!")
            return True
        except KafkaException as e:
            msg = f"Kafka error when making client: {e}"
            logger.warning(msg)
            self.client = None
            self.consumer = None
            return False

    def make_consumer(self):
        """
        Runs once, makes a consumer and sets it on the instance.
        Returns: True (success), False (failure)
        """
        if self.consumer is not None:
            return True
        if self.client is None:
            return False
        try:
            topic = self.client.topics[self.topic]
            self.consumer = topic.get_simple_consumer(
                consumer_group=b'events',
                reset_offset_on_start=False,
                auto_offset_reset=OffsetType.LATEST
            )
            return True
        except KafkaException as e:
            msg = f"Kafka error when making consumer: {e}"
            logger.warning(msg)
            self.client = None
            self.consumer = None
            return False

    def make_producer(self):
        """
        Runs once, makes a producer and sets it on the instance.
        Returns: True (success), False (failure)
        """
        if self.producer is not None:
            return True
        if self.client is None:
            return False
        try:
            topic = self.client.topics[self.topic]
            self.producer = topic.get_sync_producer()
        except KafkaException as e:
            msg = f"Make error when making producer: {e}"
            logger.warning(msg)
            self.client = None
            self.producer = None
            return False
        
    def messages(self):
        """Generator method that catches exceptions in the consumer loop"""
        if self.consumer is None:
            self.connect()
        while True:
            try:
                for msg in self.consumer:
                    yield msg
            except KafkaException as e:
                msg = f"Kafka issue in consumer: {e}"
                logger.warning(msg)
                self.client = None
                self.consumer = None
                self.connect()

    def commit(self):
        if self.consumer is not None:
            self.consumer.commit_offsets()
            logger.debug("Offsets committed!")
        else:
            logger.warning("No consumer initialized!")

    def produce(self,message):
        if self.producer is None:
            self.connect()
        try:
            self.producer.producer(message.encode('utf-8'))
            logger.info("Message added to Kafka")
            return True
        except KafkaException as e:
            logger.warning(f"Kafka error when producing message:{e}")
            self.client = None
            self.producer = None