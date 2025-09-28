# mongodb_database.py - MongoDB operations
import logging
from typing import List, Tuple, Optional, Any, Dict
from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class MongoDBDatabase:
    def __init__(self) -> None:
        self.client: Optional[MongoClient] = None
        self.db: Optional[Any] = None
        self.channels: Optional[Collection] = None
        self.member_counts: Optional[Collection] = None
        self.broadcasts: Optional[Collection] = None
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize MongoDB connection"""
        try:
            mongodb_url = os.getenv('MONGODB_URL', '')
            if not mongodb_url:
                raise ValueError("MONGODB_URL environment variable is not set")
            
            self.client = MongoClient(mongodb_url)
            self.db = self.client['channel_bot_db']
            
            # Create collections
            self.channels = self.db['channels']
            self.member_counts = self.db['member_counts']
            self.broadcasts = self.db['broadcasts']
            
            # Create indexes
            self.channels.create_index('channel_id', unique=True)
            self.member_counts.create_index([('channel_id', 1), ('record_date', -1)])
            
            logger.info("✅ MongoDB initialized successfully")
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            raise
    
    def register_channel(self, channel_id: int, channel_name: Optional[str] = None, 
                        channel_username: Optional[str] = None) -> Tuple[bool, str]:
        """Register channel in database"""
        try:
            existing_channel = self.channels.find_one({'channel_id': str(channel_id)})
            
            if existing_channel:
                self.channels.update_one(
                    {'channel_id': str(channel_id)},
                    {
                        '$set': {
                            'last_activity': datetime.now(),
                            'is_active': True
                        }
                    }
                )
                logger.info(f"📊 Channel activity updated: {channel_id}")
                return False, "Channel already registered. Activity updated!"
            else:
                channel_data: Dict[str, Any] = {
                    'channel_id': str(channel_id),
                    'channel_name': channel_name,
                    'channel_username': channel_username,
                    'registered_date': datetime.now(),
                    'is_active': True,
                    'forward_count': 0,
                    'last_activity': datetime.now(),
                    'current_members': 0
                }
                self.channels.insert_one(channel_data)
                logger.info(f"✅ New channel registered: {channel_id} - {channel_name}")
                return True, "✅ Channel registered successfully!"
                
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return False, f"❌ Registration failed: {str(e)}"
    
    def increment_forward_count(self, channel_id: int) -> None:
        """Increment forward message count"""
        try:
            self.channels.update_one(
                {'channel_id': str(channel_id)},
                {
                    '$inc': {'forward_count': 1},
                    '$set': {'last_activity': datetime.now()}
                }
            )
        except Exception as e:
            logger.error(f"❌ Forward count error: {e}")
    
    def get_registered_channels(self) -> List[Tuple]:
        """Get all registered channels"""
        try:
            channels = list(self.channels.find(
                {'is_active': True}
            ).sort('registered_date', -1))
            
            result: List[Tuple] = []
            for channel in channels:
                result.append((
                    channel['channel_id'],
                    channel.get('channel_name', ''),
                    channel.get('channel_username', ''),
                    channel.get('registered_date', datetime.now()),
                    channel.get('forward_count', 0),
                    channel.get('last_activity', datetime.now()),
                    channel.get('current_members', 0)
                ))
            return result
        except Exception as e:
            logger.error(f"❌ Get channels error: {e}")
            return []
    
    def update_channel_member_count(self, channel_id: int, member_count: int) -> None:
        """Update channel member count and record in history"""
        try:
            self.channels.update_one(
                {'channel_id': str(channel_id)},
                {
                    '$set': {
                        'current_members': member_count,
                        'last_activity': datetime.now()
                    }
                }
            )
            
            member_count_record = {
                'channel_id': str(channel_id),
                'member_count': member_count,
                'record_date': datetime.now()
            }
            self.member_counts.insert_one(member_count_record)
            
            logger.info(f"Member count updated for channel: {channel_id} - {member_count}")
        except Exception as e:
            logger.error(f"Member count update error: {e}")
    
    def get_today_growth(self, channel_id: int) -> str:
        """Calculate today's member growth"""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start.replace(day=today_start.day-1)
            
            today_record = self.member_counts.find_one(
                {
                    'channel_id': str(channel_id),
                    'record_date': {'$gte': today_start}
                },
                sort=[('record_date', -1)]
            )
            
            yesterday_record = self.member_counts.find_one(
                {
                    'channel_id': str(channel_id),
                    'record_date': {'$gte': yesterday_start, '$lt': today_start}
                },
                sort=[('record_date', -1)]
            )
            
            if today_record and yesterday_record:
                growth = today_record['member_count'] - yesterday_record['member_count']
                return f"+{growth}" if growth > 0 else str(growth)
            elif today_record:
                return "New tracking"
            else:
                return "No data"
                
        except Exception as e:
            logger.error(f"Growth calculation error: {e}")
            return "Error"
    
    def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")
