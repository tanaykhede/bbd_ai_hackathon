import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from workflow_engine.workflow.db.models import Base

# Load environment variables from .env if present
load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
	raise RuntimeError("SQLALCHEMY_DATABASE_URL must be set to a PostgreSQL URL (postgresql://...)")

# Normalize legacy 'postgres://' scheme to 'postgresql://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
	SQLALCHEMY_DATABASE_URL = "postgresql://" + SQLALCHEMY_DATABASE_URL[len("postgres://"):]

if not SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
	raise RuntimeError("Only PostgreSQL is supported. Provide a postgresql:// URL.")

# Enforce search_path to workflow_db via connection options
engine = create_engine(
	SQLALCHEMY_DATABASE_URL,
	connect_args={"options": "-csearch_path=workflow_db"},
	pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


