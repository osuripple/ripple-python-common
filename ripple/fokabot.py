import requests

from objects import glob


def _request(handler, json, timeout=3):
	return requests.post(
		"{}/{}".format(glob.conf["FOKABOT_API_BASE"].rstrip("/"), handler.lstrip("/")),
		headers={"Secret": glob.conf["FOKABOT_API_SECRET"]},
		json=json,
		timeout=timeout
	)


def message(message, target):
	return _request("/api/v0/send_message", {"message": message, "target": target})


def last(userID):
	return _request("/api/v0/last", {"user_id": userID})
