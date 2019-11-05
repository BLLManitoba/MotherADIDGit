import cPickle
import wave
import os
import time


def save_data(obj, filename):
	with open(filename, 'wb') as f:
		cPickle.dump(obj, f, cPickle.HIGHEST_PROTOCOL)


def load_data(filename):
	with open(filename, 'rb') as f:
		data = cPickle.load(f)
	return data

# def sum_dicts(*dics):
# 	s = {}
# 	for dic in dics:
# 		# s = {key: int(round(s.get(key, 0) + dic.get(key, 0))) for key in set(dic)}
# 		s = {key: s.get(key, 0) + dic.get(key, 0) for key in set(dic)}

# 	return s

# def sum_dicts(*dicts):
# 	res = {}
# 	for dic in dicts:
# 	    res = dict(res.items() + dic.items() +
# 	    [(k, res[k] + dic[k]) for k in set(res) & set(dic)])
# 	return res



def timer(func):
	def wrapper(*args, **kwargs):
		t0 = time.time()
		res = func(*args, **kwargs)
		t = time.time() - t0
		print '{} took {} s'.format(func.__name__, t)
		return res
	return wrapper


# def merge_coders_data(path, datafiles):
# 	data = {}
# 	for dfile in datafiles:
# 		coder = dfile.strip('.pkl')
# 		with open(os.path.join(path, dfile), 'rb') as f:
# 			data[coder] = cPickle.load(f)
# 	return data


def merge_coders_data(path):
	data = {}
	for dfile in [d for d in os.listdir(path) if d.endswith('.pkl')]:
		coder = dfile.replace('.pkl','')
		with open(os.path.join(path, dfile), 'rb') as f:
			data[coder] = cPickle.load(f)
	return data
