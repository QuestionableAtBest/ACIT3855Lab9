import connexion
import yaml
import logging
import logging.config
from pykafka import KafkaClient
import json
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("fitscale.yaml", strict_validation=True,validate_responses=True)
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
with open('/configs/analyzer_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open("/configs/analyzer_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

def get_watch(index):
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    counter = 0
    payload = { "message": f"No message at index {index}!"}
    status_code = 404
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        # Look for the index requested and return the payload with 200 status code
        if data["type"] == "watch_event":
            if counter == index:
                payload = data["payload"]
                status_code = 200
            counter += 1
    return payload, status_code

def get_scale(index):
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    counter = 0
    payload = { "message": f"No message at index {index}!"}
    status_code = 404
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        # Look for the index requested and return the payload with 200 status code
        if data["type"] == "scale_event":
            if counter == index:
                payload = data["payload"]
                status_code = 200
            counter += 1
    return payload, status_code

def get_stats():
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    count_scale = 0
    count_watch = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data["type"] == "watch_event":
            count_watch += 1
        else:
            count_scale += 1
    return {"num_w": count_watch,
            "num_s": count_scale}, 200
    


if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")