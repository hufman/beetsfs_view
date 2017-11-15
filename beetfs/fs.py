import errno
import datetime
import os.path
import stat
import sys

import fuse
import beetfs.fuse_logger

default_time = datetime.datetime.now()
default_time = default_time.timestamp()


class BeetsFS(beetfs.fuse_logger.LoggingMixIn, fuse.Operations):
	def __init__(self, root, real_root, beets):
		self.root = root
		self.real_root = real_root
		self.beets = beets

	def _full_path(self, partial):
		if partial.startswith("/"):
			return os.path.join(self.root, partial[1:])
		else:
			return os.path.join(self.root, partial)

	def _real_path(self, partial):
		if partial.startswith("/"):
			return os.path.join(self.real_root, partial[1:])
		else:
			return os.path.join(self.real_root, partial)

	# ignore modifications
	def _EROFS(self, *args, **kwargs):
		raise fuse.FuseOSError(errno.EROFS)

	chmod = _EROFS
	chown = _EROFS
	mknod = _EROFS
	rmdir = _EROFS
	mkdir = _EROFS
	unlink = _EROFS
	symlink = _EROFS
	rename = _EROFS
	link = _EROFS
	create = _EROFS
	read = _EROFS
	write = _EROFS
	truncate = _EROFS

	def access(self, path, mode):
		# test if the file/directory exists and can be opened
		if mode & os.W_OK:	# writable? no
			raise fuse.FuseOSError(errno.EROFS)
		found = self.beets.get(self._full_path(path))
		if found is None:
			raise fuse.FuseOSError(errno.ENOENT)
		if mode & os.X_OK and found['type'] == 'file':
			raise fuse.FuseOSError(errno.EACCES)
		# everything else is all good
		# mode & os.F_OK   (exists)
		# mode & os.R_OK   (readable)
		# mode & os.X_OK   (cd into a dir)
		return 0

	def getattr(self, path, fh=None):
		found = self.beets.get(self._full_path(path))
		if found is None:
			raise fuse.FuseOSError(errno.ENOENT)
		st_common = {
			'st_atime': default_time,
			'st_ctime': default_time,
			'st_mtime': default_time,
			'st_gid': 65534,
			'st_uid': 65534
		}
		st_dir = {
			'st_mode': stat.S_IFDIR | 0o555,
			'st_nlink': 2,
			'st_size': 4096
		}
		st_file = {
			'st_mode': stat.S_IFREG | 0o444,
			'st_nlink': 1,
			'st_size': int(found.get('size', found.get('length', 60) * 50000))
		}
		ret = st_common
		if found['type'] == 'directory':
			ret.update(st_dir)
			return ret
		else:
			ret.update(st_file)
			return ret

	def opendir(self, path):
		found = self.beets.get(self._full_path(path))
		if found is None:
			raise fuse.FuseOSError(errno.ENOENT)
		return 0

	def readdir(self, path, fh=None):
		found = self.beets.get(self._full_path(path))
		if found is None:
			raise fuse.FuseOSError(errno.ENOENT)

		entries = [e['name'] for e in self.beets.listdir(self._full_path(path))]
		entries.append('.')
		if os.path.normpath(self._full_path(path)) != '/':
			entries.append('..')
		return entries

	def readlink(self, path):
		raise fuse.FuseOSError(errno.ENOENT)

	def open(self, path, flags):
		if flags & os.O_WRONLY or \
		   flags & os.O_RDWR or \
		   flags & os.O_APPEND or \
		   flags & os.O_CREAT or \
		   flags & os.O_TRUNC:
			raise errno.EROFS
		return os.open(self._real_path(path), flags)

	def read(self, path, length, offset, fh):
		os.lseek(fh, offset, os.SEEK_SET)
		return os.read(fh, length)

	def release(self, path, fh):
		return os.close(fh)

	def statfs(self, path):
		return {'f_bsize':512, 'f_blocks':4096, 'f_bavail':2048}

def run(mountpoint, real_root, db):
	fs = fuse.FUSE(BeetsFS(mountpoint, real_root, db), mountpoint, foreground=True, ro=True, nothreads=True)
