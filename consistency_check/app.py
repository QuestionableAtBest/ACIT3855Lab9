# Logging and storage
import json,logging,logging.config
# API packages
import yaml,httpx,connexion
from connexion import NoContent
from datetime import datetime,timezone
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
    logger.info

def get_checks():
    pass

if __name__ == "__main__":
    app.run(port=8120, host="0.0.0.0")