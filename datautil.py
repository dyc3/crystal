import io

class DataUtil(object):
	"""docstring for DataUtil."""
	def __init__(self):
		super(DataUtil, self).__init__()

	@staticmethod
	def loadTrainingData(filename):
		X = []
		y = []
		with open(filename, "r") as f:
			for line in f:
				spl = line.rstrip("\n").split(",")
				X.append(spl[0])
				y.append(spl[1])
		return X, y
