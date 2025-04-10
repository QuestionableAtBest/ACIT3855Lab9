import connexion
import time
import yaml
import logging
import logging.config
from models import KafkaProducer
from connexion import NoContent
from datetime import datetime as dt
import json
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("fitscale.yaml", base_path="/receiver",strict_validation=True,validate_responses=True)

with open('./configs/receiver_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open("./configs/receiver_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')
kaf_prod = KafkaProducer(f"{app_config['events']['hostname']}:{app_config['events']['port']}",str.encode(app_config['events']['topic']))
def report_watch(body):
    trace_id = time.time_ns()
    logger.info(f"Received event watch results with trace id of {trace_id}")
    body["trace_id"] = trace_id
    msg = { "type": "watch_event",
        "datetime": dt.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    kaf_prod.send_request(msg_str.encode('utf-8'))
    return NoContent, 201

def report_scale(body):
    trace_id = time.time_ns()
    logger.info(f"Received event watch results with trace id of {trace_id}")
    body["trace_id"] = trace_id
    msg = { "type": "scale_event",
        "datetime": dt.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    kaf_prod.send_request(msg_str.encode('utf-8'))
    return NoContent, 201

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")