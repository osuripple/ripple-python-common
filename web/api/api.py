import tornado.gen
import tornado.web

from common.web import requestsManager
from common.web.api import exceptions
from objects import glob


def args(*requiredArgs):
	"""
	Decorator that checks passed arguments.
	If some arguments are missing, an invalidArgumentsError exception is thrown.
	Example:
	```
	@api.api
	@api.args("first", "second")
	def asyncGet(self):
		...
	```

	:param requiredArgs: tuple containing required arguments strings
	:return:
	"""
	def decorator(function):
		def wrapper(self, *args, **kwargs):
			missing = []
			for i in requiredArgs:
				if i not in self.request.arguments:
					missing.append(i)
			if missing:
				raise exceptions.invalidArgumentsError("Missing required argument ({})".format(missing))
			return function(self, *args, **kwargs)
		return wrapper
	return decorator

def apiErrors(f):
	"""
	Decorator that handles API requests and errors.

	:param f:
	:return:
	"""
	def wrapper(self, *args, **kwargs):
		try:
			#self.checkAPIKey()
			#glob.rateLimits.getRateLimiter()
			return f(self, *args, **kwargs)
		except exceptions.invalidArgumentsError as e:
			self.data["status"] = 400
			self.data["message"] = str(e)
		except exceptions.forbiddenError:
			self.data["status"] = 403
			self.data["message"] = "Invalid token"
		except exceptions.notFoundError:
			self.data["status"] = 404
			self.data["message"] = "Data not found"
		except exceptions.methodNotAllowedError:
			self.data["status"] = 405
			self.data["message"] = "Method not allowed"
		finally:
			self.set_status(self.data["status"])
			self.write(self.data)
	return wrapper

def api(f):
	"""
	Decorator that handles api errors asynchronously.
	Using this decorator is the same as doing:
	```
	@tornado.gen.engine
	@tornado.web.asynchronous
	@api.api
	def asyncGet():
		...
	```

	:param f:
	:return:
	"""
	return tornado.gen.engine(tornado.web.asynchronous(apiErrors(f)))

class asyncAPIHandler(requestsManager.asyncRequestHandler):
	"""
	Async API handler.
	Same as a normal asyncRequestHandler, but with a self.data attribute.
	self.data is the dictionary that will be returned in the response.
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.data = {
			"status": 200,
			"message": "ok"
		}