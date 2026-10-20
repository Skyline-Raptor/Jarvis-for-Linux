import shutil
import uuid
from pathlib import Path
from .config import atomic_json


def stage_core(config,reason):
    source=Path(__file__).resolve().parent.parent
    target=Path(config.get('roots')[0])/'Candidates'/('Jarvis-'+uuid.uuid4().hex[:12])
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('.venv','__pycache__','*.pyc','test-results','*.log','resolved-environment.txt','wheelhouse','.bootstrap','install-logs'))
    atomic_json(target/'candidate.json',dict(source=str(source),reason=reason,status='staged_not_active'))
    return dict(candidate=str(target),status='staged_not_active',next='Edit and run candidate tests. Quit Jarvis before manually applying through apply_candidate.sh (Linux) or Apply_Candidate.cmd (Windows). Keep a rollback archive.')
