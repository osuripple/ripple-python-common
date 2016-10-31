import time
import threading

class rateLimiter:
	"""
	Rate limiter class
	"""
	def __init__(self, rate, per):
		"""
		Initialize a rateLimiter object

		:param rate: max number of requests...
		:param per: ...in this interval (seconds)
		"""
		self.rate = rate
		self.per = per
		self.allowance = self.rate  # requests
		self.lastCheck = time.time()

	def checkRateLimit(self, update=True):
		"""
		Check rate (and update) limit.

		:param update: if True, update latest check time. Default: True
		:return: True if requests are below rate limit, otherwise false
		"""
		current = time.time()
		timePassed = current - self.lastCheck
		if update:
			self.lastCheck = current
		self.allowance += timePassed * (self.rate / self.per)
		if (self.allowance > self.rate):
			self.allowance = self.rate # throttle
		if (self.allowance < 1.0):
			return False
		else:
			if update:
				self.allowance -= 1.0
			return True

class rateLimiters:
	"""
	A group of rate limiters
	"""
	def __init__(self, rate, per):
		"""
		Initialize a rateLimiters object
		:param rate: default max requests...
		:param per: ...in this interval (seconds)
		NOTE: Authenticated rateLimiters have `2 * rate / per` rate limit
		"""
		self.publicRateLimiters = {}
		self.authRateLimiters = {}
		self.rate = rate
		self.per = per

	def addRateLimiter(self, identifier, auth):
		"""
		Add a public/auth rate limiter

		:param identifier: user id (if auth) or IP (if private)
		:param auth: if True, create a auth API token, otherwise create a public one
		:return:
		"""
		dest = self.authRateLimiters if auth else self.publicRateLimiters
		if identifier not in dest:
			rate = self.rate * 2 if auth else self.rate
			dest[identifier] = rateLimiter(rate, self.per)

	def getRateLimiter(self, identifier, auth):
		"""
		Returns a specific rateLimiter.
		If the requested rateLimiter doesn't exist, it'll be created.

		:param identifier: user id (if auth) or IP (if private)
		:param auth: if True, create a auth API token, otherwise create a public one
		:return: rateLimiter object
		"""
		dest = self.authRateLimiters if auth else self.publicRateLimiters
		if identifier not in dest:
			self.addRateLimiter(identifier, auth)
		return dest[identifier]

	def clearRateLimiters(self, interval=60, repeatEvery=60):
		"""
		Delete unused rate limiters.

		:param interval: check interval in seconds. Default: 60
		:param repeatEvery: number of seconds between checks. If <= 0, check only once
		:return:
		"""
		delete = []

		# Add old keys to delete list
		for d in [self.publicRateLimiters, self.authRateLimiters]:
			for key, value in d.items():
				if value.lastCheck < time.time() - interval:
					delete.append(key)

			# Delete all unused rate limiters by key
			for i in delete:
				del d[i]

		# Repeat every x seconds
		if repeatEvery > 0:
			threading.Timer(repeatEvery, self.clearRateLimiters).start()