import unittest
import asyncio
from typing import Optional
import os

from javis.tools import database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Set up test database credentials from environment variables or use defaults
        self.mysql_config = {
            "db_type": "mysql",
            "host": os.environ.get("TEST_MYSQL_HOST", "localhost"),
            "port": int(os.environ.get("TEST_MYSQL_PORT", 3306)),
            "user": os.environ.get("TEST_MYSQL_USER", "root"),
            "password": os.environ.get("TEST_MYSQL_PASSWORD", "password"),
            "database": os.environ.get("TEST_MYSQL_DATABASE", "test_db")
        }
        
        self.postgres_config = {
            "db_type": "postgres",
            "host": os.environ.get("TEST_POSTGRES_HOST", "localhost"),
            "port": int(os.environ.get("TEST_POSTGRES_PORT", 5432)),
            "user": os.environ.get("TEST_POSTGRES_USER", "postgres"),
            "password": os.environ.get("TEST_POSTGRES_PASSWORD", "password"),
            "database": os.environ.get("TEST_POSTGRES_DATABASE", "test_db")
        }
        
        # Connection results to be used across tests
        self.mysql_conn: Optional[database.ConnectionResult] = None
        self.postgres_conn: Optional[database.ConnectionResult] = None

    async def async_setUp(self):
        # Create test tables if connections are successful
        if self.mysql_conn and self.mysql_conn.success:
            await database.execute_query(
                self.mysql_conn,
                "CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100))"
            )
            # Clear any existing data
            await database.execute_query(self.mysql_conn, "DELETE FROM test_table")
            
        if self.postgres_conn and self.postgres_conn.success:
            await database.execute_query(
                self.postgres_conn,
                "CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(100))"
            )
            # Clear any existing data
            await database.execute_query(self.postgres_conn, "DELETE FROM test_table")

    async def async_tearDown(self):
        # Clean up test tables
        if self.mysql_conn and self.mysql_conn.success:
            await database.execute_query(self.mysql_conn, "DROP TABLE IF EXISTS test_table")
            await database.close_database_connection(self.mysql_conn)
            
        if self.postgres_conn and self.postgres_conn.success:
            await database.execute_query(self.postgres_conn, "DROP TABLE IF EXISTS test_table")
            await database.close_database_connection(self.postgres_conn)

    def test_create_connection(self):
        async def run_test():
            # Test MySQL connection
            try:
                self.mysql_conn = await database.create_connection(**self.mysql_config)
                if database.aiomysql is not None:
                    self.assertTrue(self.mysql_conn.success)
                    self.assertEqual(self.mysql_conn.db_type, "mysql")
                else:
                    self.assertFalse(self.mysql_conn.success)
                    self.assertIn("aiomysql is not installed", self.mysql_conn.message)
            except Exception:
                # Skip if MySQL is not available
                pass
                
            # Test PostgreSQL connection
            try:
                self.postgres_conn = await database.create_connection(**self.postgres_config)
                if database.asyncpg is not None:
                    self.assertTrue(self.postgres_conn.success)
                    self.assertEqual(self.postgres_conn.db_type, "postgres")
                else:
                    self.assertFalse(self.postgres_conn.success)
                    self.assertIn("asyncpg is not installed", self.postgres_conn.message)
            except Exception:
                # Skip if PostgreSQL is not available
                pass
                
            # Test invalid database type
            invalid_conn = await database.create_connection(
                db_type="invalid",
                host="localhost",
                port=1234,
                user="user",
                password="password",
                database="db"
            )
            self.assertFalse(invalid_conn.success)
            self.assertIn("Unsupported database type", invalid_conn.message)
            
            # Set up for other tests
            await self.async_setUp()
        
        asyncio.run(run_test())

    def test_execute_query(self):
        async def run_test():
            if not (self.mysql_conn and self.mysql_conn.success) and not (self.postgres_conn and self.postgres_conn.success):
                self.skipTest("No database connections available")
                
            # Test with MySQL if available
            if self.mysql_conn and self.mysql_conn.success:
                # Insert data
                result = await database.execute_query(
                    self.mysql_conn,
                    "INSERT INTO test_table (name) VALUES (%s), (%s)",
                    ("Test1", "Test2")
                )
                self.assertTrue(result.success)
                self.assertEqual(result.rowcount, 2)
                
                # Test with invalid query
                result = await database.execute_query(
                    self.mysql_conn,
                    "INSERT INTO nonexistent_table (name) VALUES (%s)",
                    ("Test",)
                )
                self.assertFalse(result.success)
                self.assertIn("Error executing MySQL query", result.message)
                
            # Test with PostgreSQL if available
            if self.postgres_conn and self.postgres_conn.success:
                # Insert data
                result = await database.execute_query(
                    self.postgres_conn,
                    "INSERT INTO test_table (name) VALUES ($1), ($2)",
                    ("Test1", "Test2")
                )
                self.assertTrue(result.success)
                
                # Test with invalid query
                result = await database.execute_query(
                    self.postgres_conn,
                    "INSERT INTO nonexistent_table (name) VALUES ($1)",
                    ("Test",)
                )
                self.assertFalse(result.success)
                self.assertIn("Error executing PostgreSQL query", result.message)
                
            # Test with invalid connection
            invalid_conn = database.ConnectionResult(success=False, message="Invalid connection", db_type="mysql")
            result = await database.execute_query(invalid_conn, "SELECT 1")
            self.assertFalse(result.success)
            self.assertIn("Invalid connection", result.message)
        
        asyncio.run(run_test())

    def test_execute_read_query(self):
        async def run_test():
            if not (self.mysql_conn and self.mysql_conn.success) and not (self.postgres_conn and self.postgres_conn.success):
                self.skipTest("No database connections available")
                
            # Test with MySQL if available
            if self.mysql_conn and self.mysql_conn.success:
                # Insert test data
                await database.execute_query(
                    self.mysql_conn,
                    "INSERT INTO test_table (name) VALUES (%s), (%s)",
                    ("Test1", "Test2")
                )
                
                # Read data
                result = await database.execute_read_query(
                    self.mysql_conn,
                    "SELECT * FROM test_table ORDER BY id"
                )
                self.assertTrue(result.success)
                self.assertEqual(result.rowcount, 2)
                self.assertEqual(len(result.data), 2)
                self.assertEqual(result.data[0]["name"], "Test1")
                self.assertEqual(result.data[1]["name"], "Test2")
                
                # Test with parameters
                result = await database.execute_read_query(
                    self.mysql_conn,
                    "SELECT * FROM test_table WHERE name = %s",
                    ("Test1",)
                )
                self.assertTrue(result.success)
                self.assertEqual(result.rowcount, 1)
                self.assertEqual(result.data[0]["name"], "Test1")
                
                # Test with invalid query
                result = await database.execute_read_query(
                    self.mysql_conn,
                    "SELECT * FROM nonexistent_table"
                )
                self.assertFalse(result.success)
                self.assertIn("Error executing MySQL read query", result.message)
                
            # Test with PostgreSQL if available
            if self.postgres_conn and self.postgres_conn.success:
                # Insert test data
                await database.execute_query(
                    self.postgres_conn,
                    "INSERT INTO test_table (name) VALUES ($1), ($2)",
                    ("Test1", "Test2")
                )
                
                # Read data
                result = await database.execute_read_query(
                    self.postgres_conn,
                    "SELECT * FROM test_table ORDER BY id"
                )
                self.assertTrue(result.success)
                self.assertEqual(result.rowcount, 2)
                self.assertEqual(len(result.data), 2)
                self.assertEqual(result.data[0]["name"], "Test1")
                self.assertEqual(result.data[1]["name"], "Test2")
                
                # Test with parameters
                result = await database.execute_read_query(
                    self.postgres_conn,
                    "SELECT * FROM test_table WHERE name = $1",
                    ("Test1",)
                )
                self.assertTrue(result.success)
                self.assertEqual(result.rowcount, 1)
                self.assertEqual(result.data[0]["name"], "Test1")
                
                # Test with invalid query
                result = await database.execute_read_query(
                    self.postgres_conn,
                    "SELECT * FROM nonexistent_table"
                )
                self.assertFalse(result.success)
                self.assertIn("Error executing PostgreSQL read query", result.message)
                
            # Test with invalid connection
            invalid_conn = database.ConnectionResult(success=False, message="Invalid connection", db_type="mysql")
            result = await database.execute_read_query(invalid_conn, "SELECT 1")
            self.assertFalse(result.success)
            self.assertIn("Invalid connection", result.message)
        
        asyncio.run(run_test())

    def test_close_connection(self):
        async def run_test():
            # Test closing MySQL connection if available
            if self.mysql_conn and self.mysql_conn.success:
                result = await database.close_database_connection(self.mysql_conn)
                self.assertTrue(result.success)
                self.assertIn("Connection to mysql database closed successfully", result.message)
                
            # Test closing PostgreSQL connection if available
            if self.postgres_conn and self.postgres_conn.success:
                result = await database.close_database_connection(self.postgres_conn)
                self.assertTrue(result.success)
                self.assertIn("Connection to postgres database closed successfully", result.message)
                
            # Test with invalid connection
            invalid_conn = database.ConnectionResult(success=False, message="Invalid connection", db_type="mysql")
            result = await database.close_database_connection(invalid_conn)
            self.assertFalse(result.success)
            self.assertIn("Invalid connection", result.message)
            
            # Test with unsupported database type
            unsupported_conn = database.ConnectionResult(success=True, message="Connected", connection={}, db_type="unsupported")
            result = await database.close_database_connection(unsupported_conn)
            self.assertFalse(result.success)
            self.assertIn("Unsupported database type", result.message)
            
            # Clean up
            await self.async_tearDown()
        
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
