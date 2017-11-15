import sqlite3

class BeetsDB(object):
	def __init__(self, path):
		self._has_directories = False	# directory index in the database
		self.path = path
		self.db = sqlite3.connect(self.path)
		self.db.row_factory = sqlite3.Row
		self._check_schema()

	def _check_schema(self):
		cursor = self.db.cursor()
		cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
		tables = [r[0] for r in cursor]
		if 'directories' in tables:
			self._has_directories = True

	def listdir(self, path):
		if self._has_directories:
			return self.listdir_indexed(path)
		else:
			return self.listdir_naive(path)

	def listdir_naive(self, path):
		contents = []
		path = path.rstrip('/')
		start_query = "%s/%%" % (path,)
		end_query = "%s/%%/%%" % (path,)
		# get the list of subdirs
		cursor = self.db.cursor()
		cursor.execute("SELECT DISTINCT substr(path, ?, instr(substr(path, ?), '/')-1) FROM items WHERE path like ?;", (len(path)+2, len(path)+2, end_query))
		contents.extend(({'name':r[0], 'type':'directory'} for r in cursor))
		
		# get the list of files
		cursor.execute("SELECT substr(path,?) FROM items WHERE path LIKE ? AND path NOT LIKE ?;", (len(path)+2, start_query, end_query))
		contents.extend(({'name':r[0], 'type':'file'} for r in cursor))

		return contents

	def get(self, path):
		cursor = self.db.cursor()
		path = path.rstrip('/')
		# try to find a file by name
		cursor.execute("SELECT * FROM items WHERE path == ?;", (path,))
		result = cursor.fetchone()
		if result is not None:
			# found a file
			result = dict(zip(result.keys(), result))
			result['type'] = 'file'
			return result

		# try to find a directory
		start_query = "%s/%%" % (path,)
		cursor.execute("SELECT * FROM items WHERE path LIKE ? LIMIT 1;", (start_query,))
		result = cursor.fetchone()
		if result is not None:
			# found a directory
			return {'path': path, 'type': 'directory'}
		# give up
		return None
