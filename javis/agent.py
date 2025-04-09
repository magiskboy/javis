from javis.models.gemini import gemini
from pydantic_ai import Agent
from typing import List, Callable
from javis.tools import filesystem, python, internet_search, redis, database


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

        # Redis
        # redis.create_redis_connection,
        # redis.execute_command,
        # redis.close_redis_connection,
        # redis.key_exists,
        # redis.get_all_keys,
        # redis.get_value,
        # redis.set_value,
        # redis.delete_key,
        # redis.flush_db,
        # redis.get_key_type,
        # redis.get_ttl,
        # redis.set_ttl,
        # redis.list_push,
        # redis.list_pop,
        # redis.list_range,
        # redis.hash_set,
        # redis.hash_get,
        # redis.hash_get_all,

        # Database
        # database.create_database_connection,
        database.execute_query,
        database.execute_read_query,
        # database.close_database_connection,
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