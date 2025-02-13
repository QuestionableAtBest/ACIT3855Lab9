import connexion
import live
from sqlalchemy import text
import logging
import logging.config
import yaml
from connexion import NoContent
from models import Base,Watch,Scale
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from datetime import datetime,timezone
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("fitscale.yaml", strict_validation=True,validate_responses=True)

with open("storage/log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

with open('storage/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

engine = create_engine(f"mysql://{app_config['datastore']['user']}:{app_config['datastore']['password']}@{app_config['datastore']['hostname']}:{app_config['datastore']['port']}/{app_config['datastore']['db']}")
Base.metadata.create_all(engine)
logger = logging.getLogger('basicLogger')
#New storage
def make_session():
    session = sessionmaker(bind=engine)()
    session.execute(text("SET time_zone = 'UTC'"))
    return session

def report_watch(body):
    session = make_session()
    event = Watch(
        device_id=body["device_id"],
        user_id = body["user_id"],
        exercise_type = body["exercise_type"],
        distance = body["distance"],
        duration = body["duration"],
        avg_heart_rate = body["avg_heart_rate"],
        timestamp = datetime.strptime(body["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
        trace_id = body["trace_id"]
    )
    session.add(event)
    session.commit()
    session.close()

    logger.debug(f"Stored watch results with trace id of {body['trace_id']}")
    return NoContent, 201

def report_scale(body):
    session = make_session()
    event = Scale(
        scale_id=body["scale_id"],
        weight = body["weight"],
        age = body["age"],
        gender = body["gender"],
        height = body["height"],
        body_fat_percentage = body["body_fat_percentage"],
        timestamp = datetime.strptime(body["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
        trace_id = body["trace_id"]
    )
    session.add(event)
    session.commit()
    session.close()
    logger.debug(f"Stored scale results with trace id of {body['trace_id']}")
    return NoContent, 201


def get_scale_readings(start_timestamp, end_timestamp):
    session = make_session()
    #SQLAlchemy filter statement
    statement = select(Scale).where(Scale.date_created > start_timestamp).where(Scale.date_created < end_timestamp)
    #Formatting the results in a dictionary
    results = [result.to_dict() for result in session.execute(statement).scalars().all()]
    session.close()
    logger.info("Found %d scale readings (start: %s, end: %s )", len(results),start_timestamp,end_timestamp)

    #Should add a status code here?
    return results

def get_watch_readings(start_timestamp, end_timestamp):
    session = make_session()    
    #SQLAlchemy filter statement
    statement = select(Watch).where(Watch.date_created > start_timestamp).where(Watch.date_created < end_timestamp)
    #Formatting the results in a dictionary
    results = [result.to_dict() for result in session.execute(statement).scalars().all()]
    session.close()
    logger.info("Found %d scale readings (start: %s, end: %s )", len(results),start_timestamp,end_timestamp)

    #Should add a status code here?
    return results



if __name__ == "__main__":
    live.make_tables()
    app.run(port=8090)