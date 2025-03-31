import redis
import json
from reminder import Reminder
from dataclasses import asdict

class Repository:

    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def save_reminder(self, reminder: Reminder):
        EXPIRE_TIME = 60 * 60 * 8 #8 hours
        """Serialize and save a Reminder object in Redis."""
        reminder_key = f"reminder:{reminder.id}"
        reminder_data = json.dumps(asdict(reminder))
        self.client.set(reminder_key, reminder_data, ex=EXPIRE_TIME)

    def get_reminder(self, reminder_id: str) -> Reminder:
        """Fetch and deserialize a Reminder object from Redis."""
        reminder_key = f"reminder:{reminder_id}"
        reminder_data = self.client.get(reminder_key)
        if reminder_data:
            reminder_dict = json.loads(reminder_data)
            return Reminder(**reminder_dict)
        return None

    def get_all_reminders(self):
        """Fetch all reminders from Redis and return them as a list of Reminder objects."""
        keys = self.client.keys('reminder:*')
        reminders = []
        for key in keys:
            reminder_data = self.client.get(key)
            if reminder_data:
                reminder_dict = json.loads(reminder_data)
                reminders.append(Reminder(**reminder_dict))
        return reminders
