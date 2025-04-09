import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel

__all__ = [
    "create_database_connection",
    "execute_query",
    "execute_read_query",
    "close_database_connection"
]

# Import database libraries with error handling
try:
    import aiomysql
except ImportError:
    aiomysql = None

try:
    import asyncpg
except ImportError:
    asyncpg = None


class QueryResult(BaseModel):
    success: bool
    message: str
    rowcount: Optional[int] = None
    data: Optional[List[Dict[str, Any]]] = None


class ConnectionResult(BaseModel):
    success: bool
    message: str
    connection: Optional[Any] = None
    db_type: Optional[str] = None


async def create_database_connection(
    db_type: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    **kwargs
) -> ConnectionResult:
    """Create an async database connection to MySQL or PostgreSQL.
    
    Args:
        db_type (str): Type of database ('mysql' or 'postgres')
        host (str): Database host
        port (int): Database port
        user (str): Database username
        password (str): Database password
        database (str): Database name
        **kwargs: Additional connection parameters
        
    Returns:
        ConnectionResult: A model containing connection result with the following fields:
            - success: Boolean indicating if connection was successful
            - message: Description of the operation result
            - connection: The database connection object if successful
            - db_type: The type of database connected to
    """
    if db_type.lower() == 'mysql':
        if aiomysql is None:
            return ConnectionResult(
                success=False,
                message="aiomysql is not installed. Install with 'pip install aiomysql'",
                db_type=db_type
            )
        
        try:
            connection = await aiomysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                db=database,
                **kwargs
            )
            return ConnectionResult(
                success=True,
                message=f"Successfully connected to MySQL database: {database}",
                connection=connection,
                db_type=db_type
            )
        except Exception as e:
            return ConnectionResult(
                success=False,
                message=f"Error connecting to MySQL database: {str(e)}",
                db_type=db_type
            )
            
    elif db_type.lower() == 'postgres':
        if asyncpg is None:
            return ConnectionResult(
                success=False,
                message="asyncpg is not installed. Install with 'pip install asyncpg'",
                db_type=db_type
            )
        
        try:
            connection = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                **kwargs
            )
            return ConnectionResult(
                success=True,
                message=f"Successfully connected to PostgreSQL database: {database}",
                connection=connection,
                db_type=db_type
            )
        except Exception as e:
            return ConnectionResult(
                success=False,
                message=f"Error connecting to PostgreSQL database: {str(e)}",
                db_type=db_type
            )
    else:
        return ConnectionResult(
            success=False,
            message=f"Unsupported database type: {db_type}. Must be 'mysql' or 'postgres'",
            db_type=db_type
        )


async def execute_query(connection_result: ConnectionResult, query: str, params: Optional[Tuple] = None) -> QueryResult:
    """Execute a query that modifies the database (INSERT, UPDATE, DELETE).
    
    Args:
        connection_result (ConnectionResult): Connection result from create_database_connection
        query (str): SQL query to execute
        params (Optional[Tuple]): Parameters for the query
        
    Returns:
        QueryResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - rowcount: Number of affected rows if available
    """
    if not connection_result.success or connection_result.connection is None:
        return QueryResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    connection = connection_result.connection
    db_type = connection_result.db_type
    
    if db_type == 'mysql':
        try:
            async with connection.cursor() as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                await connection.commit()
                return QueryResult(
                    success=True,
                    message="Query executed successfully",
                    rowcount=cursor.rowcount
                )
        except Exception as e:
            await connection.rollback()
            return QueryResult(
                success=False,
                message=f"Error executing MySQL query: {str(e)}"
            )
            
    elif db_type == 'postgres':
        try:
            if params:
                result = await connection.execute(query, *params)
            else:
                result = await connection.execute(query)
            
            # Extract rowcount from the result string (e.g., "INSERT 0 1" -> 1)
            rowcount = None
            if result and ' ' in result:
                parts = result.split(' ')
                if len(parts) >= 3:
                    try:
                        rowcount = int(parts[2])
                    except ValueError:
                        pass
            
            return QueryResult(
                success=True,
                message="Query executed successfully",
                rowcount=rowcount
            )
        except Exception as e:
            return QueryResult(
                success=False,
                message=f"Error executing PostgreSQL query: {str(e)}"
            )
    else:
        return QueryResult(
            success=False,
            message=f"Unsupported database type: {db_type}"
        )


async def execute_read_query(connection_result: ConnectionResult, query: str, params: Optional[Tuple] = None) -> QueryResult:
    """Execute a SELECT query and return the results.
    
    Args:
        connection_result (ConnectionResult): Connection result from create_database_connection
        query (str): SQL query to execute
        params (Optional[Tuple]): Parameters for the query
        
    Returns:
        QueryResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
            - data: List of dictionaries containing the query results
    """
    if not connection_result.success or connection_result.connection is None:
        return QueryResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    connection = connection_result.connection
    db_type = connection_result.db_type
    
    if db_type == 'mysql':
        try:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                rows = await cursor.fetchall()
                return QueryResult(
                    success=True,
                    message=f"Query returned {len(rows)} rows",
                    rowcount=len(rows),
                    data=rows
                )
        except Exception as e:
            return QueryResult(
                success=False,
                message=f"Error executing MySQL read query: {str(e)}"
            )
            
    elif db_type == 'postgres':
        try:
            if params:
                rows = await connection.fetch(query, *params)
            else:
                rows = await connection.fetch(query)
            
            # Convert asyncpg.Record objects to dictionaries
            result_data = [dict(row) for row in rows]
            
            return QueryResult(
                success=True,
                message=f"Query returned {len(result_data)} rows",
                rowcount=len(result_data),
                data=result_data
            )
        except Exception as e:
            return QueryResult(
                success=False,
                message=f"Error executing PostgreSQL read query: {str(e)}"
            )
    else:
        return QueryResult(
            success=False,
            message=f"Unsupported database type: {db_type}"
        )


async def close_database_connection(connection_result: ConnectionResult) -> QueryResult:
    """Close the database connection.
    
    Args:
        connection_result (ConnectionResult): Connection result from create_database_connection
        
    Returns:
        QueryResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - message: Description of the operation result
    """
    if not connection_result.success or connection_result.connection is None:
        return QueryResult(
            success=False,
            message=f"Invalid connection: {connection_result.message}"
        )
    
    connection = connection_result.connection
    db_type = connection_result.db_type
    
    try:
        if db_type == 'mysql':
            connection.close()
            await connection.wait_closed()
        elif db_type == 'postgres':
            await connection.close()
        else:
            return QueryResult(
                success=False,
                message=f"Unsupported database type: {db_type}"
            )
        
        return QueryResult(
            success=True,
            message=f"Connection to {db_type} database closed successfully"
        )
    except Exception as e:
        return QueryResult(
            success=False,
            message=f"Error closing {db_type} connection: {str(e)}"
        )


