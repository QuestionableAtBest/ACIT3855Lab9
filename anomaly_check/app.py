# Logging and storage
import json,logging,logging.config
# API packages
import os
import yaml,httpx,connexion
from connexion import NoContent
from datetime import datetime,timezone
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import time
from pykafka import KafkaClient

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("anomaly.yaml", base_path="/anomaly_check", strict_validation=True,validate_responses=True)
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
#Pull app config (variables)
with open('./configs/anomaly_check_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

#Pull logging config
with open("./configs/anomaly_check_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

#create logger
logger = logging.getLogger('basicLogger')

def update_anomalies():
    logger.debug("Update anomalies started")
    start = time.perf_counter_ns()
    jsonny = {"anomaly_list":[]}
    count = 0
    client = KafkaClient(hosts=f"{app_config['datastore']['hostname']}:{app_config['datastore']['port']}")
    topic = client.topics[str.encode(app_config["datastore"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    #Change these two to be the environment variables
    max_hr = os.environ['MAX_HR']
    min_weight = os.environ['MIN_WEIGHT']
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data["type"] == "watch_event":
            if data["payload"]["avg_heart_rate"] > max_hr:
                logger.debug(f"Anomaly detected with heartrate {data["payload"]["avg_heart_rate"]} exceeding {max_hr}")
                count += 1
                anomaly = {"event_id": data["payload"]["device_id"],
                           "trace_id":str(data["payload"]["trace_id"]),
                           "event_type":data["type"],
                           "anomaly_type":"Too high",
                           "description":f"Anomaly detected with heartrate {data["payload"]["avg_heart_rate"]} exceeding {max_hr}"}
                jsonny["anomaly_list"].append(anomaly)
                
        elif data["type"] == "scale_event":
            if data["payload"]["weight"] < min_weight:
                logger.debug(f"Anomaly detected with weight {data["payload"]["weight"]} below {min_weight}")
                count += 1
                anomaly = {"event_id": data["payload"]["scale_id"],
                           "trace_id":str(data["payload"]["trace_id"]),
                           "event_type":data["type"],
                           "anomaly_type":"Too low",
                           "description":f"Anomaly detected with weight {data["payload"]["weight"]} below {min_weight}"}
                jsonny["anomaly_list"].append(anomaly)

    with open(app_config["datastore"]["data_path"], 'w') as s:
        jsonned = json.dumps(jsonny)
        s.write(jsonned)
    end = time.perf_counter_ns()
    processing_time_ms = (end - start) / 1000000
    logger.info(f"Anomaly checks completed | processing_time_ms= {processing_time_ms}")
    return {"anomaly_count":count},201

def get_anomalies(event_type=None):
    logger.debug("Requeset received!")
    if event_type not in [None,"scale","watch"]:
        logger.debug("Request type does not match scale, watch or empty.")
        return "Invalid event type", 400
    try:
        with open(app_config["datastore"]["data_path"], 'r') as data:
            data = json.load(data)
            if len(data["anomaly_list"]) == 0:
                logger.debug("JSON has no anomalies")
                return {}, 204
            if event_type == "scale":
                listy = []
                for data in data["anomaly_list"]:
                    if data["anomaly_list"]["type"] == "scale_event":
                        listy.append(data)
                logger.debug("Returning anomaly list for scale events")
                return listy, 200
            elif event_type == "watch":
                for data in data["anomaly_list"]:
                    if data["anomaly_list"]["type"] == "watch_event":
                        listy.append(data)
                logger.debug("Returning anomaly list for watch events")
                return listy, 200
            else:
                logger.debug("No filter selected, returning full list of anomalies")
                return data["anomaly_list"],200
    except FileNotFoundError:
        logger.debug("Anomaly check has not been ran before!")
        return {"message":"Not found"}, 404
if __name__ == "__main__":
    logger.info(f"Service start up. Threshholds are max heart rate: {250} for watch events and min weight: {30} for scale events")
    app.run(port=8300, host="0.0.0.0")