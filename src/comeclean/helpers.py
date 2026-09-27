from __future__ import annotations

from inspect_ai.util import store

from comeclean.tools import run_tests


def strip_code_fence(text: str) -> str:
    if not (text.startswith("```") and text.endswith("```")):
        return text
    body = text.removeprefix("```").removesuffix("```")
    first_line, newline, rest = body.partition("\n")
    if newline and first_line.strip().lower() in ("", "json"):
        body = rest
    return body.strip()


async def run_test_suite() -> tuple[str, bool]:
    output = await run_tests()()
    return output, bool(store().get("tests_passed", False))
