import datetime
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException
from workflow_engine.workflow.db import models
from workflow_engine.workflow import schemas
from workflow_engine.workflow.doa.utils import save, require_found

def create_step(db: Session, processno: int, taskno: int, status_no: int, usrid: str) -> models.Step:
    return save(db, models.Step(
        processno=processno,
        taskno=taskno,
        status_no=status_no,
        usrid=usrid
    ))

def list_all_steps(db: Session) -> list[models.Step]:
    return db.query(models.Step).all()

def _get_status_no(db: Session, description: str) -> int:
    status = db.query(models.Status).filter(models.Status.description.ilike(description)).first()
    if not status:
        raise HTTPException(status_code=500, detail=f"Required status '{description}' not configured")
    return status.statusno

def _strip_quotes(val: str) -> str:
    v = val.strip()
    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        return v[1:-1]
    return v

def _parse_rule_expr(rule: str):
    """
    Supports rule formats:
      - 'default'
      - 'procdata.<processdatatype>.<fieldname> == <value>'
      - 'procdata.<processdatatype>.<fieldname> != <value>'
    Returns:
      ('default',) for default
      (datatype, field, op, value) for expressions
      None if unparsable
    """
    s = rule.strip()
    if s.lower() == "default":
        return ("default",)
    m = re.match(
        r"^procdata\.(?P<dtype>[^.\s]+)\.(?P<field>[^\s]+)\s*(?P<op>==|!=)\s*(?P<value>.+)$",
        s,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return (m.group("dtype"), m.group("field"), m.group("op"), m.group("value").strip())

def _evaluate_condition(db: Session, processno: int, dtype: str, field: str, op: str, expected_value: str) -> bool:
    """
    Look up ProcessData by:
      - ProcessDataType.description == dtype
      - ProcessData.fieldname == field
      - ProcessData.processno == processno
    Compare the stored string value against expected_value using == or !=.
    """
    expected = _strip_quotes(expected_value)
    pd = (
        db.query(models.ProcessData)
        .join(
            models.ProcessDataType,
            models.ProcessData.process_data_type_no == models.ProcessDataType.process_data_type_no,
        )
        .filter(
            models.ProcessData.processno == processno,
            models.ProcessDataType.description == dtype,
            models.ProcessData.fieldname == field,
        )
        .order_by(models.ProcessData.process_data_no.desc())
        .first()
    )
    if not pd:
        return False
    actual = pd.value if pd.value is not None else ""
    if op == "==":
        return actual == expected
    else:
        return actual != expected

def close_step(db: Session, step_id: int, request: schemas.CloseStepRequest, usrid: str) -> models.Step:
    db_step = db.query(models.Step).filter(models.Step.stepno == step_id).first()
    require_found(db_step, "Step not found", 404)

    # Ensure current step is 'busy'
    busy_status_no = _get_status_no(db, "busy")
    if db_step.status_no != busy_status_no:
        raise HTTPException(status_code=400, detail="Step is not busy")

    # Get all rules for the current task
    task_rules = db.query(models.TaskRule).filter(models.TaskRule.taskno == db_step.taskno).all()

    next_task_no = None
    default_rule = None

    # Evaluate non-default rules first
    for tr in task_rules:
        parsed = _parse_rule_expr(tr.rule)
        if not parsed:
            continue
        if parsed[0] == "default":
            default_rule = tr
            continue
        dtype, field, op, value = parsed
        if _evaluate_condition(db, db_step.processno, dtype, field, op, value):
            next_task_no = tr.next_task_no
            break

    # If none matched, use default if present
    if next_task_no is None:
        if default_rule is not None:
            next_task_no = default_rule.next_task_no
        else:
            raise HTTPException(status_code=400, detail="No matching rule and no default task found")

    completed_status_no = _get_status_no(db, "complete")

    # Apply mutations and commit once (atomic)
    result_step: models.Step

    # Close current step
    db_step.status_no = completed_status_no
    db_step.date_ended = datetime.datetime.utcnow()

    if next_task_no is None:
        # Complete the process as part of the same atomic commit
        proc = db.query(models.Process).filter(models.Process.processno == db_step.processno).first()
        require_found(proc, "Process not found", 404)
        proc.status_no = completed_status_no
        proc.date_ended = datetime.datetime.utcnow()
        result_step = db_step
    else:
        # Create next step as 'busy'
        new_step = models.Step(
            processno=db_step.processno,
            taskno=next_task_no,
            status_no=busy_status_no,
            usrid=usrid,
        )
        db.add(new_step)
        db.flush()  # ensure PK assigned
        result_step = new_step

    db.commit()
    db.refresh(result_step)
    return result_step
