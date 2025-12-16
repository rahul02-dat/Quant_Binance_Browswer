from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from storage.models import Base
import os

DATABASE_URL = "sqlite:///data/market_data.db"

os.makedirs("data", exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()