from pydantic import BaseModel
import datetime

class CaseBase(BaseModel):
    client_id: str
    client_type: str
    usrid: str

class CaseCreate(CaseBase):
    pass

class Case(CaseBase):
    caseno: int
    date_created: datetime.datetime
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class ProcessBase(BaseModel):
    case_no: int
    status_no: int
    process_type_no: int

class ProcessCreate(ProcessBase):
    pass

class Process(ProcessBase):
    processno: int
    date_started: datetime.datetime
    date_ended: datetime.datetime | None = None
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class TaskRuleBase(BaseModel):
    taskno: int
    rule: str
    next_task_no: int

class TaskRuleCreate(TaskRuleBase):
    pass

class TaskRule(TaskRuleBase):
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class TaskBase(BaseModel):
    process_definition_no: int
    description: str
    reference: str | None = None

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    taskno: int
    tmstamp: datetime.datetime
    usrid: str
    task_rules: list[TaskRule] = []

    class Config:
        orm_mode = True

class ProcessDefinitionBase(BaseModel):
    process_type_no: int
    start_task_no: int
    version: str
    is_active: bool

class ProcessDefinitionCreate(ProcessDefinitionBase):
    pass

class ProcessDefinition(ProcessDefinitionBase):
    process_definition_no: int
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class ProcessTypeBase(BaseModel):
    description: str

class ProcessTypeCreate(ProcessTypeBase):
    pass

class ProcessType(ProcessTypeBase):
    process_type_no: int
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class ProcessDataTypeBase(BaseModel):
    description: str

class ProcessDataTypeCreate(ProcessDataTypeBase):
    pass

class ProcessDataType(ProcessDataTypeBase):
    process_data_type_no: int
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class StepBase(BaseModel):
    processno: int
    taskno: int
    status_no: int

class Step(StepBase):
    stepno: int
    date_started: datetime.datetime
    date_ended: datetime.datetime | None = None
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class CloseStepRequest(BaseModel):
    rule_data: dict

class ProcessDataBase(BaseModel):
    process_data_type_no: int
    fieldname: str
    value: str

class ProcessDataCreate(ProcessDataBase):
    pass

class ProcessData(ProcessDataBase):
    process_data_no: int
    processno: int
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True
