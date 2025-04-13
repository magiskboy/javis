from javis.models.gemini import gemini
from pydantic_ai import Agent
from typing import List, Callable
from javis.tools import filesystem, python, internet_search, resume


__all__ = [
    "create_agent",
]

def create_agent() -> Agent:
    agent = Agent(
        model=gemini,
    )

    register_tools(agent, [

        # Filesystem
        filesystem.get_file_details,
        filesystem.create_file,
        filesystem.update_file,
        filesystem.delete_file,
        filesystem.create_folder,
        filesystem.delete_folder,
        filesystem.read_folder,
        filesystem.copy_file,
        filesystem.move_file,
        filesystem.open_file,
        filesystem.read_file,

        # Python
        python.run_python_code,

        # Internet search
        internet_search.search,
        internet_search.view_website,

        # Search resume
        resume.find_top_match_experiences,
        resume.find_top_match_skills,
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