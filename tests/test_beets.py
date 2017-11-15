import beetfs
import beetfs.beetsdb

import os
import pytest
import sqlite3
from operator import itemgetter

@pytest.fixture
def sample_data():
	return { '/tank/shares/music/Artists/': {
		'J.S. Bach': {
			'': ['Unknown.mp3'],
			'Brandenburg Concertos': {
				'': ['BVW1048-1.mp3', 'BWV1048-2.mp3', 'BWV1048-3.mp3']
			},
		},
		'P.D.Q. Bach': {
			'': ['Grand Serenade For An Awful Lot of Wind & Percussion.mp3']
		}
	} }

@pytest.fixture
def flat_sample_data(sample_data):
	data = []
	
	def flatten(data, root, node):
		for k,v in node.items():
			if k == '':
				for f in v:
					data.append(os.path.join(root, f))
			else:
				flatten(data, os.path.join(root, k), v)
	flatten(data, '/', sample_data)
	return data

@pytest.fixture
def sample_database_path(tmpdir, flat_sample_data):
	db_path = tmpdir.join('test.db')
	db = sqlite3.connect(str(db_path))
	db.execute("CREATE TABLE items (path STRING PRIMARY KEY);")
	
	for item in flat_sample_data:
		print(item)
		db.execute("INSERT INTO items (path) VALUES (?);", (item,))
	db.commit()
	db.close()
	return db_path

def test_list_path(sample_database_path):
	beets = beetfs.beetsdb.BeetsDB(str(sample_database_path))
	assert [{'name':'shares','type':'directory'}] == \
	       beets.listdir('/tank'), "Incorrect dir list of /tank"
	assert [{'name':'shares','type':'directory'}] == \
	       beets.listdir('/tank/'), "Incorrect dir list of /tank"
	assert [{'name':'J.S. Bach','type':'directory'},
	        {'name':'P.D.Q. Bach','type':'directory'}] == \
	       sorted(beets.listdir('/tank/shares/music/Artists'), key=itemgetter('name'))
	assert [{'name':'J.S. Bach','type':'directory'},
	        {'name':'P.D.Q. Bach','type':'directory'}] == \
	       sorted(beets.listdir('/tank/shares/music/Artists/'), key=itemgetter('name'))
	assert [{'name':'Brandenburg Concertos','type':'directory'},
	        {'name':'Unknown.mp3','type':'file'}] == \
	       sorted(beets.listdir('/tank/shares/music/Artists/J.S. Bach'), key=itemgetter('name'))

def test_get(sample_database_path):
	beets = beetfs.beetsdb.BeetsDB(str(sample_database_path))
	assert beets.get('/tank/shares/music/Artists/J.S. Bach/Unknown.mp3') is not None
	assert beets.get('/tank/shares/music/Artists/J.S. Bach/Missing.mp3') is None
	assert beets.get('/tank/shares/music/Artists/J.S. Bach/') is not None
	assert beets.get('/tank/shares/music/Artists/J.S. Bach') is not None
	assert beets.get('/tank/shares/music/Artists/J.') is None
	assert 'file' == beets.get('/tank/shares/music/Artists/J.S. Bach/Unknown.mp3')['type']
	assert 'directory' == beets.get('/tank/shares/music/Artists/J.S. Bach/')['type']
	assert 'directory' == beets.get('/tank/shares/music/Artists/J.S. Bach')['type']
