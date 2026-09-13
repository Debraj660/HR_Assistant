from langchain.agents import (
    create_agent,
)


from assistant import config
from assistant.logger import get_logger


logger = get_logger(__name__)


def create_hr_agent(
    llm,
    tools,
):

    logger.info(
        "Creating HR agent with %d tool(s).",
        len(tools),
    )

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=(
            config.SYSTEM_PROMPT
        ),
    )

    logger.info(
        "HR agent ready."
    )

    return agent