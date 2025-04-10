import redis
import json
from reminder import Reminder
from dataclasses import asdict
from datetime import datetime
import logging

class Repository:

    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        logging.info(f"Connected to Redis at {host}:{port}, DB: {db}")

    def save_reminder(self, reminder: Reminder):
        """Serialize and save a Reminder object in Redis."""
        reminder_key = f"reminder:{reminder.id}"
        reminder_data = json.dumps({
            'id': reminder.id,
            'message': reminder.message,
            'time': reminder.time.isoformat() if reminder.time else '',
            'list': reminder.list,
            'location': reminder.location,
            'completed': reminder.completed
        })
        logging.info(f"Saving reminder with key: {reminder_key} and data: {reminder_data}")
        self.client.set(reminder_key, reminder_data)

    def get_reminder(self, reminder_id: str) -> Reminder:
        """Fetch and deserialize a Reminder object from Redis."""
        reminder_key = f"reminder:{reminder_id}"
        logging.info(f"Fetching reminder with key: {reminder_key}")
        reminder_data = self.client.get(reminder_key)
        if reminder_data:
            reminder_dict = json.loads(reminder_data)
            if reminder_dict['time'] != '':
                reminder_dict['time'] = datetime.fromisoformat(reminder_dict['time'])
            logging.info(f"Reminder found: {reminder_dict}")
            return Reminder(**reminder_dict)
        logging.warning(f"Reminder with key {reminder_key} not found")
        return None

    def get_all_reminders(self):
        """Fetch all reminders from Redis and return them as a list of Reminder objects."""
        logging.info("Fetching all reminders")
        keys = self.client.keys('reminder:*')
        reminders = []
        for key in keys:
            reminder_data = self.client.get(key)
            if reminder_data:
                reminder_dict = json.loads(reminder_data)
                if reminder_dict['time'] != '':
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
