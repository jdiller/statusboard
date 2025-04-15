import redis
import json
from reminder import Reminder
from datetime import datetime
import logging

# Default TTL for reminders (8 hours in seconds)
DEFAULT_REMINDER_TTL = 60 * 60 * 8

class Repository:

    def __init__(self, config):
        self.host = config.get('redis', 'host', fallback='redis')
        self.port = config.getint('redis', 'port', fallback=6379)
        self.client = redis.StrictRedis(host=self.host, port=self.port, decode_responses=True)
        self.reminder_ttl = config.get('redis', 'reminder_ttl', fallback=DEFAULT_REMINDER_TTL)
        logging.info(f"Connected to Redis at {self.host}:{self.port}")

    def save_reminder(self, reminder: Reminder):
        """Serialize and save a Reminder object in Redis."""
        reminder_key = f"reminder:{reminder.id}"
        reminder_data = json.dumps({
            'id': reminder.id,
            'message': reminder.message,
            'time': reminder.time.isoformat() if reminder.time else None,
            'list': reminder.list,
            'location': reminder.location,
            'completed': reminder.completed
        })
        logging.info(f"Saving reminder with key: {reminder_key} and data: {reminder_data}")
        self.client.set(reminder_key, reminder_data, ex=self.reminder_ttl)

    def get_reminder(self, reminder_id: str) -> Reminder:
        """Fetch and deserialize a Reminder object from Redis."""
        reminder_key = f"reminder:{reminder_id}"
        logging.info(f"Fetching reminder with key: {reminder_key}")
        reminder_data = self.client.get(reminder_key)
        if reminder_data:
            reminder_dict = json.loads(reminder_data)
            if reminder_dict['time'] and not isinstance(reminder_dict['time'], datetime):
                reminder_dict['time'] = datetime.fromisoformat(reminder_dict['time'])
            logging.info(f"Reminder found: {reminder_dict}")
            return Reminder(**reminder_dict)
        logging.warning(f"Reminder with key {reminder_key} not found")
        return None

    def get_all_reminders(self) -> list[Reminder]:
        """Fetch all reminders from Redis and return them as a list of Reminder objects."""
        logging.info("Fetching all reminders")
        keys = self.client.keys('reminder:*')
        reminders = []
        for key in keys:
            reminder_data = self.client.get(key)
            if reminder_data:
                reminder_dict = json.loads(reminder_data)
                if reminder_dict['time'] and not isinstance(reminder_dict['time'], datetime):
                    reminder_dict['time'] = datetime.fromisoformat(reminder_dict['time'])
                reminders.append(Reminder(**reminder_dict))
        logging.info(f"Total reminders fetched: {len(reminders)}")
        return reminders

    def delete_all_reminders(self):
        """Delete all reminders from Redis."""
        logging.info("Deleting all reminders")
        keys = self.client.keys('reminder:*')
        for key in keys:
            self.client.delete(key)
        logging.info(f"Deleted {len(keys)} reminders")
