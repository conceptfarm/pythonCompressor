import traceback
import sys

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


class WorkerSignals(QObject):
	finished = pyqtSignal(object)
	error = pyqtSignal(tuple)
	result = pyqtSignal(object)
	progressMin = pyqtSignal(int)
	progressMax = pyqtSignal(int)
	progressValue = pyqtSignal(object)
	progressFormat = pyqtSignal(str)
	progressLabel = pyqtSignal(str)
	progressLog = pyqtSignal(str)
	progressNone = pyqtSignal()
	progressStarted = pyqtSignal(tuple)

class Worker(QRunnable):
	def __init__(self, fn, progressType=None, *args, **kwargs):
		super().__init__()

		# Store constructor arguments (re-used for processing)
		self.setAutoDelete(True)
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.signals = WorkerSignals()

		# Add the callback to our kwargs
		self.kwargs['progress_callback'] = None
		if progressType == 'val':
			self.kwargs['progress_callback'] = self.signals.progressValue
		elif progressType == None:
			self.kwargs['progress_callback'] = self.signals.progressNone
		
		self.kwargs['progress_setmin'] = self.signals.progressMin
		self.kwargs['progress_setmax'] = self.signals.progressMax
		self.kwargs['progress_setformat'] = self.signals.progressFormat
		self.kwargs['progress_setlabel'] = self.signals.progressLabel
		self.kwargs['progress_setlog'] = self.signals.progressLog
		self.kwargs['progress_started'] = self.signals.progressStarted
	
	@pyqtSlot()
	def run(self):
		'''
		Initialise the runner function with passed args, kwargs.
		'''
		
		# Retrieve args/kwargs here; and fire processing using them
		try:
			result = self.fn(*self.args, **self.kwargs)
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			self.signals.result.emit(result)  # Return the result of the processing
		finally:
			self.signals.finished.emit(result)  # Done

class Callbacks():
	def __init__(self, **kwargs) -> None:
		self.progress_callback = None
		self.progress_setformat = None
		self.progress_setlabel = None
		self.progress_setmin = None
		self.progress_setmax = None
		self.progress_setlog = None
		self.progress_started = None
		self.var = None
		self.setupVars(**kwargs)
	
	
	def setupVars(self, **kwargs):
		try:
			self.progress_callback = kwargs['progress_callback']
		except:
			pass
		
		try:
			self.progress_setformat = kwargs['progress_setformat']
		except:
			pass
		
		try:
			self.progress_setlabel = kwargs['progress_setlabel']
		except:
			pass
		
		try:
			self.progress_setmin = kwargs['progress_setmin']
		except:
			pass
		
		try:
			self.progress_setmax = kwargs['progress_setmax']
		except:
			pass
		
		try:
			self.progress_setlog = kwargs['progress_setlog']
		except:
			pass

		try:
			self.progress_started = kwargs['progress_started']
		except:
			pass
	
	
	def setmax(self, var):
		try:
			self.progress_setmax.emit(var)
		except:
			pass
	
	def setmin(self, var):
		try:
			self.progress_setmin.emit(var)
		except:
			pass

	def setlabel(self, var):
		try:
			self.progress_setlabel.emit(var)
		except:
			pass
	
	def setlog(self, var):
		try:
			self.progress_setlog.emit(var)
		except:
			pass

	def setformat(self, var):
		try:
			self.progress_setformat.emit(var)
		except:
			pass
	
	def setstarted(self, var):
		try:
			self.progress_started.emit(var)
		except:
			pass
	
	def callback(self, var):
		try:
			self.progress_callback.emit(var)
		except:
			pass