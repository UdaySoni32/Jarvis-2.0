"""
JARVIS 2.0 Learning Data Storage

Secure, privacy-focused storage system for user learning data, preferences,
behavior patterns, and analytics. Supports multiple storage backends with
data encryption, retention policies, and GDPR compliance features.
"""

import asyncio
import json
import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import os
import aiosqlite
from cryptography.fernet import Fernet
import uuid

from .schemas import (
    UserProfile, UserPreferences, BehaviorPattern, CommandUsage,
    UsageSession, LearningData, PrivacySettings, PersonalizationSettings
)

logger = logging.getLogger(__name__)


class DataEncryption:
    """Handles data encryption and decryption for sensitive information"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        if encryption_key:
            self.fernet = Fernet(encryption_key)
        else:
            # Generate new key if none provided
            key = Fernet.generate_key()
            self.fernet = Fernet(key)
            logger.warning("Generated new encryption key. Store securely for data recovery!")
    
    def encrypt_data(self, data: Union[str, dict]) -> bytes:
        """Encrypt data for storage"""
        if isinstance(data, dict):
            data = json.dumps(data)
        elif not isinstance(data, str):
            data = str(data)
        
        return self.fernet.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt data from storage"""
        return self.fernet.decrypt(encrypted_data).decode()
    
    def get_key(self) -> bytes:
        """Get encryption key for backup/recovery"""
        # In production, this should be handled more securely
        return self.fernet._signing_key + self.fernet._encryption_key


class DataRetentionManager:
    """Manages data retention policies and cleanup"""
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
        self.retention_policies = {
            'command_usage': timedelta(days=90),
            'usage_sessions': timedelta(days=90),
            'behavior_patterns': timedelta(days=365),
            'user_preferences': None,  # Keep indefinitely
            'learning_data': timedelta(days=180)
        }
    
    async def cleanup_expired_data(self, user_id: Optional[str] = None):
        """Remove data that has exceeded retention policy"""
        try:
            current_time = datetime.utcnow()
            
            for data_type, retention_period in self.retention_policies.items():
                if retention_period is None:
                    continue  # Keep indefinitely
                
                cutoff_date = current_time - retention_period
                
                if data_type == 'command_usage':
                    await self.storage.delete_command_usage_before(cutoff_date, user_id)
                elif data_type == 'usage_sessions':
                    await self.storage.delete_usage_sessions_before(cutoff_date, user_id)
                elif data_type == 'behavior_patterns':
                    await self.storage.delete_behavior_patterns_before(cutoff_date, user_id)
                elif data_type == 'learning_data':
                    await self.storage.delete_learning_data_before(cutoff_date, user_id)
            
            logger.info(f"Completed data cleanup for {'all users' if not user_id else user_id}")
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
    
    def set_retention_policy(self, data_type: str, days: Optional[int]):
        """Update retention policy for a data type"""
        if days is None:
            self.retention_policies[data_type] = None
        else:
            self.retention_policies[data_type] = timedelta(days=days)
        
        logger.info(f"Updated retention policy for {data_type}: {days} days")


class SQLiteStorageBackend:
    """SQLite-based storage backend with encryption support"""
    
    def __init__(self, db_path: str, encryption_key: Optional[bytes] = None):
        self.db_path = db_path
        self.encryption = DataEncryption(encryption_key) if encryption_key else None
        
        # Create database directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            await db.commit()
        
        logger.info(f"SQLite storage initialized: {self.db_path}")
    
    async def _create_tables(self, db: aiosqlite.Connection):
        """Create database tables"""
        
        # User profiles table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                email TEXT,
                profile_data TEXT,  -- JSON data, optionally encrypted
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                total_sessions INTEGER DEFAULT 0,
                total_commands INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                version TEXT DEFAULT '1.0.0'
            )
        ''')
        
        # User preferences table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                preferences_data TEXT,  -- JSON data, optionally encrypted
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version TEXT DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        # Command usage table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS command_usage (
                command_id TEXT PRIMARY KEY,
                user_id TEXT,
                session_id TEXT,
                command TEXT,
                category TEXT,
                arguments TEXT,  -- JSON
                success BOOLEAN,
                execution_time_ms REAL,
                error_message TEXT,
                context TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_feedback TEXT,
                user_rating INTEGER,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        # Usage sessions table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usage_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                total_commands INTEGER DEFAULT 0,
                successful_commands INTEGER DEFAULT 0,
                failed_commands INTEGER DEFAULT 0,
                total_execution_time_ms REAL DEFAULT 0,
                primary_context TEXT,
                contexts_used TEXT,  -- JSON array
                user_agent TEXT,
                ip_address TEXT,
                location TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        # Behavior patterns table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS behavior_patterns (
                pattern_id TEXT PRIMARY KEY,
                user_id TEXT,
                pattern_type TEXT,
                pattern_name TEXT,
                description TEXT,
                confidence_score REAL,
                strength REAL,
                pattern_data TEXT,  -- JSON
                examples TEXT,  -- JSON array
                first_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                observation_count INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        # Learning data table (aggregated analytics)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS learning_data (
                user_id TEXT,
                data_period_start TIMESTAMP,
                data_period_end TIMESTAMP,
                learning_data TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, data_period_start),
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        # Create indexes for performance
        await db.execute('CREATE INDEX IF NOT EXISTS idx_command_usage_user_time ON command_usage (user_id, timestamp)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_command_usage_session ON command_usage (session_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_usage_sessions_user_time ON usage_sessions (user_id, start_time)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_behavior_patterns_user_active ON behavior_patterns (user_id, is_active)')
    
    def _serialize_data(self, data: Any, encrypt: bool = False) -> str:
        """Serialize data to JSON string, optionally encrypted"""
        json_str = json.dumps(data, default=str)
        
        if encrypt and self.encryption:
            encrypted_data = self.encryption.encrypt_data(json_str)
            # Store as base64 for SQLite compatibility
            import base64
            return base64.b64encode(encrypted_data).decode()
        
        return json_str
    
    def _deserialize_data(self, data_str: str, encrypted: bool = False) -> Any:
        """Deserialize data from JSON string, handling encryption"""
        if encrypted and self.encryption:
            import base64
            encrypted_data = base64.b64decode(data_str.encode())
            json_str = self.encryption.decrypt_data(encrypted_data)
        else:
            json_str = data_str
        
        return json.loads(json_str)
    
    async def store_user_profile(self, profile: UserProfile):
        """Store user profile"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if profile should be encrypted based on privacy settings
            encrypt_data = profile.preferences.privacy_settings.anonymize_data
            
            profile_data = self._serialize_data(profile.dict(), encrypt=encrypt_data)
            
            await db.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_id, username, email, profile_data, updated_at, last_active, 
                 total_sessions, total_commands, status, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile.user_id, profile.username, profile.email, profile_data,
                profile.preferences.updated_at, profile.last_active,
                profile.total_sessions, profile.total_commands,
                profile.status.value, profile.version
            ))
            await db.commit()
    
    async def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT profile_data FROM user_profiles WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    try:
                        # Try to deserialize as encrypted data first
                        try:
                            profile_dict = self._deserialize_data(row[0], encrypted=True)
                        except:
                            # Fall back to unencrypted if decryption fails
                            profile_dict = self._deserialize_data(row[0], encrypted=False)
                        
                        return UserProfile(**profile_dict)
                    except Exception as e:
                        logger.error(f"Error deserializing user profile: {e}")
                        return None
                
                return None
    
    async def store_user_preferences(self, preferences: UserPreferences):
        """Store user preferences"""
        async with aiosqlite.connect(self.db_path) as db:
            encrypt_data = preferences.privacy_settings.anonymize_data
            preferences_data = self._serialize_data(preferences.dict(), encrypt=encrypt_data)
            
            await db.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (user_id, preferences_data, updated_at, version)
                VALUES (?, ?, ?, ?)
            ''', (preferences.user_id, preferences_data, preferences.updated_at, preferences.version))
            await db.commit()
    
    async def load_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Load user preferences"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT preferences_data FROM user_preferences WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    try:
                        # Try encrypted first, fall back to unencrypted
                        try:
                            prefs_dict = self._deserialize_data(row[0], encrypted=True)
                        except:
                            prefs_dict = self._deserialize_data(row[0], encrypted=False)
                        
                        return UserPreferences(**prefs_dict)
                    except Exception as e:
                        logger.error(f"Error deserializing user preferences: {e}")
                        return None
                
                return None
    
    async def store_command_usage(self, command_usage: CommandUsage):
        """Store command usage record"""
        async with aiosqlite.connect(self.db_path) as db:
            arguments_json = json.dumps(command_usage.arguments)
            
            await db.execute('''
                INSERT OR REPLACE INTO command_usage 
                (command_id, user_id, session_id, command, category, arguments,
                 success, execution_time_ms, error_message, context, timestamp,
                 user_feedback, user_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                command_usage.command_id, command_usage.user_id, command_usage.session_id,
                command_usage.command, command_usage.category.value, arguments_json,
                command_usage.success, command_usage.execution_time_ms,
                command_usage.error_message, command_usage.context.value,
                command_usage.timestamp, command_usage.user_feedback, command_usage.user_rating
            ))
            await db.commit()
    
    async def get_user_command_history(self, user_id: str, limit: int = 100, 
                                     days: int = 30) -> List[CommandUsage]:
        """Get user command history"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT * FROM command_usage 
                WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, cutoff_date, limit)) as cursor:
                rows = await cursor.fetchall()
                
                commands = []
                for row in rows:
                    try:
                        commands.append(CommandUsage(
                            command_id=row[0],
                            user_id=row[1],
                            session_id=row[2],
                            command=row[3],
                            category=row[4],
                            arguments=json.loads(row[5]) if row[5] else {},
                            success=bool(row[6]),
                            execution_time_ms=row[7],
                            error_message=row[8],
                            context=row[9],
                            timestamp=datetime.fromisoformat(row[10]) if isinstance(row[10], str) else row[10],
                            user_feedback=row[11],
                            user_rating=row[12]
                        ))
                    except Exception as e:
                        logger.error(f"Error deserializing command usage: {e}")
                        continue
                
                return commands
    
    async def store_usage_session(self, session: UsageSession):
        """Store usage session"""
        async with aiosqlite.connect(self.db_path) as db:
            contexts_json = json.dumps([ctx.value for ctx in session.contexts_used])
            
            await db.execute('''
                INSERT OR REPLACE INTO usage_sessions 
                (session_id, user_id, start_time, end_time, total_commands,
                 successful_commands, failed_commands, total_execution_time_ms,
                 primary_context, contexts_used, user_agent, ip_address, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id, session.user_id, session.start_time, session.end_time,
                session.total_commands, session.successful_commands, session.failed_commands,
                session.total_execution_time_ms, session.primary_context.value,
                contexts_json, session.user_agent, session.ip_address, session.location
            ))
            await db.commit()
    
    async def update_usage_session(self, session: UsageSession):
        """Update existing usage session"""
        await self.store_usage_session(session)  # Same as store for SQLite
    
    async def get_user_sessions(self, user_id: str, days: int = 30) -> List[UsageSession]:
        """Get user sessions"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT * FROM usage_sessions 
                WHERE user_id = ? AND start_time >= ?
                ORDER BY start_time DESC
            ''', (user_id, cutoff_date)) as cursor:
                rows = await cursor.fetchall()
                
                sessions = []
                for row in rows:
                    try:
                        from .schemas import UsageContext
                        contexts_used = [UsageContext(ctx) for ctx in json.loads(row[9])]
                        
                        sessions.append(UsageSession(
                            session_id=row[0],
                            user_id=row[1],
                            start_time=datetime.fromisoformat(row[2]) if isinstance(row[2], str) else row[2],
                            end_time=datetime.fromisoformat(row[3]) if row[3] and isinstance(row[3], str) else row[3],
                            total_commands=row[4],
                            successful_commands=row[5],
                            failed_commands=row[6],
                            total_execution_time_ms=row[7],
                            primary_context=UsageContext(row[8]),
                            contexts_used=contexts_used,
                            user_agent=row[10],
                            ip_address=row[11],
                            location=row[12]
                        ))
                    except Exception as e:
                        logger.error(f"Error deserializing usage session: {e}")
                        continue
                
                return sessions
    
    async def store_behavior_pattern(self, pattern: BehaviorPattern):
        """Store behavior pattern"""
        async with aiosqlite.connect(self.db_path) as db:
            pattern_data_json = json.dumps(pattern.pattern_data)
            examples_json = json.dumps(pattern.examples)
            
            await db.execute('''
                INSERT OR REPLACE INTO behavior_patterns 
                (pattern_id, user_id, pattern_type, pattern_name, description,
                 confidence_score, strength, pattern_data, examples,
                 first_observed, last_observed, observation_count, is_active, last_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id, pattern.user_id, pattern.pattern_type.value,
                pattern.pattern_name, pattern.description, pattern.confidence_score,
                pattern.strength, pattern_data_json, examples_json,
                pattern.first_observed, pattern.last_observed, pattern.observation_count,
                pattern.is_active, pattern.last_verified
            ))
            await db.commit()
    
    async def get_user_behavior_patterns(self, user_id: str, 
                                       active_only: bool = True) -> List[BehaviorPattern]:
        """Get user behavior patterns"""
        async with aiosqlite.connect(self.db_path) as db:
            query = 'SELECT * FROM behavior_patterns WHERE user_id = ?'
            params = [user_id]
            
            if active_only:
                query += ' AND is_active = 1'
            
            query += ' ORDER BY confidence_score DESC, strength DESC'
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                patterns = []
                for row in rows:
                    try:
                        from .schemas import BehaviorPatternType
                        
                        patterns.append(BehaviorPattern(
                            pattern_id=row[0],
                            user_id=row[1],
                            pattern_type=BehaviorPatternType(row[2]),
                            pattern_name=row[3],
                            description=row[4],
                            confidence_score=row[5],
                            strength=row[6],
                            pattern_data=json.loads(row[7]),
                            examples=json.loads(row[8]),
                            first_observed=datetime.fromisoformat(row[9]) if isinstance(row[9], str) else row[9],
                            last_observed=datetime.fromisoformat(row[10]) if isinstance(row[10], str) else row[10],
                            observation_count=row[11],
                            is_active=bool(row[12]),
                            last_verified=datetime.fromisoformat(row[13]) if isinstance(row[13], str) else row[13]
                        ))
                    except Exception as e:
                        logger.error(f"Error deserializing behavior pattern: {e}")
                        continue
                
                return patterns
    
    async def update_command_feedback(self, command_id: str, feedback: str, rating: Optional[int]):
        """Update command feedback"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE command_usage 
                SET user_feedback = ?, user_rating = ?
                WHERE command_id = ?
            ''', (feedback, rating, command_id))
            await db.commit()
    
    async def update_pattern_validation(self, pattern_id: str, is_valid: bool):
        """Update pattern validation status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE behavior_patterns 
                SET is_active = ?, last_verified = ?
                WHERE pattern_id = ?
            ''', (is_valid, datetime.utcnow(), pattern_id))
            await db.commit()
    
    # Data cleanup methods
    async def delete_command_usage_before(self, cutoff_date: datetime, user_id: Optional[str] = None):
        """Delete command usage records before cutoff date"""
        async with aiosqlite.connect(self.db_path) as db:
            if user_id:
                await db.execute(
                    'DELETE FROM command_usage WHERE timestamp < ? AND user_id = ?',
                    (cutoff_date, user_id)
                )
            else:
                await db.execute('DELETE FROM command_usage WHERE timestamp < ?', (cutoff_date,))
            await db.commit()
    
    async def delete_usage_sessions_before(self, cutoff_date: datetime, user_id: Optional[str] = None):
        """Delete usage sessions before cutoff date"""
        async with aiosqlite.connect(self.db_path) as db:
            if user_id:
                await db.execute(
                    'DELETE FROM usage_sessions WHERE start_time < ? AND user_id = ?',
                    (cutoff_date, user_id)
                )
            else:
                await db.execute('DELETE FROM usage_sessions WHERE start_time < ?', (cutoff_date,))
            await db.commit()
    
    async def delete_behavior_patterns_before(self, cutoff_date: datetime, user_id: Optional[str] = None):
        """Delete behavior patterns before cutoff date"""
        async with aiosqlite.connect(self.db_path) as db:
            if user_id:
                await db.execute(
                    'DELETE FROM behavior_patterns WHERE first_observed < ? AND user_id = ?',
                    (cutoff_date, user_id)
                )
            else:
                await db.execute('DELETE FROM behavior_patterns WHERE first_observed < ?', (cutoff_date,))
            await db.commit()
    
    async def delete_learning_data_before(self, cutoff_date: datetime, user_id: Optional[str] = None):
        """Delete learning data before cutoff date"""
        async with aiosqlite.connect(self.db_path) as db:
            if user_id:
                await db.execute(
                    'DELETE FROM learning_data WHERE data_period_start < ? AND user_id = ?',
                    (cutoff_date, user_id)
                )
            else:
                await db.execute('DELETE FROM learning_data WHERE data_period_start < ?', (cutoff_date,))
            await db.commit()
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Count records in each table
            tables = [
                'user_profiles', 'user_preferences', 'command_usage',
                'usage_sessions', 'behavior_patterns', 'learning_data'
            ]
            
            for table in tables:
                async with db.execute(f'SELECT COUNT(*) FROM {table}') as cursor:
                    count = await cursor.fetchone()
                    stats[f'{table}_count'] = count[0] if count else 0
            
            # Database file size
            try:
                file_size = os.path.getsize(self.db_path)
                stats['database_size_bytes'] = file_size
                stats['database_size_mb'] = round(file_size / (1024 * 1024), 2)
            except:
                stats['database_size_bytes'] = 0
                stats['database_size_mb'] = 0
            
            return stats


class LearningStorage:
    """Main learning storage interface"""
    
    def __init__(self, storage_type: str = "sqlite", **kwargs):
        self.storage_type = storage_type
        
        if storage_type == "sqlite":
            db_path = kwargs.get('db_path', 'user_data/learning.db')
            encryption_key = kwargs.get('encryption_key')
            self.backend = SQLiteStorageBackend(db_path, encryption_key)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
        
        # Data retention manager
        self.retention_manager = DataRetentionManager(self.backend)
        
        # Configuration
        self.auto_cleanup_enabled = kwargs.get('auto_cleanup', True)
        self.cleanup_interval = timedelta(days=1)
        self.last_cleanup = datetime.utcnow()
        
        logger.info(f"LearningStorage initialized with {storage_type} backend")
    
    async def initialize(self):
        """Initialize storage backend"""
        await self.backend.initialize()
        
        # Schedule initial cleanup if enabled
        if self.auto_cleanup_enabled:
            await self.cleanup_expired_data()
    
    # Delegate all methods to backend
    async def store_user_profile(self, profile: UserProfile):
        await self.backend.store_user_profile(profile)
        await self._check_cleanup()
    
    async def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        return await self.backend.load_user_profile(user_id)
    
    async def store_user_preferences(self, preferences: UserPreferences):
        await self.backend.store_user_preferences(preferences)
    
    async def load_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        return await self.backend.load_user_preferences(user_id)
    
    async def store_command_usage(self, command_usage: CommandUsage):
        await self.backend.store_command_usage(command_usage)
        await self._check_cleanup()
    
    async def get_user_command_history(self, user_id: str, limit: int = 100, 
                                     days: int = 30) -> List[CommandUsage]:
        return await self.backend.get_user_command_history(user_id, limit, days)
    
    async def store_usage_session(self, session: UsageSession):
        await self.backend.store_usage_session(session)
    
    async def update_usage_session(self, session: UsageSession):
        await self.backend.update_usage_session(session)
    
    async def get_user_sessions(self, user_id: str, days: int = 30) -> List[UsageSession]:
        return await self.backend.get_user_sessions(user_id, days)
    
    async def store_behavior_pattern(self, pattern: BehaviorPattern):
        await self.backend.store_behavior_pattern(pattern)
    
    async def get_user_behavior_patterns(self, user_id: str, 
                                       active_only: bool = True) -> List[BehaviorPattern]:
        return await self.backend.get_user_behavior_patterns(user_id, active_only)
    
    async def update_command_feedback(self, command_id: str, feedback: str, rating: Optional[int]):
        await self.backend.update_command_feedback(command_id, feedback, rating)
    
    async def update_pattern_validation(self, pattern_id: str, is_valid: bool):
        await self.backend.update_pattern_validation(pattern_id, is_valid)
    
    async def cleanup_expired_data(self, user_id: Optional[str] = None):
        """Clean up expired data according to retention policies"""
        await self.retention_manager.cleanup_expired_data(user_id)
        self.last_cleanup = datetime.utcnow()
    
    async def _check_cleanup(self):
        """Check if cleanup should be performed"""
        if (self.auto_cleanup_enabled and 
            datetime.utcnow() - self.last_cleanup > self.cleanup_interval):
            await self.cleanup_expired_data()
    
    def set_retention_policy(self, data_type: str, days: Optional[int]):
        """Set retention policy for data type"""
        self.retention_manager.set_retention_policy(data_type, days)
    
    def enable_auto_cleanup(self):
        """Enable automatic data cleanup"""
        self.auto_cleanup_enabled = True
        logger.info("Auto cleanup enabled")
    
    def disable_auto_cleanup(self):
        """Disable automatic data cleanup"""
        self.auto_cleanup_enabled = False
        logger.info("Auto cleanup disabled")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        backend_stats = await self.backend.get_storage_stats()
        
        return {
            "storage_type": self.storage_type,
            "auto_cleanup_enabled": self.auto_cleanup_enabled,
            "last_cleanup": self.last_cleanup.isoformat(),
            "retention_policies": {
                k: v.days if v else None 
                for k, v in self.retention_manager.retention_policies.items()
            },
            **backend_stats
        }


# Export main class
__all__ = ["LearningStorage", "SQLiteStorageBackend", "DataEncryption", "DataRetentionManager"]