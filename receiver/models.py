import time
import random
from pykafka import KafkaClient
from pykafka.common import OffsetType
from  confluent_kafka import KafkaException 
import logging

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self, hostname, topic):
        self.hostname = hostname
        self.client = KafkaClient(str.encode(hostname), str.encode(topic))
        self.producer = None
        self.connect()
    def connect(self):
        """Infinite loop: will keep trying"""
        while True:
            logger.debug("Trying to connect to Kafka...")
            if self.make_producer():
                break
            # Sleeps for a random amount of time (0.5 to 1.5s)
            time.sleep(random.randint(500, 1500) / 1000)

    def make_producer(self):
        """
        Runs once, makes a producer and sets it on the instance.
        Returns: True (success), False (failure)
        """
        if self.producer is not None:
            return True
        try:
            self.producer = self.client.topic.get_sync_producer()
            logger.info("Kafka producer created!")
            return True
        except KafkaException as e:
            msg = f"Kafka error when making client: {e}"
            logger.warning(msg)
            self.producer = None
            return False

    def send_request(self, message):
        """Producer method to send request"""
        if self.producer is not None:
            self.producer.producer.produce(message.encode('utf-8'))