import threading
import time

import pymysql
import pymysql.err

import objects.glob
import common.log.logUtils as log


class db:
	def __init__(self, **kwargs):
		self.connectionKwargs = kwargs
		self.maxAttempts = 30

	def connectionFactory(self):
		return pymysql.connect(**self.connectionKwargs)

	def _execute(self, query, params=None, cb=None):
		if params is None:
			params = ()
		attempts = 0
		result = None
		lastExc = None
		while attempts < self.maxAttempts:
			conn = objects.glob.threadScope.db
			cur = conn.cursor(pymysql.cursors.DictCursor)
			try:
				log.debug("{} ({})".format(query, params))
				cur.execute(query, params)
				if callable(cb):
					result = cb(cur)
				break
			except pymysql.err.OperationalError as e:
				lastExc = e
				log.error(
					"MySQL operational error on Thread {} ({}). Trying to recover".format(
						threading.get_ident(),
						e
					)
				)

				# Close cursor now
				try:
					cur.close()
				except:
					pass

				# Sleep if necessary
				if attempts > 0:
					time.sleep(1)

				# Reset connection (this closes the connection as well)
				objects.glob.threadScope.dbClose()
				attempts += 1
			finally:
				# Try to close the cursor (will except if there was a failure)
				try:
					cur.close()
				except:
					pass
		if lastExc is not None:
			raise lastExc
		return result

	def execute(self, query, params=None):
		return self._execute(query=query, params=params, cb=lambda x: x.lastrowid)

	def fetch(self, query, params=None):
		return self._execute(query=query, params=params, cb=lambda x: x.fetchone())

	def fetchAll(self, query, params=None):
		return self._execute(query=query, params=params, cb=lambda x: x.fetchall())
