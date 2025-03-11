# Logging and storage
import json,logging,logging.config
# API packages
import yaml,httpx,connexion
from connexion import NoContent
from datetime import datetime,timezone
# Proccessing needed
import apscheduler.schedulers.background as apsched
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("fitscale.yaml", strict_validation=True,validate_responses=True)

#Pull app config (variables)
with open('./configs/processing_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

#Pull logging config and create logger
with open("./configs/processing_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

def populate_stats():
    logger.info("Periodic statistics gathering has begun!")
    curtime = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    try:
        #Open the .json. Assuming it exists, get most recent event datetime and current time (To be used in the get request)
        with open(app_config["datastore"]["filename"], 'r') as current:
            old_data = json.load(current)
            running_watch = old_data["cum_watch"]
            running_scale = old_data["cum_scale"]
            old_max_duration = old_data["max_duration"]
            old_max_distance_traveled = old_data["max_distance_traveled"]
            old_max_weight = old_data["max_weight"]
            old_min_weight = old_data["min_weight"]
            last_updated = old_data["recent_timestamp"]

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

        #Httpx returns Response objects, need to convert to JSON

        logger.info("JSON file found, collecting new stats!")
        if scaleContent.status_code == 200 and watchContent.status_code == 200:
            #Getting list of durations, distances and weights
            scaleContent = scaleContent.json()
            watchContent = watchContent.json()
            weights = [dict_item["weight"] for dict_item in scaleContent]
            durations = [dict_item["duration"] for dict_item in watchContent]
            distances = [dict_item["distance"] for dict_item in watchContent]
            #Timestamp data to get the most recent between scale and watch later
            scaleTimes = max([dict_item['date_created'] for dict_item in scaleContent], default=last_updated)
            watchTimes = max([dict_item['date_created'] for dict_item in watchContent], default=last_updated)
            new_data = {
                "cum_watch":running_watch + len(watchContent),
                "cum_scale":running_scale + len(scaleContent),
                "max_duration":max(old_max_duration,max(durations,default=old_max_duration)),
                "max_distance_traveled":max(old_max_distance_traveled,max(distances,default=old_max_distance_traveled)),
                "max_weight":max(old_max_weight,max(weights,default=old_max_weight)),
                "min_weight":min(old_min_weight,min(weights,default=old_min_weight)),
                "recent_timestamp": max([last_updated,scaleTimes,watchTimes],default=last_updated)
            }

            logger.info("Stats collected! Writing to JSON")
            #Write json
            with open(app_config["datastore"]["filename"],'w') as current:
                json.dump(new_data,current)
                #A debug message with the timestamp
                logger.debug("Finished populating stats with timestamp")
            #An info message on completion.
            logger.info("Values added to data.json!")
            return NoContent,201
        else:
            logger.error("An error has occured while retrieving data")
            return NoContent, 404
    except FileNotFoundError:
        #.json does not exist, creating and populating with default values
        logger.info("No json detected, generating default")
        #No json file yet, make it with defaults.
        default = {
            "cum_watch":0,
            "cum_scale":0,
            "max_duration":0,
            "max_distance_traveled":0,
            "max_weight":0,
            "min_weight":10000000,
            "recent_timestamp":datetime(1000,1,1,1,1).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        default_data = json.dumps(default)
        with open(app_config["datastore"]["filename"],'w') as current:
            current.write(default_data)
        logger.info("Processing logger finished on default route!")
        return NoContent, 201

def get_stats():
    logger.info("Get Stats Processing Request received")
    try:
        with open(app_config["datastore"]["filename"],'r') as current:
            loaded = json.load(current)
            logger.debug(f"{loaded}")
            logger.info("Statistics Outputted!")
            return loaded, 201
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
    app.run(port=8100, host="0.0.0.0")
