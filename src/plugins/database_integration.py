"""
JARVIS 2.0 - Database Integration Plugin
Multi-database query system with schema analysis and optimization
"""

import asyncio
import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib

try:
    # PostgreSQL
    import asyncpg
    import psycopg2
    
    # MySQL
    import aiomysql
    import pymysql
    
    # SQLite
    import aiosqlite
    import sqlite3
    
    # MongoDB
    import motor.motor_asyncio
    import pymongo
    
    # SQL Analysis
    import sqlparse
    from sqlparse import sql, tokens
    
    DATABASE_DEPS_AVAILABLE = True
except ImportError:
    DATABASE_DEPS_AVAILABLE = False

from src.core.tools.base import BaseTool, ToolParameter
from src.core.logger import logger


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"


class QueryType(Enum):
    """SQL query types."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    DROP = "drop"
    ALTER = "alter"
    INDEX = "index"
    UNKNOWN = "unknown"


class IndexType(Enum):
    """Database index types."""
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    UNIQUE = "unique"
    PARTIAL = "partial"


@dataclass
class DatabaseConnection:
    """Database connection configuration."""
    name: str
    db_type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    connection_pool_size: int = 10
    connection_timeout: int = 30
    
    def get_connection_string(self) -> str:
        """Generate connection string for the database."""
        if self.db_type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        elif self.db_type == DatabaseType.MYSQL:
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}"
        elif self.db_type == DatabaseType.MONGODB:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")


@dataclass
class QueryResult:
    """Database query result."""
    query: str
    query_type: QueryType
    execution_time: float
    rows_affected: int
    columns: List[str]
    data: List[Dict[str, Any]]
    error: Optional[str] = None
    query_plan: Optional[Dict[str, Any]] = None
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "query_type": self.query_type.value,
            "execution_time": self.execution_time,
            "rows_affected": self.rows_affected,
            "columns": self.columns,
            "data": self.data,
            "error": self.error,
            "query_plan": self.query_plan,
            "cache_hit": self.cache_hit
        }


@dataclass
class TableSchema:
    """Database table schema information."""
    table_name: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    row_count: int
    table_size: str
    database_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class QueryAnalysis:
    """SQL query analysis result."""
    query: str
    query_type: QueryType
    tables_used: List[str]
    columns_used: List[str]
    has_joins: bool
    has_subqueries: bool
    has_aggregates: bool
    complexity_score: int
    estimated_cost: Optional[float]
    suggestions: List[str]
    potential_issues: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "query_type": self.query_type.value,
            "tables_used": self.tables_used,
            "columns_used": self.columns_used,
            "has_joins": self.has_joins,
            "has_subqueries": self.has_subqueries,
            "has_aggregates": self.has_aggregates,
            "complexity_score": self.complexity_score,
            "estimated_cost": self.estimated_cost,
            "suggestions": self.suggestions,
            "potential_issues": self.potential_issues
        }


class QueryCache:
    """Simple in-memory query result cache."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _get_cache_key(self, query: str, db_name: str) -> str:
        """Generate cache key for query."""
        content = f"{db_name}:{query}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, db_name: str) -> Optional[QueryResult]:
        """Get cached query result."""
        key = self._get_cache_key(query, db_name)
        
        if key not in self.cache:
            return None
        
        # Check TTL
        now = datetime.now()
        if (now - self.access_times[key]).total_seconds() > self.ttl_seconds:
            del self.cache[key]
            del self.access_times[key]
            return None
        
        # Update access time
        self.access_times[key] = now
        
        result = self.cache[key]
        result.cache_hit = True
        return result
    
    def set(self, query: str, db_name: str, result: QueryResult):
        """Cache query result."""
        key = self._get_cache_key(query, db_name)
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = result
        self.access_times[key] = datetime.now()
    
    def clear(self):
        """Clear all cached results."""
        self.cache.clear()
        self.access_times.clear()


class SQLAnalyzer:
    """SQL query analyzer and optimizer."""
    
    def __init__(self):
        self.aggregate_functions = {
            'count', 'sum', 'avg', 'min', 'max', 'group_concat',
            'string_agg', 'array_agg', 'stddev', 'variance'
        }
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze SQL query for optimization opportunities."""
        try:
            parsed = sqlparse.parse(query)[0]
            
            # Extract basic information
            query_type = self._get_query_type(parsed)
            tables_used = self._extract_tables(parsed)
            columns_used = self._extract_columns(parsed)
            
            # Analyze complexity
            has_joins = self._has_joins(parsed)
            has_subqueries = self._has_subqueries(parsed)
            has_aggregates = self._has_aggregates(parsed)
            
            complexity_score = self._calculate_complexity_score(
                len(tables_used), has_joins, has_subqueries, has_aggregates
            )
            
            # Generate suggestions
            suggestions = self._generate_suggestions(
                parsed, query_type, tables_used, has_joins, has_subqueries
            )
            
            # Identify potential issues
            potential_issues = self._identify_issues(
                parsed, query_type, tables_used, columns_used
            )
            
            return QueryAnalysis(
                query=query,
                query_type=query_type,
                tables_used=tables_used,
                columns_used=columns_used,
                has_joins=has_joins,
                has_subqueries=has_subqueries,
                has_aggregates=has_aggregates,
                complexity_score=complexity_score,
                estimated_cost=None,  # Would require schema information
                suggestions=suggestions,
                potential_issues=potential_issues
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            return QueryAnalysis(
                query=query,
                query_type=QueryType.UNKNOWN,
                tables_used=[],
                columns_used=[],
                has_joins=False,
                has_subqueries=False,
                has_aggregates=False,
                complexity_score=0,
                estimated_cost=None,
                suggestions=[],
                potential_issues=[f"Analysis failed: {str(e)}"]
            )
    
    def _get_query_type(self, parsed) -> QueryType:
        """Determine query type from parsed SQL."""
        first_token = None
        for token in parsed.flatten():
            if token.ttype in (tokens.Keyword, tokens.Keyword.DML):
                first_token = token.value.upper()
                break
        
        if first_token in ('SELECT',):
            return QueryType.SELECT
        elif first_token in ('INSERT',):
            return QueryType.INSERT
        elif first_token in ('UPDATE',):
            return QueryType.UPDATE
        elif first_token in ('DELETE',):
            return QueryType.DELETE
        elif first_token in ('CREATE',):
            return QueryType.CREATE
        elif first_token in ('DROP',):
            return QueryType.DROP
        elif first_token in ('ALTER',):
            return QueryType.ALTER
        else:
            return QueryType.UNKNOWN
    
    def _extract_tables(self, parsed) -> List[str]:
        """Extract table names from parsed query."""
        tables = []
        
        def extract_from_token(token):
            if hasattr(token, 'tokens'):
                for subtoken in token.tokens:
                    if isinstance(subtoken, sql.IdentifierList):
                        for identifier in subtoken.get_identifiers():
                            tables.append(str(identifier).strip())
                    elif isinstance(subtoken, sql.Identifier):
                        tables.append(str(subtoken).strip())
                    else:
                        extract_from_token(subtoken)
        
        # Look for FROM and JOIN clauses
        in_from = False
        for token in parsed.tokens:
            if token.ttype is tokens.Keyword and token.value.upper() == 'FROM':
                in_from = True
            elif in_from and isinstance(token, sql.IdentifierList):
                for identifier in token.get_identifiers():
                    tables.append(str(identifier).strip())
            elif in_from and isinstance(token, sql.Identifier):
                tables.append(str(token).strip())
            elif token.ttype is tokens.Keyword and token.value.upper() in ('WHERE', 'GROUP', 'ORDER', 'HAVING'):
                in_from = False
        
        return list(set(tables))
    
    def _extract_columns(self, parsed) -> List[str]:
        """Extract column names from parsed query."""
        columns = []
        
        def extract_identifiers(token):
            if isinstance(token, sql.IdentifierList):
                for identifier in token.get_identifiers():
                    columns.append(str(identifier).strip())
            elif isinstance(token, sql.Identifier):
                columns.append(str(token).strip())
            elif hasattr(token, 'tokens'):
                for subtoken in token.tokens:
                    extract_identifiers(subtoken)
        
        for token in parsed.tokens:
            extract_identifiers(token)
        
        return list(set(columns))
    
    def _has_joins(self, parsed) -> bool:
        """Check if query contains JOIN operations."""
        query_str = str(parsed).upper()
        join_keywords = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']
        return any(keyword in query_str for keyword in join_keywords)
    
    def _has_subqueries(self, parsed) -> bool:
        """Check if query contains subqueries."""
        def check_subquery(token):
            if isinstance(token, sql.Parenthesis):
                inner = str(token).strip('()')
                if any(keyword in inner.upper() for keyword in ['SELECT', 'WITH']):
                    return True
            elif hasattr(token, 'tokens'):
                for subtoken in token.tokens:
                    if check_subquery(subtoken):
                        return True
            return False
        
        return check_subquery(parsed)
    
    def _has_aggregates(self, parsed) -> bool:
        """Check if query contains aggregate functions."""
        query_str = str(parsed).upper()
        return any(f'{func}(' in query_str for func in self.aggregate_functions)
    
    def _calculate_complexity_score(self, table_count: int, has_joins: bool, 
                                  has_subqueries: bool, has_aggregates: bool) -> int:
        """Calculate query complexity score."""
        score = table_count * 10
        if has_joins:
            score += 20
        if has_subqueries:
            score += 30
        if has_aggregates:
            score += 15
        return score
    
    def _generate_suggestions(self, parsed, query_type: QueryType, tables: List[str],
                            has_joins: bool, has_subqueries: bool) -> List[str]:
        """Generate optimization suggestions."""
        suggestions = []
        
        if query_type == QueryType.SELECT:
            # Check for SELECT *
            if 'SELECT *' in str(parsed).upper():
                suggestions.append("Consider specifying specific columns instead of SELECT *")
            
            # Check for missing WHERE clause
            if not any('WHERE' in str(token).upper() for token in parsed.tokens):
                suggestions.append("Consider adding WHERE clause to limit results")
            
            # Multiple table suggestions
            if len(tables) > 3:
                suggestions.append("Query involves many tables - consider breaking into smaller queries")
            
            # Join suggestions
            if has_joins:
                suggestions.append("Ensure proper indexes exist on JOIN columns")
        
        if has_subqueries:
            suggestions.append("Consider if subqueries can be rewritten as JOINs for better performance")
        
        return suggestions
    
    def _identify_issues(self, parsed, query_type: QueryType, tables: List[str], 
                        columns: List[str]) -> List[str]:
        """Identify potential query issues."""
        issues = []
        query_str = str(parsed).upper()
        
        # Check for cartesian products
        if len(tables) > 1 and 'WHERE' not in query_str:
            issues.append("Potential cartesian product - missing WHERE clause with table relations")
        
        # Check for functions in WHERE clause
        if re.search(r'WHERE.*\w+\([^)]*\)', query_str):
            issues.append("Function calls in WHERE clause may prevent index usage")
        
        # Check for LIKE with leading wildcard
        if re.search(r"LIKE\s+['\"]%", query_str):
            issues.append("LIKE with leading wildcard cannot use indexes efficiently")
        
        # Check for ORDER BY without LIMIT
        if 'ORDER BY' in query_str and 'LIMIT' not in query_str:
            issues.append("ORDER BY without LIMIT may cause unnecessary sorting of large result sets")
        
        return issues


class DatabaseManager:
    """Base database manager class."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.pool = None
    
    async def connect(self) -> bool:
        """Connect to database."""
        raise NotImplementedError
    
    async def disconnect(self):
        """Disconnect from database."""
        raise NotImplementedError
    
    async def execute_query(self, query: str, params: Optional[List] = None) -> QueryResult:
        """Execute SQL query."""
        raise NotImplementedError
    
    async def get_schema(self, table_name: Optional[str] = None) -> List[TableSchema]:
        """Get database schema information."""
        raise NotImplementedError


class PostgreSQLManager(DatabaseManager):
    """PostgreSQL database manager."""
    
    async def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.connection.host,
                port=self.connection.port,
                user=self.connection.username,
                password=self.connection.password,
                database=self.connection.database,
                min_size=1,
                max_size=self.connection.connection_pool_size,
                command_timeout=self.connection.connection_timeout
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from PostgreSQL."""
        if self.pool:
            await self.pool.close()
    
    async def execute_query(self, query: str, params: Optional[List] = None) -> QueryResult:
        """Execute PostgreSQL query."""
        start_time = datetime.now()
        
        try:
            async with self.pool.acquire() as conn:
                # Determine query type
                query_type = self._get_query_type(query)
                
                if query_type == QueryType.SELECT:
                    result = await conn.fetch(query, *(params or []))
                    rows_affected = len(result)
                    columns = list(result[0].keys()) if result else []
                    data = [dict(row) for row in result]
                else:
                    result = await conn.execute(query, *(params or []))
                    rows_affected = int(result.split()[-1]) if result else 0
                    columns = []
                    data = []
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return QueryResult(
                    query=query,
                    query_type=query_type,
                    execution_time=execution_time,
                    rows_affected=rows_affected,
                    columns=columns,
                    data=data
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return QueryResult(
                query=query,
                query_type=self._get_query_type(query),
                execution_time=execution_time,
                rows_affected=0,
                columns=[],
                data=[],
                error=str(e)
            )
    
    async def get_schema(self, table_name: Optional[str] = None) -> List[TableSchema]:
        """Get PostgreSQL schema information."""
        schemas = []
        
        try:
            async with self.pool.acquire() as conn:
                # Get tables
                if table_name:
                    table_query = """
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = $1
                    """
                    tables = await conn.fetch(table_query, table_name)
                else:
                    table_query = """
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """
                    tables = await conn.fetch(table_query)
                
                for table in tables:
                    table_name = table['table_name']
                    
                    # Get columns
                    columns_query = """
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = $1 AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """
                    columns = await conn.fetch(columns_query, table_name)
                    
                    # Get indexes
                    indexes_query = """
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE tablename = $1
                    """
                    indexes = await conn.fetch(indexes_query, table_name)
                    
                    # Get row count
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                    count_result = await conn.fetchval(count_query)
                    
                    # Get table size
                    size_query = "SELECT pg_size_pretty(pg_total_relation_size($1))"
                    table_size = await conn.fetchval(size_query, table_name)
                    
                    schemas.append(TableSchema(
                        table_name=table_name,
                        columns=[dict(col) for col in columns],
                        indexes=[dict(idx) for idx in indexes],
                        constraints=[],  # TODO: Implement constraint fetching
                        row_count=count_result,
                        table_size=table_size,
                        database_name=self.connection.database
                    ))
            
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL schema: {e}")
            return []
    
    def _get_query_type(self, query: str) -> QueryType:
        """Determine query type."""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif query_upper.startswith('CREATE'):
            return QueryType.CREATE
        elif query_upper.startswith('DROP'):
            return QueryType.DROP
        elif query_upper.startswith('ALTER'):
            return QueryType.ALTER
        else:
            return QueryType.UNKNOWN


class MySQLManager(DatabaseManager):
    """MySQL database manager."""
    
    async def connect(self) -> bool:
        """Connect to MySQL database."""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.connection.host,
                port=self.connection.port,
                user=self.connection.username,
                password=self.connection.password,
                db=self.connection.database,
                minsize=1,
                maxsize=self.connection.connection_pool_size
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MySQL."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
    
    async def execute_query(self, query: str, params: Optional[List] = None) -> QueryResult:
        """Execute MySQL query."""
        start_time = datetime.now()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params)
                    
                    query_type = self._get_query_type(query)
                    
                    if query_type == QueryType.SELECT:
                        result = await cursor.fetchall()
                        rows_affected = len(result)
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        data = list(result) if result else []
                    else:
                        rows_affected = cursor.rowcount
                        columns = []
                        data = []
                        await conn.commit()
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    return QueryResult(
                        query=query,
                        query_type=query_type,
                        execution_time=execution_time,
                        rows_affected=rows_affected,
                        columns=columns,
                        data=data
                    )
                    
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return QueryResult(
                query=query,
                query_type=self._get_query_type(query),
                execution_time=execution_time,
                rows_affected=0,
                columns=[],
                data=[],
                error=str(e)
            )
    
    def _get_query_type(self, query: str) -> QueryType:
        """Determine MySQL query type."""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif query_upper.startswith('CREATE'):
            return QueryType.CREATE
        elif query_upper.startswith('DROP'):
            return QueryType.DROP
        elif query_upper.startswith('ALTER'):
            return QueryType.ALTER
        else:
            return QueryType.UNKNOWN
    
    async def get_schema(self, table_name: Optional[str] = None) -> List[TableSchema]:
        """Get MySQL schema information."""
        # Implementation similar to PostgreSQL but with MySQL-specific queries
        return []


class SQLiteManager(DatabaseManager):
    """SQLite database manager."""
    
    async def connect(self) -> bool:
        """Connect to SQLite database."""
        try:
            # SQLite connection will be created per query
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from SQLite."""
        pass  # No persistent connection for SQLite
    
    async def execute_query(self, query: str, params: Optional[List] = None) -> QueryResult:
        """Execute SQLite query."""
        start_time = datetime.now()
        
        try:
            async with aiosqlite.connect(self.connection.database) as db:
                cursor = await db.execute(query, params or [])
                
                query_type = self._get_query_type(query)
                
                if query_type == QueryType.SELECT:
                    result = await cursor.fetchall()
                    rows_affected = len(result)
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    data = [dict(zip(columns, row)) for row in result] if result else []
                else:
                    rows_affected = cursor.rowcount
                    columns = []
                    data = []
                    await db.commit()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return QueryResult(
                    query=query,
                    query_type=query_type,
                    execution_time=execution_time,
                    rows_affected=rows_affected,
                    columns=columns,
                    data=data
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return QueryResult(
                query=query,
                query_type=self._get_query_type(query),
                execution_time=execution_time,
                rows_affected=0,
                columns=[],
                data=[],
                error=str(e)
            )
    
    def _get_query_type(self, query: str) -> QueryType:
        """Determine SQLite query type."""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif query_upper.startswith('CREATE'):
            return QueryType.CREATE
        elif query_upper.startswith('DROP'):
            return QueryType.DROP
        elif query_upper.startswith('ALTER'):
            return QueryType.ALTER
        else:
            return QueryType.UNKNOWN


class MongoDBManager:
    """MongoDB database manager."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.client = None
        self.db = None
    
    async def connect(self) -> bool:
        """Connect to MongoDB."""
        try:
            connection_string = self.connection.get_connection_string()
            self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
            self.db = self.client[self.connection.database]
            
            # Test connection
            await self.client.admin.command('ismaster')
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
    
    async def execute_query(self, collection: str, operation: str, 
                          query: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Execute MongoDB operation."""
        start_time = datetime.now()
        
        try:
            collection_obj = self.db[collection]
            result_data = []
            rows_affected = 0
            
            if operation == 'find':
                cursor = collection_obj.find(query or {})
                result_data = await cursor.to_list(length=None)
                rows_affected = len(result_data)
            
            elif operation == 'find_one':
                result = await collection_obj.find_one(query or {})
                result_data = [result] if result else []
                rows_affected = len(result_data)
            
            elif operation == 'insert_one':
                result = await collection_obj.insert_one(data)
                rows_affected = 1 if result.inserted_id else 0
            
            elif operation == 'insert_many':
                result = await collection_obj.insert_many(data)
                rows_affected = len(result.inserted_ids)
            
            elif operation == 'update_one':
                result = await collection_obj.update_one(query, data)
                rows_affected = result.modified_count
            
            elif operation == 'update_many':
                result = await collection_obj.update_many(query, data)
                rows_affected = result.modified_count
            
            elif operation == 'delete_one':
                result = await collection_obj.delete_one(query)
                rows_affected = result.deleted_count
            
            elif operation == 'delete_many':
                result = await collection_obj.delete_many(query)
                rows_affected = result.deleted_count
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "collection": collection,
                "operation": operation,
                "execution_time": execution_time,
                "rows_affected": rows_affected,
                "data": result_data
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "collection": collection,
                "operation": operation,
                "execution_time": execution_time,
                "rows_affected": 0,
                "data": [],
                "error": str(e)
            }


class DatabaseIntegrationTool(BaseTool):
    """Comprehensive database integration tool."""
    
    name = "database_integration"
    description = "Multi-database query system with schema analysis and optimization"
    
    def __init__(self):
        super().__init__()
        self.connections = {}  # name -> DatabaseConnection
        self.managers = {}     # name -> DatabaseManager
        self.query_cache = QueryCache()
        self.sql_analyzer = SQLAnalyzer()
    
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Action to perform",
                required=True,
                enum=[
                    "add_connection", "remove_connection", "list_connections",
                    "execute_query", "analyze_query", "get_schema", "optimize_query",
                    "test_connection", "export_data", "import_data", "migrate_data",
                    "create_index", "explain_plan", "query_performance"
                ]
            ),
            "connection_name": ToolParameter(
                name="connection_name",
                type="string",
                description="Database connection name",
                required=False
            ),
            "connection_config": ToolParameter(
                name="connection_config",
                type="object",
                description="Database connection configuration",
                required=False
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="SQL query to execute",
                required=False
            ),
            "params": ToolParameter(
                name="params",
                type="array",
                description="Query parameters",
                required=False
            ),
            "table_name": ToolParameter(
                name="table_name",
                type="string",
                description="Table name for schema operations",
                required=False
            ),
            "mongodb_operation": ToolParameter(
                name="mongodb_operation",
                type="object",
                description="MongoDB operation details",
                required=False
            ),
            "export_config": ToolParameter(
                name="export_config",
                type="object",
                description="Data export configuration",
                required=False
            ),
            "import_config": ToolParameter(
                name="import_config",
                type="object",
                description="Data import configuration",
                required=False
            )
        }
    
    async def execute(
        self,
        action: str,
        connection_name: Optional[str] = None,
        connection_config: Optional[Dict] = None,
        query: Optional[str] = None,
        params: Optional[List] = None,
        table_name: Optional[str] = None,
        mongodb_operation: Optional[Dict] = None,
        export_config: Optional[Dict] = None,
        import_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute database integration action."""
        if not DATABASE_DEPS_AVAILABLE:
            return {
                "success": False,
                "error": "Database dependencies not installed. Run: pip install asyncpg psycopg2 aiomysql pymysql aiosqlite motor pymongo sqlparse"
            }
        
        try:
            if action == "add_connection":
                return await self._add_connection(connection_name, connection_config)
            elif action == "remove_connection":
                return await self._remove_connection(connection_name)
            elif action == "list_connections":
                return await self._list_connections()
            elif action == "execute_query":
                return await self._execute_query(connection_name, query, params)
            elif action == "analyze_query":
                return await self._analyze_query(query)
            elif action == "get_schema":
                return await self._get_schema(connection_name, table_name)
            elif action == "test_connection":
                return await self._test_connection(connection_name)
            elif action == "mongodb_operation":
                return await self._mongodb_operation(connection_name, mongodb_operation)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Database integration error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _add_connection(self, name: str, config: Dict) -> Dict[str, Any]:
        """Add new database connection."""
        try:
            if not name or not config:
                return {"success": False, "error": "Connection name and config required"}
            
            # Parse database type
            db_type_str = config.get('type', '').lower()
            try:
                db_type = DatabaseType(db_type_str)
            except ValueError:
                return {"success": False, "error": f"Unsupported database type: {db_type_str}"}
            
            # Create connection object
            connection = DatabaseConnection(
                name=name,
                db_type=db_type,
                host=config.get('host', 'localhost'),
                port=config.get('port', self._get_default_port(db_type)),
                database=config.get('database', ''),
                username=config.get('username', ''),
                password=config.get('password', ''),
                ssl_mode=config.get('ssl_mode', 'prefer'),
                connection_pool_size=config.get('pool_size', 10),
                connection_timeout=config.get('timeout', 30)
            )
            
            # Create appropriate manager
            if db_type == DatabaseType.POSTGRESQL:
                manager = PostgreSQLManager(connection)
            elif db_type == DatabaseType.MYSQL:
                manager = MySQLManager(connection)
            elif db_type == DatabaseType.SQLITE:
                manager = SQLiteManager(connection)
            elif db_type == DatabaseType.MONGODB:
                manager = MongoDBManager(connection)
            else:
                return {"success": False, "error": f"Manager not implemented for {db_type}"}
            
            # Test connection
            connected = await manager.connect()
            if not connected:
                return {"success": False, "error": "Failed to connect to database"}
            
            # Store connection and manager
            self.connections[name] = connection
            self.managers[name] = manager
            
            return {
                "success": True,
                "message": f"Database connection '{name}' added successfully",
                "connection_type": db_type.value
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to add connection: {str(e)}"}
    
    def _get_default_port(self, db_type: DatabaseType) -> int:
        """Get default port for database type."""
        ports = {
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MYSQL: 3306,
            DatabaseType.SQLITE: 0,
            DatabaseType.MONGODB: 27017
        }
        return ports.get(db_type, 0)
    
    async def _remove_connection(self, name: str) -> Dict[str, Any]:
        """Remove database connection."""
        try:
            if name not in self.connections:
                return {"success": False, "error": f"Connection '{name}' not found"}
            
            # Disconnect if manager exists
            if name in self.managers:
                await self.managers[name].disconnect()
                del self.managers[name]
            
            del self.connections[name]
            
            return {
                "success": True,
                "message": f"Connection '{name}' removed successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to remove connection: {str(e)}"}
    
    async def _list_connections(self) -> Dict[str, Any]:
        """List all database connections."""
        try:
            connections_info = []
            
            for name, conn in self.connections.items():
                connections_info.append({
                    "name": name,
                    "type": conn.db_type.value,
                    "host": conn.host,
                    "port": conn.port,
                    "database": conn.database,
                    "username": conn.username,
                    "connected": name in self.managers
                })
            
            return {
                "success": True,
                "connections": connections_info,
                "count": len(connections_info)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list connections: {str(e)}"}
    
    async def _execute_query(self, connection_name: str, query: str, 
                           params: Optional[List] = None) -> Dict[str, Any]:
        """Execute SQL query on specified connection."""
        try:
            if not connection_name or connection_name not in self.managers:
                return {"success": False, "error": f"Connection '{connection_name}' not found"}
            
            if not query:
                return {"success": False, "error": "Query is required"}
            
            manager = self.managers[connection_name]
            
            # Check cache for SELECT queries
            if query.strip().upper().startswith('SELECT'):
                cached_result = self.query_cache.get(query, connection_name)
                if cached_result:
                    return {
                        "success": True,
                        "result": cached_result.to_dict(),
                        "connection": connection_name
                    }
            
            # Execute query
            result = await manager.execute_query(query, params)
            
            # Cache SELECT results
            if result.query_type == QueryType.SELECT and not result.error:
                self.query_cache.set(query, connection_name, result)
            
            return {
                "success": True,
                "result": result.to_dict(),
                "connection": connection_name
            }
            
        except Exception as e:
            return {"success": False, "error": f"Query execution failed: {str(e)}"}
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze SQL query for optimization opportunities."""
        try:
            if not query:
                return {"success": False, "error": "Query is required"}
            
            analysis = self.sql_analyzer.analyze_query(query)
            
            return {
                "success": True,
                "analysis": analysis.to_dict()
            }
            
        except Exception as e:
            return {"success": False, "error": f"Query analysis failed: {str(e)}"}
    
    async def _get_schema(self, connection_name: str, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get database schema information."""
        try:
            if not connection_name or connection_name not in self.managers:
                return {"success": False, "error": f"Connection '{connection_name}' not found"}
            
            manager = self.managers[connection_name]
            
            # MongoDB handles schema differently
            if isinstance(manager, MongoDBManager):
                return {"success": False, "error": "Schema operations not supported for MongoDB"}
            
            schemas = await manager.get_schema(table_name)
            
            return {
                "success": True,
                "schemas": [schema.to_dict() for schema in schemas],
                "connection": connection_name,
                "count": len(schemas)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Schema retrieval failed: {str(e)}"}
    
    async def _test_connection(self, connection_name: str) -> Dict[str, Any]:
        """Test database connection."""
        try:
            if not connection_name or connection_name not in self.connections:
                return {"success": False, "error": f"Connection '{connection_name}' not found"}
            
            connection = self.connections[connection_name]
            
            # Create temporary manager to test
            if connection.db_type == DatabaseType.POSTGRESQL:
                manager = PostgreSQLManager(connection)
            elif connection.db_type == DatabaseType.MYSQL:
                manager = MySQLManager(connection)
            elif connection.db_type == DatabaseType.SQLITE:
                manager = SQLiteManager(connection)
            elif connection.db_type == DatabaseType.MONGODB:
                manager = MongoDBManager(connection)
            else:
                return {"success": False, "error": f"Unsupported database type"}
            
            start_time = datetime.now()
            connected = await manager.connect()
            connection_time = (datetime.now() - start_time).total_seconds()
            
            if connected:
                await manager.disconnect()
                return {
                    "success": True,
                    "message": f"Connection '{connection_name}' is working",
                    "connection_time": connection_time,
                    "database_type": connection.db_type.value
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to connect to '{connection_name}'"
                }
            
        except Exception as e:
            return {"success": False, "error": f"Connection test failed: {str(e)}"}


# Export the tool
__all__ = ['DatabaseIntegrationTool']