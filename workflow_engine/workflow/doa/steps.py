import datetime
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException
from workflow.db import models
from workflow import schemas
from workflow.doa.utils import save, require_found

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

def _strip_outer_parens(s: str) -> str:
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        balanced = True
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    balanced = False
                    break
        if balanced:
            s = s[1:-1].strip()
        else:
            break
    return s

def _split_outside(s: str, sep: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    in_squote = False
    in_dquote = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "'" and not in_dquote:
            in_squote = not in_squote
            buf.append(ch)
            i += 1
            continue
        if ch == '"' and not in_squote:
            in_dquote = not in_dquote
            buf.append(ch)
            i += 1
            continue
        if not in_squote and not in_dquote:
            if ch == "(":
                depth += 1
                buf.append(ch)
                i += 1
                continue
            if ch == ")":
                depth = max(0, depth - 1)
                buf.append(ch)
                i += 1
                continue
            if depth == 0 and s.startswith(sep, i):
                parts.append("".join(buf).strip())
                buf = []
                i += len(sep)
                continue
        buf.append(ch)
        i += 1
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p != ""]

def _normalize_bool_ops(s: str) -> str:
    out: list[str] = []
    in_squote = False
    in_dquote = False
    i = 0
    n = len(s)
    def is_word_char(c: str) -> bool:
        return c.isalnum() or c == "_"
    while i < n:
        ch = s[i]
        if ch == "'" and not in_dquote:
            in_squote = not in_squote
            out.append(ch); i += 1; continue
        if ch == '"' and not in_squote:
            in_dquote = not in_dquote
            out.append(ch); i += 1; continue
        if not in_squote and not in_dquote:
            if i + 3 <= n and s[i:i+3].lower() == "and":
                prev_ok = (i == 0) or not is_word_char(s[i-1])
                next_ok = (i + 3 == n) or not is_word_char(s[i+3])
                if prev_ok and next_ok:
                    out.append("&&"); i += 3; continue
            if i + 2 <= n and s[i:i+2].lower() == "or":
                prev_ok = (i == 0) or not is_word_char(s[i-1])
                next_ok = (i + 2 == n) or not is_word_char(s[i+2])
                if prev_ok and next_ok:
                    out.append("||"); i += 2; continue
        out.append(ch); i += 1
    return "".join(out)

def evaluate_rule_expression(db: Session, processno: int, rule_text: str) -> bool:
    """
    Evaluate a TaskRule expression against a process's current data.
    Supports:
      - default (ignored as boolean true; handled separately)
      - procdata.<dtype>.<field> == <value>
      - procdata.<dtype>.<field> != <value>
      - Compound expressions using && and || (and/or also accepted), with parentheses and quoted values.
    Semantics: OR-of-ANDs with parentheses respected.
    """
    text = _normalize_bool_ops(rule_text.strip())

    def _eval(text_fragment: str) -> bool:
        t = _normalize_bool_ops(text_fragment.strip())
        if t.lower() == "default":
            return False

        # Remove outermost parentheses if they wrap the whole fragment
        t = _strip_outer_parens(t)

        # Split by top-level OR (lower precedence than AND)
        or_groups = _split_outside(t, "||")
        if len(or_groups) > 1:
            return any(_eval(group) for group in or_groups)

        # Then split by top-level AND
        and_atoms = _split_outside(t, "&&")
        if len(and_atoms) > 1:
            for atom in and_atoms:
                if not _eval(atom):
                    return False
            return True

        # Leaf node: must be a simple comparison expression
        parsed = _parse_rule_expr(t)
        if not parsed or parsed[0] == "default":
            return False
        dtype, field, op, value = parsed
        return _evaluate_condition(db, processno, dtype, field, op, value)

    return _eval(text)

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

    # Evaluate non-default rules first (use module-level evaluator)
    for tr in task_rules:
        rule_text = (tr.rule or "").strip()
        if rule_text.lower() == "default":
            default_rule = tr
            continue
        if evaluate_rule_expression(db, db_step.processno, rule_text):
            next_task_no = tr.next_task_no
            break

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
