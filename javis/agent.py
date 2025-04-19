from javis.models.gemini import gemini
from pydantic_ai import Agent
from typing import List, Callable
<<<<<<< HEAD
from javis.tools import internet_search, resume, calendar, gmail
from javis.tools.email_monitor import send_and_monitor_candidate_email
from javis.tools.email_monitor_task import check_email_replies, process_candidate_reply
=======
from javis.tools import helpers, internet_search, resume, calendar, gmail
>>>>>>> 386f40c1562c (wip)
from javis import settings
from javis.tools.messages import MessageStore
from pydantic_core import to_jsonable_python
from javis.tools.telegram import send_telegram_message
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "create_agent",
]


def create_agent() -> Agent:
    agent = Agent(
        system_prompt=settings.SYSTEM_PROMPT,
        model=gemini,
    )

    register_tools(
        agent,
        [
            # Internet search
            internet_search.search,
            internet_search.view_website,
            # Search resume
            resume.find_top_match_experiences,
            resume.find_top_match_skills,
            resume.get_create_interview_schedule_instructions,
            resume.get_employees_for_interview,
            resume.create_interview_schedule,
            resume.get_resume_by_name,
            resume.get_resume_by_email,
            # Calendar
            calendar.create_calendar_event,
            calendar.delete_calendar_event,
            calendar.get_calendar_events,
            # Telegram
            send_telegram_message,
            # Gmail
            gmail.send_email,
<<<<<<< HEAD
            # Email monitoring
            check_email_replies,
            process_candidate_reply,
            send_and_monitor_candidate_email,
=======
            # Helpers
            helpers.get_time_now,
>>>>>>> 386f40c1562c (wip)
        ],
    )

    return agent


def register_tools(agent: Agent, tools: List[Callable]):
    """Register tools with the agent.

    Args:
        agent (Agent): The agent to register the tools to.
        tools (List[Callable]): The tools to register.
    """
    add_tool_plain = agent.tool_plain(
        docstring_format="google", require_parameter_descriptions=True
    )

    for tool in tools:
        add_tool_plain(tool)


async def process_prompt(prompt: str, agent: Agent, user_id: str = None):
    """Process a prompt with the agent and store chat history.

    Args:
        prompt: The user's prompt to process
        agent: The agent instance to use
        user_id: Optional user ID to store messages for

    Returns:
        str: The processed message
    """

    # Initialize message store and get existing messages if user_id provided
    print(f"Processing prompt: {prompt}")
    print(f"User ID: {user_id}")
    if user_id:
        messages_store = MessageStore()
        await messages_store.initialize()
        messages = await messages_store.get_messages(user_id)
        result = await agent.run(prompt, message_history=messages)
        messages = result.new_messages()
        as_python_objects = to_jsonable_python(messages)
        await messages_store.add_messages(user_id, as_python_objects)
        await messages_store.close()
    else:
        result = await agent.run(prompt, message_history=[])

    return result_response(result)


def result_response(result):
    message = ""
    for message in result.new_messages()[1:]:
        message = "".join(
            map(
                lambda part: part.content,
                filter(
                    lambda part: part.part_kind == "text" and len(part.content) > 0,
                    message.parts,
                ),
            )
        )
    return message
