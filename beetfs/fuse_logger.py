import errno
import inspect
import logging
import os
import stat
import sys


logger = logging.getLogger(__name__)


def parse_args(fn, args, kwargs):
	sig = inspect.signature(fn)
	bound = sig.bind(*args, **kwargs)
	bound_args = dict(bound.arguments)
	return bound_args

def format_func_call(fn, args, kwargs):
	formatter_name = 'format_func_args_%s' % (fn.__name__,)
	formatter = globals().get(formatter_name, format_func_args_default)
	bound_args = parse_args(fn, args, kwargs)
	return '%s(%s)' % (fn.__name__, formatter(bound_args))

def format_func_args_default(bound_args):
	return ', '.join(('%s=%s' % (k,format_arg_switcher(k,v))
	                  for (k,v) in bound_args.items()
	                 ))
def format_arg_switcher(arg_name, arg_value):
	formatter_name = 'format_arg_%s' % (arg_name,)
	formatter = globals().get(formatter_name, format_arg_default)
	return formatter(arg_value)

def format_arg_default(arg):
	if isinstance(arg, str):
		return '"%s"' % (arg, )
	return '%s' % (arg,)

def format_arg_mode(arg):
	pieces = []
	mode_names = ['S_IFSOCK', 'S_IFLNK', 'S_IFREG', 'S_IFBLK', 'S_IFDIR', 'S_IFCHR', 'S_IFIFO']
	for name in mode_names:
		try:
			mode = getattr(stat, name)
		except:
			continue
		if not isinstance(mode, int):
			continue
		if arg & mode == mode:
			pieces.append(name)
			arg = arg - mode
	pieces.append('0o%o' % (arg,))
	return '|'.join(pieces)

def format_arg_flags(arg):
	pieces = []
	flag_names = [m for m in dir(os) if m.startswith('O_')]
	flags = {}
	flags['O_LARGEFILE'] = 0o100000	# on Linux
	for name in flag_names:
		try:
			flag = getattr(stat, name)
		except:
			continue
		if not isinstance(flag, int):
			continue
		flags[name] = flag
	for name,flag in flags.items():
		if arg & flag == flag:
			pieces.append(name)
			arg = arg - flag
	pieces.append('0o%o' % (arg,))
	return '|'.join(pieces)

def trace_function_call(fn, *args, **kwargs):
	try:
		ret = fn(*args, **kwargs)
	except Exception as e:
		log_exception(fn, args, kwargs, e)
		raise
	log_success(fn, args, kwargs, ret)
	return ret

def log_success(fn, args, kwargs, ret):
	if isinstance(ret, str) and len(ret) > 200:
		ret = '"%s…"' % (ret[0:199],)
	elif isinstance(ret, bytes) and len(ret) > 200:
		ret = '%s…' % (ret[0:199],)
	elif isinstance(ret, str):
		ret = '"%s"' % (ret,)
	elif isinstance(ret, bytes):
		ret = '%s' % (ret,)
	logger.debug("%s = %s" % (format_func_call(fn, args, kwargs), ret))
def log_exception(fn, args, kwargs, e):
	logger.error("%s raises %s" % (format_func_call(fn, args, kwargs), e))

class LoggingMixIn(object):
	def __call__(self, op, *args, **kwargs):
		fn = getattr(self, op)
		return trace_function_call(fn, *args, **kwargs)
