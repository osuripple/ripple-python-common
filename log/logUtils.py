import logging

from objects import glob
import time
import os

ENDL = "\n" if os.name == "posix" else "\r\n"


def discord(channel, message, alertDev=False):
	if channel == "bunker":
		glob.schiavo.sendConfidential(message, alertDev)
	elif channel == "cm":
		glob.schiavo.sendCM(message)
	elif channel == "staff":
		glob.schiavo.sendStaff(message)
	elif channel == "general":
		glob.schiavo.sendGeneral(message)
	else:
		raise ValueError("Unsupported channel ({})".format(channel))


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
	glob.db.execute("INSERT INTO rap_logs (id, userid, text, datetime, through) VALUES (NULL, %s, %s, %s, %s)", [userID, message, int(time.time()), through])
	username = common.ripple.userUtils.getUsername(userID)
	if discordChannel is not None:
		discord(discordChannel, "{} {}".format(username, message))
