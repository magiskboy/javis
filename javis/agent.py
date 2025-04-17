from javis.models.gemini import gemini
from pydantic_ai import Agent
from typing import List, Callable
from pydantic_ai.messages import ModelMessage
from pydantic_ai.agent import AgentRunResult
from javis.tools import internet_search, resume
from javis import settings

__all__ = [
    "create_agent",
]

def create_agent() -> Agent:
    agent = Agent(
        system_prompt=settings.SYSTEM_PROMPT,
        model=gemini,
    )

    register_tools(agent, [
        # Internet search
        internet_search.search,
        internet_search.view_website,

        # Search resume
        resume.find_top_match_experiences,
        resume.find_top_match_skills,
        resume.get_create_interview_schedule_instructions,
        resume.get_employees_for_interview,
        resume.send_message_via_telegram,
        resume.create_interview_schedule,
    ])

    return agent


def register_tools(agent: Agent, tools: List[Callable]):
    """Register tools with the agent.

    Args:
        agent (Agent): The agent to register the tools to.
        tools (List[Callable]): The tools to register.
    """

    add_tool_plain = agent.tool_plain(docstring_format='google', require_parameter_descriptions=True)

    for tool in tools:
        add_tool_plain(tool)


async def process_prompt(prompt: str, agent: Agent, message_history: list[ModelMessage] = None) -> tuple[str, AgentRunResult]:
    result = await agent.run(
        prompt,
        message_history=message_history,
    )

    message = ''
    for message in result.new_messages()[1:]:
        message = "".join(map(
            lambda part: part.content, 
            filter(lambda part: part.part_kind == 'text' and len(part.content) > 0, message.parts)
        ))

    return message, result
