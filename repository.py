import redis
import json
from reminder import Reminder
from dataclasses import asdict

class Repository:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def save_reminder(self, reminder: Reminder):
        """Serialize and save a Reminder object in Redis."""
        reminder_key = f"reminder:{reminder.id}"
        reminder_data = json.dumps(asdict(reminder))
        self.client.set(reminder_key, reminder_data)

    def get_reminder(self, reminder_id: str) -> Reminder:
        """Fetch and deserialize a Reminder object from Redis."""
        reminder_key = f"reminder:{reminder_id}"
        reminder_data = self.client.get(reminder_key)
        if reminder_data:
            reminder_dict = json.loads(reminder_data)
            return Reminder(**reminder_dict)
        return None
