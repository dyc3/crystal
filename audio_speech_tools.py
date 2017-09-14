#!/usr/bin/env python3

class CrystalDisplay(QOpenGLWindow):
	versionprofile = QOpenGLVersionProfile()
	versionprofile.setVersion(2, 0)
	spectrum_array = [] #[(-1,-1),(1,1)]
	spectrum_mean = 0
	energy_lerp = 0

	def __init__(self, device_index = None, sample_rate = 44100, chunk_size = 1024):
		QOpenGLWindow.__init__(self)
		"""
		self.setWindowFlags(
			QtCore.Qt.WindowStaysOnTopHint |
			QtCore.Qt.FramelessWindowHint |
			QtCore.Qt.X11BypassWindowManagerHint
			)
		"""
		self.visualizer = "energy-spectrum"
		self.max_energy = 300
		self.energy_history = [0,0,0,0]

		self.setGeometry(QStyle.alignedRect(
			QtCore.Qt.LeftToRight, QtCore.Qt.AlignCenter,
			QtCore.QSize(640, 480),
			qApp.desktop().availableGeometry()))

		self.animationTimer = QTimer()
		self.animationTimer.setSingleShot(False)
		self.animationTimer.timeout.connect(self.animate)
		if self.visualizer == "spectrum":
			self.animationTimer.start(20)
		else:
			self.animationTimer.start(50)

		# set up PyAudio
		self.pyaudio_module = self.get_pyaudio()

		assert device_index is None or isinstance(device_index, int), "Device index must be None or an integer"
		if device_index is not None: # ensure device index is in range
			audio = self.pyaudio_module.PyAudio()
			try:
				count = audio.get_device_count() # obtain device count
			except:
				audio.terminate()
				raise
			assert 0 <= device_index < count, "Device index out of range ({0} devices available; device index should be between 0 and {1} inclusive)".format(count, count - 1)
		assert isinstance(sample_rate, int) and sample_rate > 0, "Sample rate must be a positive integer"
		assert isinstance(chunk_size, int) and chunk_size > 0, "Chunk size must be a positive integer"
		self.device_index = device_index
		self.format = self.pyaudio_module.paInt16 # 16-bit int sampling
		self.SAMPLE_WIDTH = self.pyaudio_module.get_sample_size(self.format) # size of each sample
		self.SAMPLE_RATE = sample_rate # sampling rate in Hertz
		self.CHUNK = chunk_size # number of frames stored in each buffer

		self.audio = self.pyaudio_module.PyAudio()
		self.stream = None

		self.pyaudio_stream = self.audio.open(
				input_device_index = self.device_index, channels = 1,
				format = self.format, rate = self.SAMPLE_RATE, frames_per_buffer = self.CHUNK,
				input = True, # stream is an input stream
			)

	@staticmethod
	def get_pyaudio():
		"""
		Imports the pyaudio module and checks its version. Throws exceptions if pyaudio can't be found or a wrong version is installed
		"""
		try:
			import pyaudio
		except ImportError:
			raise AttributeError("Could not find PyAudio; check installation")
		from distutils.version import LooseVersion
		if LooseVersion(pyaudio.__version__) < LooseVersion("0.2.9"):
			raise AttributeError("PyAudio 0.2.9 or later is required (found version {0})".format(pyaudio.__version__))
		return pyaudio

	def initializeGL(self):
		"""Apply OpenGL version profile and initialize OpenGL functions."""
		try:
			self.gl = self.context().versionFunctions(self.versionprofile)
		except Exception as e:
			print("error when getting self.gl: {}".format(e))
			return
		if not self.gl:
			raise RuntimeError("unable to apply OpenGL version profile")

		self.gl.initializeOpenGLFunctions()

		self.gl.glClearColor(0.0, 0.0, 0.0, 0.0)

	# drawing documentation: http://doc.qt.io/qt-5/qpainter.html
	def paintGL(self):
		if not self.gl: return

		self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)
		glEnableClientState(GL_VERTEX_ARRAY)
		#r = map(self.spectrum_mean, -0.3, 0.3, 0, 0.5)
		#g = map(self.spectrum_mean, -0.3, 0.3, 0, 0.2)
		#b = map(self.spectrum_mean, -0.3, 0.3, 0, 1.0)
		#r = clamp(r, 0.0, 1.0)
		#g = clamp(g, 0.0, 1.0)
		#b = clamp(b, 0.0, 1.0)

		glColor(0.4,0.2,1.0) # dunno what color this is, but it should be a light blue-ish purple

		glVertexPointerf(self.spectrum_array)
		glDrawArrays(GL_LINE_STRIP, 0, len(self.spectrum_array))
		glFlush()

	def resizeGL(self, w, h):
		"""Resize viewport to match widget dimensions."""
		if not self.gl: return
		self.gl.glViewport(0, 0, w, h)

	def animate(self):
		global isListening

		if not self.isVisible():
			return
		try:
			if enableNewBgListener:
				buffer = self.spectrum_data
			else:
				buffer = self.pyaudio_stream.read(self.CHUNK, exception_on_overflow = False)
		except Exception as e:
			return
		if self.visualizer == "spectrum":
			self.spectrum_array = []
			maxCenter = 0.6
			maxEdge = 0.0
			x = -1.0
			togg = True
			for a in buffer:
				x += 2.0 / (len(buffer))
				g = abs(x)/1.5
				k = pow(g,g)
				if x <= 0:
					yRange = map(x, -1.0, 0.0, maxEdge, maxCenter - k)
				else:
					yRange = map(x, 0.0, 1.0, maxCenter - k, maxEdge)
				if togg:
					y = map(a, 1.0, 256.0, 0, yRange)
				else:
					y = map(a, 1.0, 256.0, 0, -yRange)
				togg = not togg
				#y = clamp(y, -yRange, yRange)
				self.spectrum_array.append([x, y])
			self.spectrum_mean = numpy.mean(self.spectrum_array)
		elif self.visualizer == "energy-spectrum":
			self.spectrum_array = []
			energy = audioop.rms(buffer, self.SAMPLE_WIDTH) # energy of the audio signal
			self.energy_lerp = lerp(0.2, self.energy_lerp, energy)
			#print("energy: {} lerp: {}".format(energy, self.energy_lerp))
			self.min_energy = 30
			self.max_energy = 200
			maxCenter = 0.6
			maxEdge = 0.0
			x = -1.0
			togg = True
			vertices = 800
			for v in range(vertices):
				x = -1 + (2.0 / vertices) * v
				g = abs(x)/1.5
				k = pow(g,g)
				if x <= 0:
					yRange = map(x, -1.0, 0.0, maxEdge, maxCenter - k)
				else:
					yRange = map(x, 0.0, 1.0, maxCenter - k, maxEdge)
				if togg:
					y = map(self.energy_lerp, 0, self.max_energy, 0, yRange)
				else:
					y = map(self.energy_lerp, 0, self.max_energy, 0, -yRange)
				r = ((random.random() - 0.5) / 20) * (energy / self.max_energy)
				y += r
				togg = not togg
				self.spectrum_array.append([x, y])
		elif self.visualizer == "energy":
			self.spectrum_array = []
			energy = audioop.rms(buffer, self.SAMPLE_WIDTH) # energy of the audio signal
			self.energy_history.append(energy)
			# i dont know where im going with this

		self.update()

display = CrystalDisplay()
display.show()
