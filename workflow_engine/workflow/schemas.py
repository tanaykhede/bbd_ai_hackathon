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
    next_task_no: int | None = None

class TaskRuleCreate(TaskRuleBase):
    pass

class TaskRule(BaseModel):
    taskruleno: int
    taskno: int
    rule: str
    next_task_no: int | None = None
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class TaskRuleUpdate(BaseModel):
    next_task_no: int | None = None

class TaskBase(BaseModel):
    process_definition_no: int
    description: str
    reference: str | None = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    process_definition_no: int | None = None
    description: str | None = None
    reference: str | None = None

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
    # Clients don't provide this; it's created server-side along with the start task
    start_task_no: int | None = None
    start_task_description: str

class ProcessDefinitionUpdate(BaseModel):
    process_type_no: int | None = None
    start_task_no: int | None = None
    version: str | None = None
    is_active: bool | None = None

class ProcessDefinition(BaseModel):
    process_definition_no: int
    process_type_no: int
    start_task_no: int
    version: str
    is_active: bool
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class ProcessTypeBase(BaseModel):
    description: str

class ProcessTypeCreate(ProcessTypeBase):
    pass

class ProcessTypeUpdate(BaseModel):
    description: str | None = None

class ProcessType(BaseModel):
    description: str
    process_type_no: int
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class StatusBase(BaseModel):
    description: str

class StatusCreate(StatusBase):
    statusno: int

class Status(StatusBase):
    statusno: int
    tmstamp: datetime.datetime
    usrid: str

    class Config:
        orm_mode = True

class ProcessDataTypeBase(BaseModel):
    description: str

class ProcessDataTypeCreate(ProcessDataTypeBase):
    pass

class ProcessDataTypeUpdate(BaseModel):
    description: str | None = None

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

# User schemas (for potential future use)
class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True
