# Logging and storage
import json,logging,logging.config
# Mean for averages
from statistics import mean 
# API packages
import yaml,httpx,connexion
from connexion import NoContent
from datetime import datetime,timezone
import time
# Proccessing needed
import apscheduler.schedulers.background as apsched
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("fitscale.yaml", strict_validation=True,validate_responses=True)

#Pull app config (variables)
with open('processing/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

#Pull logging config and create logger
with open("processing/log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

def populate_stats():
    logger.info("Periodic statistics gathering has begun!")
    curtime = time.time()
    try:
        #Open the .json. Assuming it exists, get most recent event datetime and current time (To be used in the get request)
        with open(app_config["datastore"]["filename"], 'r') as current:
            old_data = json.load(current)
            last_updated = old_data["time_updated"]

        # Magic functions that gets the data necessary
        # Should add response codes to make sure the functions are working, ask Tim about it, something in the storage/app.py should give a response code?
        scaleContent = httpx.get(
            app_config["scalestats"]["url"], 
            params={"start_timestamp":last_updated,"end_timestamp":curtime}
        )

        watchContent = httpx.get(
            app_config["watchstats"]["url"], 
            params={"start_timestamp":last_updated,"end_timestamp":curtime}
        )

        logger.info("JSON file found, collecting new stats!")
        exercise_durs = [dict_item["duration"] for dict_item in watchContent]
        distances = [dict_item["distance"] for dict_item in watchContent]
        heart_reads = [dict_item["avg_heart_rate"] for dict_item in watchContent]
        weights = [dict_item["weight"] for dict_item in scaleContent]

        new_data = {
            "watchstore": {
                "durations":exercise_durs,
                "distances":distances,
                "heart_rates":heart_reads,
            },
            "scalestore": {
                "weights": weights
            },
            "time_updated": curtime
        }

        logger.info("Stats collected! Writing to JSON")
        json_new_data = json.dump(new_data)
        #Write json
        with open(app_config["datastore"]["filename"],'w') as current:
            current.write(json_new_data)
            #A debug message with the timestamp
            logger.debug(f"JSON Updated on {curtime}")

        #An info message on completion.
        logger.info("Values added to data.json!")
        return NoContent, 200
    except FileNotFoundError:
        #.json does not exist, creating and populating with default values
        logger.info("No json detected, generating default")
        #No json file yet, make it with defaults.
        default = {
            "watchstore": {
                "durations":[0],
                "distances":[0],
                "heart_rates":[0],
            },
            "scalestore": {
                "weights": [0]
            },
            "time_updated": 0 #The epoch in utc
        }
        default_data = json.dumps(default)
        with open(app_config["datastore"]["filename"],'w') as current:
            current.write(default_data)
        logger.info("Processing logger finished on default route!")
        return NoContent, 200

def get_stats():
    logger.info("Get Stats Processing Request received")
    try:
        with open(app_config["datastore"]["filename"],'r') as current:
            loaded = json.load(current)
        
            #Calculate the stats needed
            #In watch:
            avg_ex_dur = mean(loaded["watchstore"]["durations"])
            avg_dist_trav = mean(loaded["watchstore"]["distances"])
            max_hr = max(loaded["watchstore"]["heart_rates"])
            
            #In scale:
            max_weight, min_weight = max(loaded["scalestore"]["weight"]), min(loaded["scalestore"]["weight"])

            #UTC Time to a human readable timestamp
            human_time = datetime.fromtimestamp(loaded["time_updated"], tz=timezone.utc)
            #convert to dictionary
            new_data = {
                "avg_exercise_duration":avg_ex_dur,
                "avg_distance_traveled":avg_dist_trav,
                "max_hr_readings":max_hr,
                "max_weight":max_weight,
                "min_weight":min_weight,
                "time_updated":human_time
            }
            logger.debug(f"{new_data}")
            #convert to json
            datajson = json.dump(new_data)
            with open("./processing/stats.json", "w") as current:
                current.write(datajson)
            logger.info("Statistics successfully updated!")

    except FileNotFoundError:
        logger.error("Statistics do not exist")
        return NoContent, 404

def init_scheduler():
    sched = apsched.BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
                'interval',
                seconds=app_config['scheduler']['interval'])
    sched.start()

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100)
