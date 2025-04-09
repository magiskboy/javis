import unittest
import redis
from unittest.mock import patch, MagicMock

from javis.tools import redis as redis_tools


class TestRedis(unittest.TestCase):
    def setUp(self):
        # Create a mock Redis connection for testing
        self.mock_redis = MagicMock(spec=redis.Redis)
        self.connection_result = redis_tools.RedisConnectionResult(
            success=True,
            message="Test connection",
            connection=self.mock_redis
        )
        self.failed_connection = redis_tools.RedisConnectionResult(
            success=False,
            message="Failed connection",
            connection=None
        )

    @patch('redis.Redis')
    def test_create_connection(self, mock_redis_class):
        # Setup mock
        mock_instance = MagicMock()
        mock_redis_class.return_value = mock_instance
        
        # Test successful connection
        result = redis_tools.create_connection(host="localhost", port=6379, db=0)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.connection)
        mock_redis_class.assert_called_with(host="localhost", port=6379, db=0, password=None)
        
        # Test connection error
        mock_instance.ping.side_effect = redis.ConnectionError("Connection refused")
        result = redis_tools.create_connection()
        self.assertFalse(result.success)
        self.assertIsNone(result.connection)
        self.assertIn("Connection refused", result.message)
        
        # Test unexpected error
        mock_instance.ping.side_effect = Exception("Unexpected error")
        result = redis_tools.create_connection()
        self.assertFalse(result.success)
        self.assertIsNone(result.connection)
        self.assertIn("Unexpected error", result.message)

    def test_execute_command(self):
        # Setup mock
        self.mock_redis.execute_command.return_value = "OK"
        
        # Test successful command execution
        result = redis_tools.execute_command(self.connection_result, "PING")
        self.assertTrue(result.success)
        self.assertEqual(result.data, "OK")
        self.mock_redis.execute_command.assert_called_with("PING")
        
        # Test with failed connection
        result = redis_tools.execute_command(self.failed_connection, "PING")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test Redis error
        self.mock_redis.execute_command.side_effect = redis.RedisError("Command error")
        result = redis_tools.execute_command(self.connection_result, "PING")
        self.assertFalse(result.success)
        self.assertIn("Command error", result.message)
        
        # Test unexpected error
        self.mock_redis.execute_command.side_effect = Exception("Unexpected error")
        result = redis_tools.execute_command(self.connection_result, "PING")
        self.assertFalse(result.success)
        self.assertIn("Unexpected error", result.message)

    def test_close_connection(self):
        # Test successful connection close
        result = redis_tools.close_redis_connection(self.connection_result)
        self.assertTrue(result.success)
        self.mock_redis.close.assert_called_once()
        
        # Test with failed connection
        result = redis_tools.close_redis_connection(self.failed_connection)
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error during close
        self.mock_redis.close.side_effect = Exception("Close error")
        result = redis_tools.close_redis_connection(self.connection_result)
        self.assertFalse(result.success)
        self.assertIn("Close error", result.message)

    def test_key_exists(self):
        # Setup mock
        self.mock_redis.exists.return_value = 1
        
        # Test key exists
        result = redis_tools.key_exists(self.connection_result, "test_key")
        self.assertTrue(result.success)
        self.assertTrue(result.data)
        self.mock_redis.exists.assert_called_with("test_key")
        
        # Test key doesn't exist
        self.mock_redis.exists.return_value = 0
        result = redis_tools.key_exists(self.connection_result, "nonexistent_key")
        self.assertTrue(result.success)
        self.assertFalse(result.data)
        
        # Test with failed connection
        result = redis_tools.key_exists(self.failed_connection, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.exists.side_effect = Exception("Error checking key")
        result = redis_tools.key_exists(self.connection_result, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Error checking key", result.message)

    def test_get_all_keys(self):
        # Setup mock
        self.mock_redis.keys.return_value = [b"key1", b"key2", b"key3"]
        
        # Test getting all keys
        result = redis_tools.get_all_keys(self.connection_result)
        self.assertTrue(result.success)
        self.assertEqual(result.data, ["key1", "key2", "key3"])
        self.mock_redis.keys.assert_called_with("*")
        
        # Test with pattern
        result = redis_tools.get_all_keys(self.connection_result, "key*")
        self.assertTrue(result.success)
        self.mock_redis.keys.assert_called_with("key*")
        
        # Test with failed connection
        result = redis_tools.get_all_keys(self.failed_connection)
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.keys.side_effect = Exception("Error getting keys")
        result = redis_tools.get_all_keys(self.connection_result)
        self.assertFalse(result.success)
        self.assertIn("Error getting keys", result.message)

    def test_get_value(self):
        # Setup mock
        self.mock_redis.get.return_value = b"test_value"
        
        # Test getting value
        result = redis_tools.get_value(self.connection_result, "test_key")
        self.assertTrue(result.success)
        self.assertEqual(result.data, "test_value")
        self.mock_redis.get.assert_called_with("test_key")
        
        # Test key doesn't exist
        self.mock_redis.get.return_value = None
        result = redis_tools.get_value(self.connection_result, "nonexistent_key")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with failed connection
        result = redis_tools.get_value(self.failed_connection, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.get.side_effect = Exception("Error getting value")
        result = redis_tools.get_value(self.connection_result, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Error getting value", result.message)

    def test_set_value(self):
        # Setup mock
        self.mock_redis.set.return_value = True
        
        # Test setting value
        result = redis_tools.set_value(self.connection_result, "test_key", "test_value")
        self.assertTrue(result.success)
        self.mock_redis.set.assert_called_with("test_key", "test_value", ex=None, px=None, nx=False, xx=False)
        
        # Test with expiration
        result = redis_tools.set_value(self.connection_result, "test_key", "test_value", ex=60)
        self.assertTrue(result.success)
        self.mock_redis.set.assert_called_with("test_key", "test_value", ex=60, px=None, nx=False, xx=False)
        
        # Test condition not met
        self.mock_redis.set.return_value = None
        result = redis_tools.set_value(self.connection_result, "test_key", "test_value", nx=True)
        self.assertFalse(result.success)
        self.assertIn("condition not met", result.message)
        
        # Test with failed connection
        result = redis_tools.set_value(self.failed_connection, "test_key", "test_value")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.set.side_effect = Exception("Error setting value")
        result = redis_tools.set_value(self.connection_result, "test_key", "test_value")
        self.assertFalse(result.success)
        self.assertIn("Error setting value", result.message)

    def test_delete_key(self):
        # Setup mock
        self.mock_redis.delete.return_value = 1
        
        # Test deleting key
        result = redis_tools.delete_key(self.connection_result, "test_key")
        self.assertTrue(result.success)
        self.assertEqual(result.data, 1)
        self.mock_redis.delete.assert_called_with("test_key")
        
        # Test deleting multiple keys
        result = redis_tools.delete_key(self.connection_result, "key1", "key2", "key3")
        self.assertTrue(result.success)
        self.mock_redis.delete.assert_called_with("key1", "key2", "key3")
        
        # Test with no keys
        result = redis_tools.delete_key(self.connection_result)
        self.assertFalse(result.success)
        self.assertIn("No keys specified", result.message)
        
        # Test with failed connection
        result = redis_tools.delete_key(self.failed_connection, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.delete.side_effect = Exception("Error deleting keys")
        result = redis_tools.delete_key(self.connection_result, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Error deleting keys", result.message)

    def test_flush_db(self):
        # Test flushing database
        result = redis_tools.flush_db(self.connection_result)
        self.assertTrue(result.success)
        self.mock_redis.flushdb.assert_called_once()
        
        # Test with failed connection
        result = redis_tools.flush_db(self.failed_connection)
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.flushdb.side_effect = Exception("Error flushing database")
        result = redis_tools.flush_db(self.connection_result)
        self.assertFalse(result.success)
        self.assertIn("Error flushing database", result.message)

    def test_get_key_type(self):
        # Setup mock
        self.mock_redis.type.return_value = b"string"
        
        # Test getting key type
        result = redis_tools.get_key_type(self.connection_result, "test_key")
        self.assertTrue(result.success)
        self.assertEqual(result.data, "string")
        self.mock_redis.type.assert_called_with("test_key")
        
        # Test key doesn't exist
        self.mock_redis.type.return_value = b"none"
        result = redis_tools.get_key_type(self.connection_result, "nonexistent_key")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with failed connection
        result = redis_tools.get_key_type(self.failed_connection, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.type.side_effect = Exception("Error getting key type")
        result = redis_tools.get_key_type(self.connection_result, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Error getting key type", result.message)

    def test_get_ttl(self):
        # Setup mock
        self.mock_redis.ttl.return_value = 60
        
        # Test getting TTL
        result = redis_tools.get_ttl(self.connection_result, "test_key")
        self.assertTrue(result.success)
        self.assertEqual(result.data, 60)
        self.mock_redis.ttl.assert_called_with("test_key")
        
        # Test key doesn't exist
        self.mock_redis.ttl.return_value = -2
        result = redis_tools.get_ttl(self.connection_result, "nonexistent_key")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test key exists but has no TTL
        self.mock_redis.ttl.return_value = -1
        result = redis_tools.get_ttl(self.connection_result, "test_key")
        self.assertTrue(result.success)
        self.assertEqual(result.data, -1)
        
        # Test with failed connection
        result = redis_tools.get_ttl(self.failed_connection, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.ttl.side_effect = Exception("Error getting TTL")
        result = redis_tools.get_ttl(self.connection_result, "test_key")
        self.assertFalse(result.success)
        self.assertIn("Error getting TTL", result.message)

    def test_set_ttl(self):
        # Setup mock
        self.mock_redis.expire.return_value = 1
        
        # Test setting TTL
        result = redis_tools.set_ttl(self.connection_result, "test_key", 60)
        self.assertTrue(result.success)
        self.mock_redis.expire.assert_called_with("test_key", 60)
        
        # Test key doesn't exist
        self.mock_redis.expire.return_value = 0
        result = redis_tools.set_ttl(self.connection_result, "nonexistent_key", 60)
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with failed connection
        result = redis_tools.set_ttl(self.failed_connection, "test_key", 60)
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.expire.side_effect = Exception("Error setting TTL")
        result = redis_tools.set_ttl(self.connection_result, "test_key", 60)
        self.assertFalse(result.success)
        self.assertIn("Error setting TTL", result.message)

    def test_list_push(self):
        # Setup mock
        self.mock_redis.rpush.return_value = 3
        self.mock_redis.lpush.return_value = 3
        
        # Test right push
        result = redis_tools.list_push(self.connection_result, "test_list", "value1", "value2")
        self.assertTrue(result.success)
        self.assertEqual(result.data, 3)
        self.mock_redis.rpush.assert_called_with("test_list", "value1", "value2")
        
        # Test left push
        result = redis_tools.list_push(self.connection_result, "test_list", "value1", "value2", left=True)
        self.assertTrue(result.success)
        self.assertEqual(result.data, 3)
        self.mock_redis.lpush.assert_called_with("test_list", "value1", "value2")
        
        # Test with no values
        result = redis_tools.list_push(self.connection_result, "test_list")
        self.assertFalse(result.success)
        self.assertIn("No values specified", result.message)
        
        # Test with failed connection
        result = redis_tools.list_push(self.failed_connection, "test_list", "value")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.rpush.side_effect = Exception("Error pushing to list")
        result = redis_tools.list_push(self.connection_result, "test_list", "value")
        self.assertFalse(result.success)
        self.assertIn("Error pushing to list", result.message)

    def test_list_pop(self):
        # Setup mock
        self.mock_redis.rpop.return_value = b"value"
        self.mock_redis.lpop.return_value = b"value"
        
        # Test right pop
        result = redis_tools.list_pop(self.connection_result, "test_list")
        self.assertTrue(result.success)
        self.assertEqual(result.data, "value")
        self.mock_redis.rpop.assert_called_with("test_list")
        
        # Test left pop
        result = redis_tools.list_pop(self.connection_result, "test_list", left=True)
        self.assertTrue(result.success)
        self.assertEqual(result.data, "value")
        self.mock_redis.lpop.assert_called_with("test_list")
        
        # Test empty list
        self.mock_redis.rpop.return_value = None
        result = redis_tools.list_pop(self.connection_result, "test_list")
        self.assertFalse(result.success)
        self.assertIn("empty or does not exist", result.message)
        
        # Test with failed connection
        result = redis_tools.list_pop(self.failed_connection, "test_list")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.rpop.side_effect = Exception("Error popping from list")
        result = redis_tools.list_pop(self.connection_result, "test_list")
        self.assertFalse(result.success)
        self.assertIn("Error popping from list", result.message)

    def test_list_range(self):
        # Setup mock
        self.mock_redis.lrange.return_value = [b"value1", b"value2", b"value3"]
        
        # Test getting range
        result = redis_tools.list_range(self.connection_result, "test_list")
        self.assertTrue(result.success)
        self.assertEqual(result.data, ["value1", "value2", "value3"])
        self.mock_redis.lrange.assert_called_with("test_list", 0, -1)
        
        # Test with custom range
        result = redis_tools.list_range(self.connection_result, "test_list", 1, 2)
        self.assertTrue(result.success)
        self.mock_redis.lrange.assert_called_with("test_list", 1, 2)
        
        # Test with failed connection
        result = redis_tools.list_range(self.failed_connection, "test_list")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.lrange.side_effect = Exception("Error getting list range")
        result = redis_tools.list_range(self.connection_result, "test_list")
        self.assertFalse(result.success)
        self.assertIn("Error getting list range", result.message)

    def test_hash_set(self):
        # Setup mock
        self.mock_redis.hset.return_value = 2
        
        # Test setting hash fields with dictionary
        result = redis_tools.hash_set(self.connection_result, "test_hash", {"field1": "value1", "field2": "value2"})
        self.assertTrue(result.success)
        self.assertEqual(result.data, 2)
        self.mock_redis.hset.assert_called_with("test_hash", mapping={"field1": "value1", "field2": "value2"})
        
        # Test setting hash fields with kwargs
        result = redis_tools.hash_set(self.connection_result, "test_hash", field1="value1", field2="value2")
        self.assertTrue(result.success)
        self.assertEqual(result.data, 2)
        self.mock_redis.hset.assert_called_with("test_hash", mapping={"field1": "value1", "field2": "value2"})
        
        # Test with no fields
        result = redis_tools.hash_set(self.connection_result, "test_hash")
        self.assertFalse(result.success)
        self.assertIn("No field-value pairs", result.message)
        
        # Test with failed connection
        result = redis_tools.hash_set(self.failed_connection, "test_hash", field="value")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.hset.side_effect = Exception("Error setting hash fields")
        result = redis_tools.hash_set(self.connection_result, "test_hash", field="value")
        self.assertFalse(result.success)
        self.assertIn("Error setting hash fields", result.message)

    def test_hash_get(self):
        # Setup mock
        self.mock_redis.hget.return_value = b"value"
        
        # Test getting hash field
        result = redis_tools.hash_get(self.connection_result, "test_hash", "field")
        self.assertTrue(result.success)
        self.assertEqual(result.data, "value")
        self.mock_redis.hget.assert_called_with("test_hash", "field")
        
        # Test field doesn't exist
        self.mock_redis.hget.return_value = None
        result = redis_tools.hash_get(self.connection_result, "test_hash", "nonexistent_field")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with failed connection
        result = redis_tools.hash_get(self.failed_connection, "test_hash", "field")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.hget.side_effect = Exception("Error getting hash field")
        result = redis_tools.hash_get(self.connection_result, "test_hash", "field")
        self.assertFalse(result.success)
        self.assertIn("Error getting hash field", result.message)

    def test_hash_get_all(self):
        # Setup mock
        self.mock_redis.hgetall.return_value = {b"field1": b"value1", b"field2": b"value2"}
        
        # Test getting all hash fields
        result = redis_tools.hash_get_all(self.connection_result, "test_hash")
        self.assertTrue(result.success)
        self.assertEqual(result.data, {"field1": "value1", "field2": "value2"})
        self.mock_redis.hgetall.assert_called_with("test_hash")
        
        # Test empty hash
        self.mock_redis.hgetall.return_value = {}
        result = redis_tools.hash_get_all(self.connection_result, "test_hash")
        self.assertFalse(result.success)
        self.assertIn("empty or does not exist", result.message)
        
        # Test with failed connection
        result = redis_tools.hash_get_all(self.failed_connection, "test_hash")
        self.assertFalse(result.success)
        self.assertIn("Invalid connection", result.message)
        
        # Test error
        self.mock_redis.hgetall.side_effect = Exception("Error getting all hash fields")
        result = redis_tools.hash_get_all(self.connection_result, "test_hash")
        self.assertFalse(result.success)
        self.assertIn("Error getting all hash fields", result.message)


if __name__ == "__main__":
    unittest.main()
