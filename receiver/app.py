import connexion
import httpx
import time
import yaml
import logging
import logging.config
from connexion import NoContent
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("fitscale.yaml", strict_validation=True,validate_responses=True)

with open('receiver/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open("receiver/log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

def report_watch(body):
    trace_id = time.time_ns()
    logger.info(f"Received event watch results with trace id of {trace_id}")
    body["trace_id"] = trace_id
    r = httpx.post(app_config["watchstore"]["url"],json=body)
    logger.info(f"Response for event watch results, id:{trace_id} has status {r.status_code}")
    return NoContent,r.status_code

def report_scale(body):
    trace_id = time.time_ns()
    body["trace_id"] = trace_id
    logger.info(f"Received event scale results with trace id of {trace_id}")
    r = httpx.post(app_config["scalestore"]["url"],json=body)
    logger.info(f"Response for event scale results, id:{trace_id} has status {r.status_code}")
    return NoContent, r.status_code

if __name__ == "__main__":
    app.run(port=8080)