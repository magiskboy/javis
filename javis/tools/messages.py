from typing import List
import json
from javis.helper import get_database_connection


class MessageStore:
    """A class to manage chat message storage in PostgreSQL database.

    This class provides methods to store and retrieve chat messages for users
    using PostgreSQL as the backend database.
    """

    def __init__(self):
        """Initialize the MessageStore with a database connection and create table if not exists."""
        self.connection = None

    async def initialize(self):
        """Initialize async database connection and create table if not exists.

        This method should be called before using any other methods of the class.
        """
        self.connection = await get_database_connection()
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                messages JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
            # CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
        )

    async def add_messages(, user_id: str, messages: list[dict]) -> None:
        """Add messages for a specific user to the database.

        Args:
            user_id (str): The unique identifier of the user
            messages (list[dict]): List of message dictionaries to store

        Raises:
            ValueError: If connection is not initialized
            asyncpg.PostgresError: If database operation fails
        """
        if not self.connection:
            raise ValueError(
                "Database connection not initialized. Call initialize() first."
            )

        query = """
        INSERT INTO messages (user_id, messages) 
        VALUES ($1, $2)
        """
        await self.connection.execute(query, user_id, json.dumps(messages))

    async def get_messages(self, user_id: str) -> List[any]:
        from pydantic_ai.messages import ModelMessagesTypeAdapter

        """Retrieve all messages for a specific user.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            List[ModelMessage]: List of ModelMessage objects containing the user's messages

        Raises:
            ValueError: If connection is not initialized
            asyncpg.PostgresError: If database operation fails
        """
        if not self.connection:
            raise ValueError(
                "Database connection not initialized. Call initialize() first."
            )

        query = """
        SELECT user_id, messages 
        FROM messages 
        WHERE user_id = $1
        ORDER BY created_at ASC
        """
        rows = await self.connection.fetch(query, user_id)
        messages = json.loads(rows[0][1])
        return ModelMessagesTypeAdapter.validate_python(messages)

    async def close(self):
        """Close the database connection.

        This method should be called when the MessageStore is no longer needed.
        """
        if self.connection:
            await self.connection.close()
            self.connection = None

    async def delete_messages(self, user_id: str):
        """Delete all messages for a specific user.

        Args:
            user_id (str): The unique identifier of the user
        """
        await self.connection.execute(
            "DELETE FROM messages WHERE user_id = $1", user_id
        )
