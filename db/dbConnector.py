import pymysql
import pymysqlpool

import common.log.logUtils as log


class db:
	def __init__(self, size=8, **kwargs):
		self.timeout = 10
		self.retry_num = 10
		self.pool = pymysqlpool.ConnectionPool(size=size, **kwargs)

	def _get_connection(self):
		return self.pool.get_connection(timeout=self.timeout, retry_num=self.retry_num)

	def execute(self, query, params=None):
		if params is None:
			params = ()
		conn = self._get_connection()
		with conn:
			cur = conn.cursor(pymysql.cursors.DictCursor)
			log.debug("{} ({})".format(query, params))
			cur.execute(query, params)
			return cur.lastrowid

	def fetch(self, query, params=None, all_=False):
		if params is None:
			params = ()
		conn = self._get_connection()
		with conn:
			log.debug("{} ({})".format(query, params))
			return conn.execute_query(query, params, dictcursor=True, return_one=not all_)

	def fetchAll(self, query, params=None):
		return self.fetch(query=query, params=params, all_=True)
