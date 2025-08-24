from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Case(Base):
    __tablename__ = 'cases'
    caseno = Column(Integer, primary_key=True)
    client_id = Column(String)
    client_type = Column(String)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)
    processes = relationship("Process", back_populates="case")

class Process(Base):
    __tablename__ = 'processes'
    processno = Column(Integer, primary_key=True)
    case_no = Column(Integer, ForeignKey('cases.caseno'))
    status_no = Column(Integer, ForeignKey('status.statusno'))
    process_type_no = Column(Integer, ForeignKey('process_types.process_type_no'))
    date_started = Column(DateTime, default=datetime.datetime.utcnow)
    date_ended = Column(DateTime)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)
    case = relationship("Case", back_populates="processes")
    status = relationship("Status")
    process_type = relationship("ProcessType")
    steps = relationship("Step", back_populates="process")
    process_data = relationship("ProcessData", back_populates="process")

class Step(Base):
    __tablename__ = 'steps'
    stepno = Column(Integer, primary_key=True)
    processno = Column(Integer, ForeignKey('processes.processno'))
    taskno = Column(Integer, ForeignKey('tasks.taskno'))
    status_no = Column(Integer, ForeignKey('status.statusno'))
    date_started = Column(DateTime, default=datetime.datetime.utcnow)
    date_ended = Column(DateTime)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)
    process = relationship("Process", back_populates="steps")
    task = relationship("Task")
    status = relationship("Status")

class Task(Base):
    __tablename__ = 'tasks'
    taskno = Column(Integer, primary_key=True)
    process_definition_no = Column(Integer, ForeignKey('process_definitions.process_definition_no'))
    description = Column(String)
    reference = Column(String)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)
    process_definition = relationship("ProcessDefinition", back_populates="tasks")
    task_rules = relationship("TaskRule", back_populates="task")

class ProcessDefinition(Base):
    __tablename__ = 'process_definitions'
    process_definition_no = Column(Integer, primary_key=True)
    process_type_no = Column(Integer, ForeignKey('process_types.process_type_no'))
    start_task_no = Column(Integer)
    version = Column(String)
    is_active = Column(Boolean)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)
    process_type = relationship("ProcessType")
    tasks = relationship("Task", back_populates="process_definition")

class ProcessType(Base):
    __tablename__ = 'process_types'
    process_type_no = Column(Integer, primary_key=True)
    description = Column(String)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)

class Status(Base):
    __tablename__ = 'status'
    statusno = Column(Integer, primary_key=True)
    description = Column(String)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)

class ProcessData(Base):
    __tablename__ = 'process_data'
    process_data_no = Column(Integer, primary_key=True)
    processno = Column(Integer, ForeignKey('processes.processno'))
    process_data_type_no = Column(Integer, ForeignKey('process_data_types.process_data_type_no'))
    fieldname = Column(String)
    value = Column(String)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)
    process = relationship("Process", back_populates="process_data")
    process_data_type = relationship("ProcessDataType")

class ProcessDataType(Base):
    __tablename__ = 'process_data_types'
    process_data_type_no = Column(Integer, primary_key=True)
    description = Column(String)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)

class TaskRule(Base):
    __tablename__ = 'task_rules'
    taskruleno = Column(Integer, primary_key=True, autoincrement=True)
    taskno = Column(Integer, ForeignKey('tasks.taskno'), nullable=False)
    rule = Column(String, nullable=False)
    next_task_no = Column(Integer)
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String)
    task = relationship("Task", back_populates="task_rules")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")  # "user" or "admin"
    tmstamp = Column(DateTime, default=datetime.datetime.utcnow)
    usrid = Column(String, default="system")

class LogEntry(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String, index=True, nullable=False)  # INFO/WARNING/ERROR
    logger_name = Column(String, nullable=False)
    message = Column(String, nullable=False)
    pathname = Column(String)
    lineno = Column(Integer)
    func = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # HTTP request context (optional)
    http_method = Column(String)
    http_path = Column(String, index=True)
    status_code = Column(Integer)
    duration_ms = Column(Integer)
    user_agent = Column(String)
    client_ip = Column(String)
    user_id = Column(String)
