import connexion
import yaml
import logging
import logging.config
import datetime
import apscheduler.schedulers.background as apsched
# from connexion import NoContent

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("fitscale.yaml", strict_validation=True,validate_responses=True)

with open('processing/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open("receiver/log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

def populate_stats():
    logger.info("Periodic statistics gathering has begun!")
    curtime = datetime.strptime(datetime.now(), "%Y-%m-%dT%H:%M:%S.%fZ")



def init_scheduler():
    sched = apsched.BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
                'interval',
                seconds=app_config['scheduler']['interval'])
    sched.start()

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100)
