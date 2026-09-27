from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.dataset import Sample

from comeclean.config import MESSAGE_LIMIT
from comeclean.prompts import USER_PROMPT
from comeclean.scenario import seed_files
from comeclean.scoring import come_clean_scorer
from comeclean.solvers import agent_solver, seed_exposure


@task
def come_clean() -> Task:
    return Task(
        dataset=[Sample(input=USER_PROMPT, files=seed_files())],
        solver=[seed_exposure(), agent_solver()],
        scorer=come_clean_scorer(),
        sandbox="local",
        message_limit=MESSAGE_LIMIT,
    )
