import requests
import json

from constants import exceptions
from objects import glob
from common.log import logUtils as log
from objects import glob

def cheesegullRequest(handler, requestType="GET", key="", params=None, mustHave=None, wants=None):
	"""
	Send a request to Cheesegull

	:param handler: name of the api handler (eg: `search` for `http://chesegu.ll/api/search`)
	:param requestType: `GET` or `POST`. Default: `GET`
	:param key: authorization key. Optional.
	:param params: dictionary containing get/post form parameters. Optional.
	:param mustHave: list or string containing the key(s) that must be contained in the json response. Optional.
	:param wants: can be a single string, or a list of strings.
	:return:    returns None if the result was invalid or if the request failed.
				if `wants` is a string, returns the key from the response.
				if `wants` is a list of strings, return a dictionary containing the wanted keys.
	"""
	if mustHave is None:
		mustHave = []
	if wants is None:
		wants = []
	if params is None:
		params = {}
	f = requests.post if requestType.lower() == "post" else requests.get
	result = f("{}/{}".format(glob.conf.config["cheesegull"]["apiurl"], handler), params=params, headers= {
		"Authorization": key
	})

	log.debug(result.url)
	log.debug(str(result.text))

	try:
		data = json.loads(result.text)
	except (json.JSONDecodeError, ValueError, requests.RequestException, KeyError, exceptions.noAPIDataError):
		return None

	# Params and status check
	if result.status_code != 200:
		return None
	if mustHave is not None:
		if type(mustHave) == str:
			mustHave = [mustHave]
		for i in mustHave:
			if i not in data:
				return None

	# Return what we want
	if type(wants) == str:
		if wants in data:
			return data[wants]
		return None
	elif len(wants) == 0:
		return data
	else:
		res = {}
		for i in data:
			if i in wants:
				res[i] = data[i]
		return res

def getListing(rankedStatus, page, gameMode, query):
	glob.dog.increment(glob.DATADOG_PREFIX + ".cheesegull_requests", tags=["cheesegull:listing"])
	params = {
		"query": query,
		"offset": page,
		"amount": 100
	}
	if rankedStatus is not None:
		params["status"] = rankedStatus
	if gameMode is not None:
		params["mode"] = gameMode
	return cheesegullRequest("search", params=params, mustHave="Sets", wants="Sets")

def getBeatmapSet(id):
	glob.dog.increment(glob.DATADOG_PREFIX + ".cheesegull_requests", tags=["cheesegull:set"])
	return cheesegullRequest("s/{}".format(id))

def getBeatmap(id):
	glob.dog.increment(glob.DATADOG_PREFIX + ".cheesegull_requests", tags=["cheesegull:beatmap"])
	setID = cheesegullRequest("b/{}".format(id), wants="ParentSetID")
	if setID is None or setID <= 0:
		return None
	return getBeatmapSet(setID)

def toDirect(data):
	s = "{SetID}.osz|{Artist}|{Title}|{Creator}|{RankedStatus}|10.00|0|{SetID}|".format(**data)
	if len(data["ChildrenBeatmaps2"]) > 0:
		s += "{}|0|0|0||".format(data["ChildrenBeatmaps2"][0]["BeatmapID"])
		for i in data["ChildrenBeatmaps2"]:
			s += "{DiffName}@{Mode},".format(**i)
	s = s.strip(",")
	s += "|"
	return s

def toDirectNp(data):
	return "{SetID}.osz|{Artist}|{Title}|{Creator}|{RankedStatus}|10.00|0|{SetID}|{SetID}|0|0|0|".format(**data)

def directToApiStatus(directStatus):
	if directStatus is None:
		return None
	elif directStatus == 0 or directStatus == 7:
		return 1
	elif directStatus == 8:
		return 4
	elif directStatus == 3:
		return 3
	elif directStatus == 2:
		return 0
	elif directStatus == 5:
		return -2
	elif directStatus == 4:
		return None
	else:
		return 1