def route_request(state: dict) -> str:
    message = state["user_message"].lower()

    github_indicators = [
        "github.com/",
        "github repository",
        "github repo",
        "repository on github",
    ]

    if any(indicator in message for indicator in github_indicators):
        return "github"

    return "eia"