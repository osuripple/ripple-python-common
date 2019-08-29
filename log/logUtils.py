import logging

import time
import os

ENDL = "\n" if os.name == "posix" else "\r\n"


def discord(channel, message, level=None):
	import objects.glob

	if channel == "bunker":
		objects.glob.schiavo.sendConfidential(message)
	elif channel == "cm":
		objects.glob.schiavo.sendCM(message)
	elif channel == "staff":
		objects.glob.schiavo.sendStaff(message)
	elif channel == "general":
		objects.glob.schiavo.sendGeneral(message)
	else:
		raise ValueError("Unsupported channel ({})".format(channel))

	# Log with stdlib logging
	if level is not None:
		LEVELS_MAPPING.get(level.lower(), info)(message)


def cm(message):
	"""
	CM logging (to discord and with logging)

	:param message: the message to log
	:return:
	"""
	return discord("cm", message, level="warning")


def warning(message):
	logging.warning(message)


def error(message):
	logging.error(message)


def info(message):
	logging.info(message)


def debug(message):
	logging.debug(message)


def rap(userID, message, discordChannel=None, through="FokaBot"):
	"""
	Log a message to Admin Logs.

	:param userID: admin user ID
	:param message: message content, without username
	:param discordChannel: discord channel to send this message to or None to disable discord logging
	:param through: through string. Default: FokaBot
	:return:
	"""
	import common.ripple
	import objects.glob
	objects.glob.db.execute("INSERT INTO rap_logs (id, userid, text, datetime, through) VALUES (NULL, %s, %s, %s, %s)", [userID, message, int(time.time()), through])
	username = common.ripple.userUtils.getUsername(userID)
	if discordChannel is not None:
		discord(discordChannel, "{} {}".format(username, message))

LEVELS_MAPPING = {
	"warning": warning,
	"info": info,
	"error": error
}