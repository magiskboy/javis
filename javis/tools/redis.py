import redis
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, ConfigDict


__all__ = [
    "create_redis_connection",
    "execute_command",
    "close_redis_connection",
    "key_exists",
    "get_all_keys",
    "get_value",
    "set_value",
    "delete_key",
    "flush_db",
    "get_key_type",
    "get_ttl",
    "set_ttl",
    "list_push",
    "list_pop",
    "list_range",
    "hash_set",
    "hash_get",
    "hash_get_all",
]


class RedisConnectionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    success: bool
    message: str
    connection: Optional[Any] = None


class RedisCommandResult(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


def create_redis_connection(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    **kwargs
) -> RedisConnectionResult:
    """Create a connection to a Redis server.
    
    Args:
        host (str, optional): Redis server host. Defaults to "localhost".
        port (int, optional): Redis server port. Defaults to 6379.
        db (int, optional): Redis database number. Defaults to 0.
        password (Optional[str], optional): Redis password. Defaults to None.
        **kwargs: Additional arguments to pass to Redis client.
        
    Returns:
        RedisConnectionResult: A model containing connection result with the following fields:
            - success: Boolean indicating if connection was successful
            - message: Description of the operation result
            - connection: The Redis connection object if successful
    """
    try:
        connection = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            **kwargs
        )
        # Test the connection
        connection.ping()
        return RedisConnectionResult(
            success=True,
            message=f"Successfully connected to Redis server at {host}:{port} (db: {db})",
            connection=connection
        )
    except redis.ConnectionError as e:
        return RedisConnectionResult(
            success=False,
            message=f"Error connecting to Redis server: {str(e)}"
        )
    except Exception as e:
        return RedisConnectionResult(
            success=False,
            message=f"Unexpected error connecting to Redis: {str(e)}"
        )


def execute_command(
    connection_result: RedisConnectionResult,
    command: str,
    *args
) -> RedisCommandResult:
    """Execute a Redis command.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        command (str): Redis command to execute
        *args: Arguments for the Redis command
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Result data from the command if successful
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        result = connection_result.connection.execute_command(command, *args)
        return RedisCommandResult(
            success=True,
            message=f"Command '{command}' executed successfully",
            data=result
        )
    except redis.RedisError as e:
        return RedisCommandResult(
            success=False,
            message=f"Error executing Redis command '{command}': {str(e)}"
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Unexpected error executing Redis command '{command}': {str(e)}"
        )


def close_redis_connection(connection_result: RedisConnectionResult) -> RedisCommandResult:
    """Close the Redis connection.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        connection_result.connection.close()
        return RedisCommandResult(
            success=True,
            message="Redis connection closed successfully"
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error closing Redis connection: {str(e)}"
        )


def key_exists(connection_result: RedisConnectionResult, key: str) -> RedisCommandResult:
    """Check if a key exists in Redis.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Key to check
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Boolean indicating if the key exists
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        exists = connection_result.connection.exists(key)
        return RedisCommandResult(
            success=True,
            message=f"Key '{key}' {'exists' if exists else 'does not exist'}",
            data=bool(exists)
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error checking if key exists: {str(e)}"
        )


def get_all_keys(
    connection_result: RedisConnectionResult,
    pattern: str = "*"
) -> RedisCommandResult:
    """Get all keys matching a pattern.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        pattern (str, optional): Pattern to match keys. Defaults to "*" (all keys).
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: List of keys matching the pattern
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        keys = connection_result.connection.keys(pattern)
        # Convert bytes to strings
        keys_str = [k.decode('utf-8') if isinstance(k, bytes) else k for k in keys]
        return RedisCommandResult(
            success=True,
            message=f"Found {len(keys_str)} keys matching pattern '{pattern}'",
            data=keys_str
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error getting keys: {str(e)}"
        )


def get_value(connection_result: RedisConnectionResult, key: str) -> RedisCommandResult:
    """Get the value of a key.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Key to get value for
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Value of the key if successful
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        value = connection_result.connection.get(key)
        if value is None:
            return RedisCommandResult(
                success=False,
                message=f"Key '{key}' does not exist",
                data=None
            )
        
        # Try to decode bytes to string
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                # Keep as bytes if it can't be decoded
                pass
                
        return RedisCommandResult(
            success=True,
            message=f"Successfully retrieved value for key '{key}'",
            data=value
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error getting value: {str(e)}"
        )


def set_value(
    connection_result: RedisConnectionResult,
    key: str,
    value: Any,
    ex: Optional[int] = None,
    px: Optional[int] = None,
    nx: bool = False,
    xx: bool = False
) -> RedisCommandResult:
    """Set the value of a key.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Key to set
        value (Any): Value to set
        ex (Optional[int], optional): Expire time in seconds. Defaults to None.
        px (Optional[int], optional): Expire time in milliseconds. Defaults to None.
        nx (bool, optional): Only set if key does not exist. Defaults to False.
        xx (bool, optional): Only set if key exists. Defaults to False.
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        result = connection_result.connection.set(
            key,
            value,
            ex=ex,
            px=px,
            nx=nx,
            xx=xx
        )
        if result:
            return RedisCommandResult(
                success=True,
                message=f"Successfully set value for key '{key}'",
                data=True
            )
        else:
            return RedisCommandResult(
                success=False,
                message=f"Failed to set value for key '{key}' (condition not met)",
                data=False
            )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error setting value: {str(e)}"
        )


def delete_key(
    connection_result: RedisConnectionResult,
    *keys
) -> RedisCommandResult:
    """Delete one or more keys.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        *keys: Keys to delete
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Number of keys deleted
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    if not keys:
        return RedisCommandResult(
            success=False,
            message="No keys specified for deletion"
        )
    
    try:
        count = connection_result.connection.delete(*keys)
        return RedisCommandResult(
            success=True,
            message=f"Successfully deleted {count} key(s)",
            data=count
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error deleting keys: {str(e)}"
        )


def flush_db(connection_result: RedisConnectionResult) -> RedisCommandResult:
    """Delete all keys in the current database.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        connection_result.connection.flushdb()
        return RedisCommandResult(
            success=True,
            message="Successfully flushed all keys from the database"
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error flushing database: {str(e)}"
        )


def get_key_type(connection_result: RedisConnectionResult, key: str) -> RedisCommandResult:
    """Get the type of a key.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Key to check
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Type of the key (string, list, set, hash, etc.)
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        key_type = connection_result.connection.type(key)
        if isinstance(key_type, bytes):
            key_type = key_type.decode('utf-8')
            
        if key_type == 'none':
            return RedisCommandResult(
                success=False,
                message=f"Key '{key}' does not exist",
                data=None
            )
            
        return RedisCommandResult(
            success=True,
            message=f"Key '{key}' is of type '{key_type}'",
            data=key_type
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error getting key type: {str(e)}"
        )


def get_ttl(connection_result: RedisConnectionResult, key: str) -> RedisCommandResult:
    """Get the time-to-live (TTL) of a key in seconds.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Key to check
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: TTL in seconds, -1 if no expiry, -2 if key doesn't exist
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        ttl = connection_result.connection.ttl(key)
        
        if ttl == -2:
            return RedisCommandResult(
                success=False,
                message=f"Key '{key}' does not exist",
                data=-2
            )
        elif ttl == -1:
            return RedisCommandResult(
                success=True,
                message=f"Key '{key}' has no expiration",
                data=-1
            )
        else:
            return RedisCommandResult(
                success=True,
                message=f"Key '{key}' will expire in {ttl} seconds",
                data=ttl
            )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error getting TTL: {str(e)}"
        )


def set_ttl(
    connection_result: RedisConnectionResult,
    key: str,
    seconds: int
) -> RedisCommandResult:
    """Set the time-to-live (TTL) of a key in seconds.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Key to set TTL for
        seconds (int): TTL in seconds
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Boolean indicating if the operation was successful
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        result = connection_result.connection.expire(key, seconds)
        if result:
            return RedisCommandResult(
                success=True,
                message=f"Successfully set TTL of {seconds} seconds for key '{key}'",
                data=True
            )
        else:
            return RedisCommandResult(
                success=False,
                message=f"Failed to set TTL: key '{key}' does not exist",
                data=False
            )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error setting TTL: {str(e)}"
        )


def list_push(
    connection_result: RedisConnectionResult,
    key: str,
    *values,
    left: bool = False
) -> RedisCommandResult:
    """Push values to a list.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): List key
        *values: Values to push
        left (bool, optional): Push to the left (beginning) of the list. Defaults to False.
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Length of the list after the push operation
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    if not values:
        return RedisCommandResult(
            success=False,
            message="No values specified to push"
        )
    
    try:
        if left:
            length = connection_result.connection.lpush(key, *values)
            position = "beginning"
        else:
            length = connection_result.connection.rpush(key, *values)
            position = "end"
            
        return RedisCommandResult(
            success=True,
            message=f"Successfully pushed {len(values)} value(s) to the {position} of list '{key}'",
            data=length
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error pushing to list: {str(e)}"
        )


def list_pop(
    connection_result: RedisConnectionResult,
    key: str,
    left: bool = False
) -> RedisCommandResult:
    """Pop a value from a list.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): List key
        left (bool, optional): Pop from the left (beginning) of the list. Defaults to False.
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Popped value, or None if the list is empty
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        if left:
            value = connection_result.connection.lpop(key)
            position = "beginning"
        else:
            value = connection_result.connection.rpop(key)
            position = "end"
            
        if value is None:
            return RedisCommandResult(
                success=False,
                message=f"List '{key}' is empty or does not exist",
                data=None
            )
            
        # Try to decode bytes to string
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                # Keep as bytes if it can't be decoded
                pass
                
        return RedisCommandResult(
            success=True,
            message=f"Successfully popped value from the {position} of list '{key}'",
            data=value
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error popping from list: {str(e)}"
        )


def list_range(
    connection_result: RedisConnectionResult,
    key: str,
    start: int = 0,
    end: int = -1
) -> RedisCommandResult:
    """Get a range of elements from a list.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): List key
        start (int, optional): Start index. Defaults to 0.
        end (int, optional): End index. Defaults to -1 (last element).
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: List of elements in the specified range
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        values = connection_result.connection.lrange(key, start, end)
        
        # Try to decode bytes to strings
        decoded_values = []
        for value in values:
            if isinstance(value, bytes):
                try:
                    decoded_values.append(value.decode('utf-8'))
                except UnicodeDecodeError:
                    decoded_values.append(value)
            else:
                decoded_values.append(value)
                
        return RedisCommandResult(
            success=True,
            message=f"Successfully retrieved {len(decoded_values)} element(s) from list '{key}'",
            data=decoded_values
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error getting list range: {str(e)}"
        )


def hash_set(
    connection_result: RedisConnectionResult,
    key: str,
    field_value_dict: Dict[str, Any] = None,
    **fields
) -> RedisCommandResult:
    """Set fields in a hash.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Hash key
        field_value_dict (Dict[str, Any], optional): Dictionary of field-value pairs. Defaults to None.
        **fields: Field-value pairs as keyword arguments
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Number of fields that were added (not updated)
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    # Combine both ways of providing field-value pairs
    mapping = {}
    if field_value_dict:
        mapping.update(field_value_dict)
    if fields:
        mapping.update(fields)
        
    if not mapping:
        return RedisCommandResult(
            success=False,
            message="No field-value pairs specified"
        )
    
    try:
        result = connection_result.connection.hset(key, mapping=mapping)
        return RedisCommandResult(
            success=True,
            message=f"Successfully set {len(mapping)} field(s) in hash '{key}' ({result} new field(s))",
            data=result
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error setting hash fields: {str(e)}"
        )


def hash_get(
    connection_result: RedisConnectionResult,
    key: str,
    field: str
) -> RedisCommandResult:
    """Get a field from a hash.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Hash key
        field (str): Field to get
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Value of the field, or None if the field or hash doesn't exist
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        value = connection_result.connection.hget(key, field)
        
        if value is None:
            return RedisCommandResult(
                success=False,
                message=f"Field '{field}' does not exist in hash '{key}' or hash does not exist",
                data=None
            )
            
        # Try to decode bytes to string
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                # Keep as bytes if it can't be decoded
                pass
                
        return RedisCommandResult(
            success=True,
            message=f"Successfully retrieved value for field '{field}' in hash '{key}'",
            data=value
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error getting hash field: {str(e)}"
        )


def hash_get_all(
    connection_result: RedisConnectionResult,
    key: str
) -> RedisCommandResult:
    """Get all fields and values from a hash.
    
    Args:
        connection_result (RedisConnectionResult): Connection result from create_redis_connection
        key (str): Hash key
        
    Returns:
        RedisCommandResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: Dictionary of field-value pairs, or empty dict if hash doesn't exist
    """
    if not connection_result.success or connection_result.connection is None:
        return RedisCommandResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    try:
        result = connection_result.connection.hgetall(key)
        
        # If hash doesn't exist or is empty
        if not result:
            return RedisCommandResult(
                success=False,
                message=f"Hash '{key}' is empty or does not exist",
                data={}
            )
            
        # Try to decode bytes to strings
        decoded_result = {}
        for field, value in result.items():
            # Decode field if it's bytes
            if isinstance(field, bytes):
                try:
                    field = field.decode('utf-8')
                except UnicodeDecodeError:
                    # Keep as bytes if it can't be decoded
                    pass
                    
            # Decode value if it's bytes
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8')
                except UnicodeDecodeError:
                    # Keep as bytes if it can't be decoded
                    pass
                    
            decoded_result[field] = value
                
        return RedisCommandResult(
            success=True,
            message=f"Successfully retrieved {len(decoded_result)} field(s) from hash '{key}'",
            data=decoded_result
        )
    except Exception as e:
        return RedisCommandResult(
            success=False,
            message=f"Error getting all hash fields: {str(e)}"
        )
