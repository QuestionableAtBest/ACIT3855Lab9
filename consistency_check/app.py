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
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("consistency_check.yaml", base_path="/consistency_check", strict_validation=True,validate_responses=True)
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
with open('./configs/consistency_check_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

#Pull logging config
with open("./configs/consistency_check_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

#create logger
logger = logging.getLogger('basicLogger')

def run_consistency_checks():
    start = time.perf_counter_ns()
    logger.info("Beginning consistency check!")
    proccessing_count = httpx.get(f"http://{app_config["datastore"]["vm_hostname"]}/{app_config["datastore"]["proc_hostname"]}/stats").json()
    analyzer_count = httpx.get(f"http://{app_config["datastore"]["vm_hostname"]}/{app_config["datastore"]["ana_hostname"]}/stats").json()
    storage_count = httpx.get(f"http://{app_config["datastore"]["vm_hostname"]}/{app_config["datastore"]["store_hostname"]}/count").json()
    storage_watch_list = httpx.get(f"http://{app_config["datastore"]["vm_hostname"]}/{app_config["datastore"]["store_hostname"]}/watchlist").json()
    storage_scale_list = httpx.get(f"http://{app_config["datastore"]["vm_hostname"]}/{app_config["datastore"]["store_hostname"]}/scalelist").json()
    analyzer_watch_list = httpx.get(f"http://{app_config["datastore"]["vm_hostname"]}/{app_config["datastore"]["ana_hostname"]}/watchlist").json()
    analyzer_scale_list = httpx.get(f"http://{app_config["datastore"]["vm_hostname"]}/{app_config["datastore"]["ana_hostname"]}/scalelist").json()
    missing_in_db = 0
    missing_in_queue = 0
    jsonny = {"counts":{
                "db":{"watch":storage_count["watch_count"],
                    "scale":storage_count["scale_count"]},
                "queue":{"watch":analyzer_count["num_w"],
                        "scale":analyzer_count["num_s"]},
                "processing":{"watch":proccessing_count["cum_watch"],
                            "scale":proccessing_count["cum_scale"]}},
              "not_in_db":[],
              "not_in_queue":[],
              "last_updated": datetime.now().isoformat()}
    #Checking watch counts
    watch_storage_traces = [watch_event["trace_id"] for watch_event in storage_watch_list]
    watch_analyzer_traces = [watch_event["trace_id"] for watch_event in analyzer_watch_list]
    print(analyzer_watch_list)
    print(watch_analyzer_traces)
    print(watch_storage_traces)
    for watch_event in storage_watch_list:
        if watch_event["trace_id"] not in watch_analyzer_traces:
            missing_in_db += 1
            watch_event["type"] = "watch"
            jsonny["not_in_db"].append(watch_event)
    for watch_event in analyzer_watch_list:
        if watch_event["trace_id"] not in watch_storage_traces:
            missing_in_queue += 1
            watch_event["type"] = "watch"
            jsonny["not_in_queue"].append(watch_event)

    #Checking scale counts
    scale_storage_traces = [scale_event["trace_id"] for scale_event in storage_scale_list]
    print("=========================")
    print(scale_storage_traces)
    scale_analyzer_traces = [scale_event["trace_id"] for scale_event in analyzer_scale_list]
    print(scale_analyzer_traces)
    for scale_event in storage_scale_list:
        if scale_event["trace_id"] not in scale_analyzer_traces:
            missing_in_db += 1
            scale_event["type"] = "scale"
            jsonny["not_in_db"].append(scale_event)
    for scale_event in analyzer_scale_list:
        if scale_event["trace_id"] not in scale_storage_traces:
            missing_in_queue += 1
            scale_event["type"] = "scale"
            jsonny["not_in_queue"].append(scale_event)

    with open(app_config["datastore"]["data_path"], 'w') as s:
        jsonned = json.dumps(jsonny)
        s.write(jsonned)
    end = time.perf_counter_ns()
    processing_time_ms = (end - start) / 1000000
    logger.info(f"Consistency checks completed | processing_time_ms= {processing_time_ms} | missing_in_db: {missing_in_db} | missing_in_queue: {missing_in_queue}")
    return {"processing_time_ms":int(processing_time_ms)}

def get_checks():
    try:
        with open(app_config["datastore"]["data_path"], 'r') as s:
            jsonny = json.load(s)
            return jsonny, 200
    except FileNotFoundError:
        return {"message":"Update has not been ran yet"}, 404

if __name__ == "__main__":
    app.run(port=8120, host="0.0.0.0")