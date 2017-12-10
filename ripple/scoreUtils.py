from common.constants import mods


def isRankable(m):
	"""
	Checks if `m` contains unranked mods

	:param m: mods enum
	:return: True if there are no unranked mods in `m`, else False
	"""
	# TODO: Check other modes unranked mods ...?
	return not ((m & mods.RELAX > 0) or (m & mods.RELAX2 > 0) or (m & mods.AUTOPLAY > 0) or (m & mods.SCOREV2 > 0))

def readableGameMode(gameMode):
	"""
	Convert numeric gameMode to a readable format. Can be used for db too.

	:param gameMode:
	:return:
	"""
	# TODO: Same as common.constants.gameModes.getGameModeForDB, remove one
	if gameMode == 0:
		return "std"
	elif gameMode == 1:
		return "taiko"
	elif gameMode == 2:
		return "ctb"
	else:
		return "mania"

def readableMods(m):
	"""
	Return a string with readable std mods.
	Used to convert a mods number for oppai

	:param m: mods bitwise number
	:return: readable mods string, eg HDDT
	"""
	r = ""
	if m == 0:
		return "nomod"
	if m & mods.NOFAIL > 0:
		r += "NF"
	if m & mods.EASY > 0:
		r += "EZ"
	if m & mods.HIDDEN > 0:
		r += "HD"
	if m & mods.HARDROCK > 0:
		r += "HR"
	if m & mods.DOUBLETIME > 0:
		r += "DT"
	if m & mods.HALFTIME > 0:
		r += "HT"
	if m & mods.FLASHLIGHT > 0:
		r += "FL"
	if m & mods.SPUNOUT > 0:
		r += "SO"
	if m & mods.TOUCHSCREEN > 0:
		r += "TD"
	return r
