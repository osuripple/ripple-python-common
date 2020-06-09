import json

from objects import glob


def notification(userID, message):
	glob.redis.publish("peppy:notification", json.dumps({"userID": userID, "message": message}))
