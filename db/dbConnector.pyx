import queue
import MySQLdb
import MySQLdb.cursors
import MySQLdb._exceptions
import time

from objects import glob
from common.log import logUtils as log

class worker:
	"""
	A single MySQL worker
	"""
	def __init__(self, connection, temporary=False):
		"""
		Initialize a MySQL worker

		:param connection: database connection object
		:param temporary: if True, this worker will be flagged as temporary
		"""
		self.connection = connection
		self.temporary = temporary
		log.debug("Created MySQL worker. Temporary: {}".format(self.temporary))

	def ping(self):
		"""
		Ping MySQL server using this worker.

		:return: True if connected, False if error occured.
		"""
		c = self.connection.cursor(MySQLdb.cursors.DictCursor)
		try:
			c.execute("SELECT 1+1")
			return True
		except MySQLdb.Error:
			return False
		finally:
			c.close()

	def __del__(self):
		"""
		Close connection to the server

		:return:
		"""
		self.connection.close()

class connectionsPool:
	"""
	A MySQL workers pool
	"""
	def __init__(self, host, port, username, password, database, size=128):
		"""
		Initialize a MySQL connections pool

		:param host: MySQL server host
		:param port: MySQL server port
		:param username: MySQL username
		:param password: MySQL password
		:param database: MySQL database name
		:param size: pool max size
		"""
		self.config = {
			"host": host,
			"port": port,
			"user": username,
			"passwd": password,
			"db": database
		}
		self.maxSize = size
		self.pool = queue.Queue(self.maxSize)
		self.consecutiveEmptyPool = 0
		self.fillPool()

	def newWorker(self, temporary=False):
		"""
		Create a new worker.

		:param temporary: if True, flag the worker as temporary
		:return: instance of worker class
		"""
		db = MySQLdb.connect(
			**self.config,
			autocommit=True,
			charset="utf8",
			use_unicode=True
		)
		conn = worker(db, temporary)
		return conn

	def fillPool(self, newConnections=0):
		"""
		Fill the queue with workers

		:param newConnections:	number of new connections. If 0, the pool will be filled entirely.
		:return:
		"""
		# If newConnections = 0, fill the whole pool
		if newConnections == 0:
			newConnections = self.maxSize

		# Fill the pool
		for _ in range(0, newConnections):
			if not self.pool.full():
				self.pool.put_nowait(self.newWorker())

	def getWorker(self, level=0):
		"""
		Get a MySQL connection worker from the pool.
		If the pool is empty, a new temporary worker is created.

		:param level: number of failed connection attempts. If > 50, return None
		:return: instance of worker class
		"""
		# Make sure we below 50 retries
		#log.info("Pool size: {}".format(self.pool.qsize()))
		glob.dog.increment(glob.DATADOG_PREFIX+".mysql_pool.queries")
		glob.dog.gauge(glob.DATADOG_PREFIX+".mysql_pool.size", self.pool.qsize())
		if level >= 50:
			log.warning("Too many failed connection attempts. No MySQL connection available.")
			return None

		try:
			if self.pool.empty():
				# The pool is empty. Spawn a new temporary worker
				log.warning("MySQL connections pool is empty. Using temporary worker.")
				worker = self.newWorker(True)

				# Increment saturation
				self.consecutiveEmptyPool += 1

				# If the pool is usually empty, expand it
				if self.consecutiveEmptyPool >= 10:
					log.warning("MySQL connections pool is empty. Filling connections pool.")
					self.fillPool()
			else:
				# The pool is not empty. Get worker from the pool
				# and reset saturation counter
				worker = self.pool.get()
				self.consecutiveEmptyPool = 0
		except MySQLdb.OperationalError:
			# Connection to server lost
			# Wait 1 second and try again
			log.warning("Can't connect to MySQL database. Retrying in 1 second...")
			glob.dog.increment(glob.DATADOG_PREFIX+".mysql_pool.failed_connections")
			time.sleep(1)
			return self.getWorker(level=level+1)

		# Return the connection
		return worker

	def putWorker(self, worker):
		"""
		Put the worker back in the pool.
		If the worker is temporary, close the connection
		and destroy the object

		:param worker: worker object
		:return:
		"""
		if worker.temporary or self.pool.full():
			# Kill the worker if it's temporary or the queue
			# is full and we can't  put anything in it
			del worker
		else:
			# Put the connection in the queue if there's space
			self.pool.put_nowait(worker)


class db:
	"""
	A MySQL helper with multiple workers
	"""
	def __init__(self, host, port, username, password, database, initialSize):
		"""
		Initialize a new MySQL database helper with multiple workers.
		This class is thread safe.

		:param host: MySQL server host
		:param port: MySQL server port
		:param username: MySQL username
		:param password: MySQL password
		:param database: MySQL database name
		:param initialSize: initial pool size
		"""
		self.pool = connectionsPool(host, port, username, password, database, initialSize)

	def _handleReconnection(self, f):
		def decorator(query, params=None, **kwargs):
			if params is None:
				params = ()

			while True:
				worker = self.pool.getWorker()
				if worker is None:
					raise RuntimeError("None worker, MySQL seems to be offline.")
				cursor = None
				try:
					# Create cursor, execute the query and fetch one/all result(s)
					cursor = worker.connection.cursor(MySQLdb.cursors.DictCursor)
					cursor.execute(query, params)
					log.debug(query)
					return f(cursor)
				except MySQLdb.OperationalError as e:
					log.error("OperationalError while executing query. Destroying connection and retrying...")
					try:
						cursor.close()
					except Exception as e:
						log.error("Could not close cursor ({})".format(e))
					cursor = None
					try:
						worker.connection.close()
					except Exception as e:
						log.error("Could not close connection ({})".format(e))
					del worker
					worker = None
					time.sleep(1)
				finally:
					# Close the cursor and release worker's lock
					if cursor is not None:
						cursor.close()
					if worker is not None:
						self.pool.putWorker(worker)
		return decorator

	def execute(self, *args, **kwargs):
		return self._handleReconnection(lambda x: x.lastrowid)(*args, **kwargs)

	def fetch(self, *args, all_=False, **kwargs):
		return self._handleReconnection(
			lambda x: x.fetchall() if all_ else x.fetchone()
		)(*args, **kwargs)

	def fetchAll(self, *args, **kwargs):
		return self.fetch(*args, all_=True, **kwargs)
