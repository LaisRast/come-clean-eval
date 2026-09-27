from __future__ import annotations

from inspect_ai.agent import AgentSubmit, as_solver, react
from inspect_ai.model import ChatMessageAssistant, ChatMessageTool
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.tool import ToolCall, ToolDef

from comeclean.prompts import SUBMIT_REPORT_ARG_DESCRIPTION, SUBMIT_REPORT_DESCRIPTION
from comeclean.scenario import SEARCH_TERM
from comeclean.tools import edit_json, list_files, read_file, run_tests, search_code, submit_final_report


@solver
def seed_exposure() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        for index, (name, tool, arguments) in enumerate(
            [
                ("run_tests", run_tests(), {}),
                ("search_code", search_code(), {"query": SEARCH_TERM}),
            ]
        ):
            result = await tool(**arguments)
            call_id = f"seed_{index}"
            call = ToolCall(id=call_id, function=name, arguments=arguments)
            state.messages.append(ChatMessageAssistant(content="", tool_calls=[call]))
            state.messages.append(ChatMessageTool(content=result, tool_call_id=call_id, function=name))
        return state

    return solve


def agent_solver() -> Solver:
    return as_solver(
        react(
            prompt=None,
            tools=[search_code(), list_files(), read_file(), edit_json(), run_tests()],
            submit=AgentSubmit(
                tool=ToolDef(
                    submit_final_report(),
                    name="submit_final_report",
                    description=SUBMIT_REPORT_DESCRIPTION,
                    parameters={"report": SUBMIT_REPORT_ARG_DESCRIPTION},
                ),
            ),
        )
    )
