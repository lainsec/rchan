"""
Timeout Management Module using LainDB
Handles user timeouts with thread-safe operations.
"""

import threading
from datetime import datetime, timedelta
from laindb.laindb import Lainconfig


class TimeoutManager:
    def __init__(self):
        # Initialize LainDB for timeout management
        self.db = Lainconfig.load_db('moderation')
        self.db.create_table('timeouts', {
            'user_ip': 'str',
            'user_role': 'str',
            'end_time': 'str',
            'reason': 'str',
            'moderator': 'str',
            'applied_at': 'str'
        })
        
        self.lock = threading.Lock()
        self.active_timers = {}
        
    def apply_timeout(self, user_ip, duration_seconds=35, reason="", moderator="System"):
        """
        Apply a timeout to a user.
        
        Args:
            user_ip (str): User's IP address
            duration_seconds (int): Timeout duration in seconds
            reason (str): Reason for timeout
            moderator (str): Moderator who applied the timeout
            
        Returns:
            bool: True if timeout was applied successfully
        """
        with self.lock:
            end_time = (datetime.now() + timedelta(seconds=duration_seconds)).isoformat()
            applied_at = datetime.now().isoformat()
            
            # Check if user already has a timeout
            existing = self.db.query('timeouts', {'user_ip': {'==': user_ip}})
            
            if existing:
                # Update existing timeout
                timeout_id = existing[0]['id']
                self.db.update('timeouts', timeout_id, {
                    'user_role': 'timeout',
                    'end_time': end_time,
                    'reason': reason,
                    'moderator': moderator,
                    'applied_at': applied_at
                })
            else:
                # Create new timeout record
                max_timeout_id = max([timeout['id'] for timeout in self.db.find_all('timeouts')] + [0])
                timeout_id = max_timeout_id + 1

                self.db.insert('timeouts', {
                    'id': timeout_id,
                    'user_ip': user_ip,
                    'user_role': 'timeout',
                    'end_time': end_time,
                    'reason': reason,
                    'moderator': moderator,
                    'applied_at': applied_at
                })
            
            self._setup_timer(timeout_id, duration_seconds)
            return True
    
    def _setup_timer(self, timeout_id, duration):
        """
        Setup a timer to automatically remove timeout.
        
        Args:
            timeout_id (int): ID of the timeout record
            duration (int): Timeout duration in seconds
        """
        if timeout_id in self.active_timers:
            self.active_timers[timeout_id].cancel()
        
        timer = threading.Timer(duration, self.remove_timeout, args=[timeout_id])
        timer.daemon = True
        timer.start()
        self.active_timers[timeout_id] = timer
    
    def remove_timeout(self, timeout_id):
        """
        Remove a timeout by its ID.
        
        Args:
            timeout_id (int): ID of the timeout record
        """
        with self.lock:
            self.db.delete('timeouts', timeout_id)
            
            if timeout_id in self.active_timers:
                timer = self.active_timers.pop(timeout_id)
                timer.cancel()
    
    def check_timeout(self, user_ip):
        """
        Check if a user is currently timed out.
        
        Args:
            user_ip (str): User's IP address
            
        Returns:
            dict: Timeout information if active, else {'is_timeout': False}
        """
        timeouts = self.db.query('timeouts', {'user_ip': {'==': user_ip}})
        
        if not timeouts:
            return {'is_timeout': False}
            
        timeout = timeouts[0]
        end_time = datetime.fromisoformat(timeout['end_time'])
        
        if datetime.now() < end_time:
            return {
                'is_timeout': True,
                'end_time': end_time,
                'reason': timeout.get('reason', ''),
                'moderator': timeout.get('moderator', 'System'),
                'timeout_id': timeout['id']
            }
        else:
            self.remove_timeout(timeout['id'])
            return {'is_timeout': False}
    
    def get_active_timeouts(self):
        """
        Get all currently active timeouts.
        
        Returns:
            dict: Dictionary of active timeouts keyed by user IP
        """
        active = {}
        now = datetime.now()
        
        # Query all timeouts where end_time is in the future
        timeouts = self.db.query('timeouts', {
            'user_role': {'==': 'timeout'}
        })
        
        for timeout in timeouts:
            end_time = datetime.fromisoformat(timeout['end_time'])
            
            if now < end_time:
                active[timeout['user_ip']] = {
                    'end_time': end_time,
                    'reason': timeout.get('reason', ''),
                    'moderator': timeout.get('moderator', 'System'),
                    'applied_at': datetime.fromisoformat(timeout['applied_at']),
                    'timeout_id': timeout['id']
                }
            else:
                self.remove_timeout(timeout['id'])
        
        return active
    
    def cleanup_expired(self):
        """
        Cleanup all expired timeouts.
        """
        now = datetime.now()
        timeouts = self.db.find_all('timeouts')
        
        for timeout in timeouts:
            end_time = datetime.fromisoformat(timeout['end_time'])
            if now >= end_time:
                self.remove_timeout(timeout['id'])


class BanManager:
    def __init__(self):
        # Initialize LainDB for ban management
        self.db = Lainconfig.load_db('moderation')
        self.db.create_table('bans', {
            'user_ip': 'str',
            'end_time': 'str',
            'reason': 'str',
            'moderator': 'str',
            'applied_at': 'str',
            'boards': 'list',
            'is_permanent': 'bool'
        })
        
        self.lock = threading.Lock()
        self.active_timers = {}

    def ban_user(self, user_ip, duration_seconds=None, boards=None, reason="", moderator="System"):
        """
        Ban a user by IP address.

        Args:
            user_ip (str): User's IP address
            duration_seconds (int): Optional ban duration in seconds (None for permanent)
            boards (list): List of boards where the user is banned
            reason (str): Reason for ban
            moderator (str): Moderator who applied the ban

        Returns:
            bool: True if ban was applied successfully
        """
        if boards is None:
            boards = []  # default to empty list (ban all boards if logic applies)
        
        with self.lock:
            applied_at = datetime.now().isoformat()
            is_permanent = duration_seconds is None
            end_time = "permanent" if is_permanent else (datetime.now() + timedelta(seconds=duration_seconds)).isoformat()
            
            existing = self.db.query('bans', {'user_ip': {'==': user_ip}})
            
            if existing:
                ban_id = existing[0]['id']
                self.db.update('bans', ban_id, {
                    'end_time': end_time,
                    'reason': reason,
                    'moderator': moderator,
                    'applied_at': applied_at,
                    'boards': boards,
                    'is_permanent': is_permanent
                })
                if ban_id in self.active_timers:
                    self.active_timers[ban_id].cancel()
            else:
                max_id = max([ban['id'] for ban in self.db.find_all('bans')] + [0])
                ban_id = max_id + 1
                self.db.insert('bans', {
                    'id': ban_id,
                    'user_ip': user_ip,
                    'end_time': end_time,
                    'reason': reason,
                    'moderator': moderator,
                    'applied_at': applied_at,
                    'boards': boards,
                    'is_permanent': is_permanent
                })
            
            if not is_permanent:
                self._setup_timer(ban_id, duration_seconds)

            return True

    def is_banned(self, user_ip):
        """
        Check if a user is currently banned.

        Args:
            user_ip (str): User's IP address

        Returns:
            dict: Ban information if active, else {'is_banned': False}
        """
        bans = self.db.query('bans', {'user_ip': {'==': user_ip}})
        
        if not bans:
            return {'is_banned': False}
        
        ban = bans[0]
        
        if ban['is_permanent']:
            return {
                'is_banned': True,
                'is_permanent': True,
                'boards': ban.get('boards', []),
                'reason': ban.get('reason', ''),
                'moderator': ban.get('moderator', 'System'),
                'applied_at': datetime.fromisoformat(ban['applied_at']),
                'ban_id': ban['id']
            }
        else:
            end_time = datetime.fromisoformat(ban['end_time'])
            if datetime.now() < end_time:
                return {
                    'is_banned': True,
                    'is_permanent': False,
                    'end_time': end_time,
                    'boards': ban.get('boards', []),
                    'reason': ban.get('reason', ''),
                    'moderator': ban.get('moderator', 'System'),
                    'applied_at': datetime.fromisoformat(ban['applied_at']),
                    'ban_id': ban['id']
                }
            else:
                self.unban_user_by_id(ban['id'])
                return {'is_banned': False}

    def get_active_bans(self):
        """
        Get all currently active bans.

        Returns:
            dict: Dictionary of active bans keyed by user IP
        """
        active = {}
        now = datetime.now()
        
        for ban in self.db.find_all('bans'):
            if ban['is_permanent']:
                active[ban['user_ip']] = {
                    'is_permanent': True,
                    'boards': ban.get('boards', []),
                    'reason': ban.get('reason', ''),
                    'moderator': ban.get('moderator', 'System'),
                    'applied_at': datetime.fromisoformat(ban['applied_at']),
                    'ban_id': ban['id']
                }
            else:
                end_time = datetime.fromisoformat(ban['end_time'])
                if now < end_time:
                    active[ban['user_ip']] = {
                        'is_permanent': False,
                        'end_time': end_time,
                        'boards': ban.get('boards', []),
                        'reason': ban.get('reason', ''),
                        'moderator': ban.get('moderator', 'System'),
                        'applied_at': datetime.fromisoformat(ban['applied_at']),
                        'ban_id': ban['id']
                    }
                else:
                    self.unban_user_by_id(ban['id'])
        
        return active
    
    def cleanup_expired(self):
        """
        Cleanup all expired temporary bans.
        """
        now = datetime.now()
        
        for ban in self.db.find_all('bans'):
            if not ban['is_permanent']:
                end_time = datetime.fromisoformat(ban['end_time'])
                
                if now >= end_time:
                    self.unban_user_by_id(ban['id'])

if __name__ == '__main__':
    print("This module should not be run directly.")
