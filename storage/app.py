import connexion
import live
import logging
import logging.config
import yaml
from models import Base,Watch,Scale,KafkaConsumer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from datetime import datetime
from threading import Thread
import json
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("fitscale.yaml", strict_validation=True,base_path="/storage",validate_responses=True)

with open("./configs/storage_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read()) 
    logging.config.dictConfig(LOG_CONFIG)

with open('./configs/storage_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

engine = create_engine(f"mysql://{app_config['datastore']['user']}:{app_config['datastore']['password']}@{app_config['datastore']['hostname']}:{app_config['datastore']['port']}/{app_config['datastore']['db']}", pool_size=10,pool_recycle=1800,pool_pre_ping=True)
Base.metadata.create_all(engine)
logger = logging.getLogger('basicLogger')
kaf_consumer = KafkaConsumer(f"{app_config['events']['hostname']}:{app_config['events']['port']}",str.encode(app_config["events"]["topic"]))
#New storage
def make_session():
    return sessionmaker(bind=engine)()

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

def get_count():
    session = make_session()
    scale_count = session.query(Scale).count()
    watch_count = session.query(Watch).count()
    session.close()
    return {"watch_count": watch_count, "scale_count": scale_count}

def get_watch_list():
    session = make_session()
    watch_list = session.query(Watch.device_id, Watch.trace_id).all()
    session.close()
    print(watch_list)
    return [{"event_id": watch.device_id, "trace_id": watch.trace_id} for watch in watch_list]

def get_scale_list():
    session = make_session()
    scale_list = session.query(Scale.scale_id, Scale.trace_id).all()
    session.close()
    print(scale_list)
    return [{"scale_id": scale.scale_id, "trace_id": scale.trace_id} for scale in scale_list]



def process_messages():
    """ Process event messages """
    for msg in kaf_consumer.messages():
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]
        if msg["type"] == "watch_event":
            session = make_session()
            event = Watch(
                device_id=payload["device_id"],
                user_id = payload["user_id"],
                exercise_type = payload["exercise_type"],
                distance = payload["distance"],
                duration = payload["duration"],
                avg_heart_rate = payload["avg_heart_rate"],
                timestamp = datetime.strptime(payload["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                trace_id = payload["trace_id"]
            )
            session.add(event)
            session.commit()
            session.close()
            logger.debug(f"Stored scale results with trace id of {payload['trace_id']}")
        elif msg["type"] == "scale_event":
            session = make_session()
            event = Scale(
                scale_id=payload["scale_id"],
                weight = payload["weight"],
                age = payload["age"],
                gender = payload["gender"],
                height = payload["height"],
                body_fat_percentage = payload["body_fat_percentage"],
                timestamp = datetime.strptime(payload["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                trace_id = payload["trace_id"]
            )
            session.add(event)
            session.commit()
            session.close()
            logger.debug(f"Stored scale results with trace id of {payload['trace_id']}")
        kaf_consumer.commit()

def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

if __name__ == "__main__":
    live.make_tables()
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")