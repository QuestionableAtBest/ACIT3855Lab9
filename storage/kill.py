from models import Base
from sqlalchemy import create_engine
import yaml
with open('./configs/storage_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

def drop_tables():
    engine = create_engine(f"mysql://{app_config['datastore']['user']}:{app_config['datastore']['password']}@{app_config['datastore']['hostname']}/{app_config['datastore']['db']}")
    Base.metadata.drop_all(engine)

if __name__ == "__main__":
    drop_tables()