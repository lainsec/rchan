"""
Timeout and Moderation Management Module using LainDB
Handles user timeouts, bans, reports, chan config and word filters.
"""

import threading
import re
from datetime import datetime, timedelta
from database_modules.sqlite_handler import SQLiteConfig


class TimeoutManager:
    def __init__(self):
        # Initialize SQLite for timeout management
        self.db = SQLiteConfig.load_db('moderation')
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
        # Initialize SQLite for ban management
        self.db = SQLiteConfig.load_db('moderation')
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
    
    def _setup_timer(self, ban_id, duration):
        """
        Setup a timer to automatically remove a ban.

        Args:
            ban_id (int): ID of the ban record
            duration (int): Ban duration in seconds
        """
        if ban_id in self.active_timers:
            self.active_timers[ban_id].cancel()

        timer = threading.Timer(duration, self.unban_user_by_id, args=[ban_id])
        timer.daemon = True
        timer.start()
        self.active_timers[ban_id] = timer

    def unban_user_by_id(self, ban_id):
        """
        Remove a ban by its ID.

        Args:
            ban_id (int): ID of the ban record
        """
        with self.lock:
            self.db.delete('bans', ban_id)
            if ban_id in self.active_timers:
                self.active_timers[ban_id].cancel()
                del self.active_timers[ban_id]

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
                    'reason': reason if reason != "" else "No reason.",
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


class ThreadCreationAllowlistManager:
    def __init__(self):
        self.db = SQLiteConfig.load_db('moderation')
        self.db.create_table('thread_creation_allowed_ips', {
            'ip': 'str',
            'expire_at': 'str'
        })

    def _cleanup_expired(self):
        now = datetime.now()
        entries = self.db.find_all('thread_creation_allowed_ips')
        for entry in entries:
            expire_raw = entry.get('expire_at')
            try:
                expire_at = datetime.fromisoformat(expire_raw)
            except Exception:
                self.db.delete('thread_creation_allowed_ips', entry['id'])
                continue
            if now >= expire_at:
                self.db.delete('thread_creation_allowed_ips', entry['id'])

    def is_ip_allowed(self, ip):
        self._cleanup_expired()
        records = self.db.query('thread_creation_allowed_ips', {'ip': {'==': ip}})
        if not records:
            return False
        entry = records[0]
        expire_raw = entry.get('expire_at')
        try:
            expire_at = datetime.fromisoformat(expire_raw)
        except Exception:
            self.db.delete('thread_creation_allowed_ips', entry['id'])
            return False
        now = datetime.now()
        if now >= expire_at:
            self.db.delete('thread_creation_allowed_ips', entry['id'])
            return False
        return True

    def allow_for_hours(self, ip, hours=2):
        expire_at = (datetime.now() + timedelta(hours=hours)).isoformat()
        existing = self.db.query('thread_creation_allowed_ips', {'ip': {'==': ip}})
        if existing:
            entry_id = existing[0]['id']
            self.db.update('thread_creation_allowed_ips', entry_id, {'expire_at': expire_at})
        else:
            entries = self.db.find_all('thread_creation_allowed_ips')
            max_id = max([e.get('id', 0) for e in entries] + [0])
            entry_id = max_id + 1
            self.db.insert('thread_creation_allowed_ips', {
                'id': entry_id,
                'ip': ip,
                'expire_at': expire_at
            })


class ReportManager:
    def __init__(self):
        # Initialize SQLite for report management
        self.db = SQLiteConfig.load_db('moderation')
        self.db.create_table('reports', {
            'id': 'int',
            'motivo': 'str',
            'post_id': 'int',
            'board': 'str',
            'solved': 'int'
        })

    def add_report(self, motivo, post_id, board, solved=False):
        """
        Add a new report.
        
        Args:
            motivo (str): Reason for the report
            post_id (int): ID of the reported post
            board (str): Board URI
            solved (bool): Whether the report is solved
            
        Returns:
            bool: True if report was added successfully
        """
        max_id = max([r['id'] for r in self.db.find_all('reports')] + [0])
        report_id = max_id + 1
        
        self.db.insert('reports', {
            'id': report_id,
            'motivo': motivo,
            'post_id': post_id,
            'board': board,
            'solved': 1 if solved else 0
        })
        return True

    def get_all_reports(self):
        """
        Get all reports.
        
        Returns:
            list: List of all reports
        """
        return self.db.find_all('reports')

    def get_board_reports(self, board_uri):
        """
        Get reports for a specific board.
        
        Args:
            board_uri (str): Board URI
            
        Returns:
            list: List of reports for the board
        """
        return self.db.query('reports', {'board': {'==': board_uri}})

    def get_report(self, report_id):
        """
        Get a report by ID.
        
        Args:
            report_id (int): Report ID
            
        Returns:
            dict: Report data or None
        """
        reports = self.db.query('reports', {'id': {'==': int(report_id)}})
        return reports[0] if reports else None

    def resolve_report(self, report_id):
        """
        Mark a report as solved.
        
        Args:
            report_id (int): Report ID
        """
        self.db.update('reports', report_id, {'solved': 1})

    def resolve_reports_by_post(self, post_id):
        """
        Mark all reports for a specific post as solved.
        
        Args:
            post_id (int): Post ID
        """
        reports = self.db.query('reports', {'post_id': {'==': int(post_id)}, 'solved': {'==': 0}})
        for report in reports:
            self.db.update('reports', report['id'], {'solved': 1})


class ChanConfigManager:
    def __init__(self):
        # Initialize SQLite for chan config
        self.db = SQLiteConfig.load_db('moderation')
        self.db.create_table('chan_config', {
            'id': 'int',
            'free_board_creation': 'int',
            'index_news': 'str',
            'sidebar_enabled': 'int',
            'max_pages_per_board': 'int',
            'default_poster_name': 'str',
            'posts_per_page': 'int'
        })
        try:
            self.db.add_column('chan_config', 'sidebar_enabled', 'int')
        except Exception:
            pass
        try:
            self.db.add_column('chan_config', 'max_pages_per_board', 'int')
        except Exception:
            pass
        try:
            self.db.add_column('chan_config', 'default_poster_name', 'str')
        except Exception:
            pass
        try:
            self.db.add_column('chan_config', 'posts_per_page', 'int')
        except Exception:
            pass
        self._ensure_record()

    def _ensure_record(self):
        """Ensure that the configuration record exists."""
        configs = self.db.find_all('chan_config')
        if not configs:
            self.db.insert('chan_config', {
                'id': 1,
                'free_board_creation': 1,
                'index_news': "No news to display",
                'sidebar_enabled': 0,
                'max_pages_per_board': 0,
                'default_poster_name': "Anonymous",
                'posts_per_page': 6
            })
        else:
            config = configs[0]
            if 'sidebar_enabled' not in config:
                self.db.update('chan_config', config['id'], {'sidebar_enabled': 0})
            if 'max_pages_per_board' not in config:
                self.db.update('chan_config', config['id'], {'max_pages_per_board': 0})
            if 'default_poster_name' not in config:
                self.db.update('chan_config', config['id'], {'default_poster_name': "Anonymous"})
            if 'posts_per_page' not in config:
                self.db.update('chan_config', config['id'], {'posts_per_page': 6})

    def get_config(self):
        """
        Get the chan configuration.
        
        Returns:
            dict: The configuration record
        """
        self._ensure_record()
        return self.db.find_all('chan_config')[0]

    def update_config(self, free_board_creation=None, index_news=None, sidebar_enabled=None,
                      max_pages_per_board=None, default_poster_name=None, posts_per_page=None):
        """
        Update the chan configuration.
        
        Args:
            free_board_creation (bool): Whether to allow free board creation
            index_news (str): News to display on index
            sidebar_enabled (bool): Whether to enable sidebar layout on /
        """
        self._ensure_record()
        config = self.get_config()
        updates = {}
        
        if free_board_creation is not None:
            updates['free_board_creation'] = 1 if free_board_creation else 0
            
        if index_news is not None:
            updates['index_news'] = index_news

        if sidebar_enabled is not None:
            updates['sidebar_enabled'] = 1 if sidebar_enabled else 0

        if max_pages_per_board is not None:
            try:
                value = int(max_pages_per_board)
            except (TypeError, ValueError):
                value = 0
            if value < 0:
                value = 0
            updates['max_pages_per_board'] = value

        if default_poster_name is not None:
            updates['default_poster_name'] = default_poster_name

        if posts_per_page is not None:
            try:
                value = int(posts_per_page)
            except (TypeError, ValueError):
                value = 6
            if value < 1:
                value = 1
            updates['posts_per_page'] = value
            
        if updates:
            self.db.update('chan_config', config['id'], updates)


class WordFilterManager:
    def __init__(self):
        # Initialize SQLite for word filters
        self.db = SQLiteConfig.load_db('moderation')
        self.db.create_table('word_filters', {
            'word': 'str',
            'filter': 'str'
        })

    def get_filters(self):
        return self.db.find_all('word_filters')

    def add_filter(self, word, replacement, mode='word'):
        if not word:
            return False
        existing = self.get_filters()
        new_id = max([f.get('id', 0) for f in existing] + [0]) + 1
        stored_word = word + '*' if mode == 'prefix' else word
        self.db.insert('word_filters', {
            'id': new_id,
            'word': stored_word,
            'filter': replacement or ''
        })
        return True

    def delete_filter(self, filter_id):
        try:
            return self.db.delete('word_filters', int(filter_id))
        except:
            return False

    def apply_filters(self, text):
        if not text:
            return text
        filters = self.get_filters()
        for f in filters:
            word = f.get('word', '')
            replacement = f.get('filter', '')
            if not word:
                continue
            is_prefix = word.endswith('*')
            core = word[:-1] if is_prefix else word
            if not core:
                continue
            if is_prefix:
                pattern = re.compile(rf'{re.escape(core)}\S*', re.IGNORECASE)
            else:
                pattern = re.compile(rf'(?<!\w){re.escape(core)}(?!\w)', re.IGNORECASE)

            def _repl(match):
                original = match.group(0)
                if original.isupper():
                    return replacement.upper()
                if original[0].isupper() and original[1:].islower():
                    return replacement.capitalize()
                return replacement

            text = pattern.sub(_repl, text)
        return text


if __name__ == '__main__':
    print("This module should not be run directly.")
