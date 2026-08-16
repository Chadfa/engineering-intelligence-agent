from typing import Any, TypedDict


class EIAState(TypedDict):
    user_message: str
    response: str
    github_data: dict[str, Any] | None