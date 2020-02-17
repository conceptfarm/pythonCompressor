from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import re
import time
import traceback, sys
from subprocessClass import pyFFMEGCompress


from datetime import datetime
from math import floor



class WorkerSignals(QObject):
	'''
	Defines the signals available from a running worker thread.

	Supported signals are:

	finished
		No data
	
	error
		`tuple` (exctype, value, traceback.format_exc() )
	
	result
		`object` data returned from processing, anything

	progress
		`int` indicating % progress 

	'''
	finished = pyqtSignal(bool)
	error = pyqtSignal(tuple)
	result = pyqtSignal(object)
	progress = pyqtSignal(int)


class Worker(QRunnable):
	'''
	Worker thread

	Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

	:param callback: The function callback to run on this worker thread. Supplied args and 
					 kwargs will be passed through to the runner.
	:type callback: function
	:param args: Arguments to pass to the callback function
	:param kwargs: Keywords to pass to the callback function

	'''

	def __init__(self, fn, path, codec, alpha, frameRate, *args, **kwargs):
		super(Worker, self).__init__()

		# Store constructor arguments (re-used for processing)
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.signals = WorkerSignals()	
		self.path = path
		self.codec = codec
		self.alpha = alpha
		self.frameRate = frameRate
		
		# Add the callback to our kwargs
		self.kwargs['progress_callback'] = self.signals.progress	

	@pyqtSlot()
	def run(self):
		'''
		Initialise the runner function with passed args, kwargs.
		'''
		
		self.finishResult = False
		
		# Retrieve args/kwargs here; and fire processing using them
		try:
			result = self.fn( self.path, self.codec, self.alpha, self.frameRate, *self.args, **self.kwargs)
		except:
			#print("error")
			self.finishResult = True
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit( (exctype, value, traceback.format_exc()) )
			#errorCSS = "QProgressBar::chunk { background-color: red; }"
			#errorText = "Error"
			#self.signals.error.emit( (errorCSS, errorText) )
		else:
			self.signals.result.emit(result)  # Return the result of the processing
		finally:
			self.signals.finished.emit(self.finishResult)  # Done
		


class MainWindow(QMainWindow):


	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)
	
		self.counter = 0
	
		layout = QVBoxLayout()
		
		self.l = QLabel("Start")
		b = QPushButton("DANGER!")
		b.pressed.connect(self.oh_no)
		
		self.tempPB = QProgressBar(self)
		self.tempPB.setMinimum(0)
		self.tempPB.setMaximum(100)
		self.tempPB.setFormat("Test " + '%p%')
		self.tempPB.setValue(0)
		self.tempPB.setTextVisible(True)
		self.tempPB.setAlignment(Qt.AlignCenter)
		self.defaulStyle = self.tempPB.styleSheet()
		print(self.defaulStyle)
		
	
		layout.addWidget(self.l)
		layout.addWidget(b)
		layout.addWidget(self.tempPB)
		
	
		w = QWidget()
		w.setLayout(layout)
	
		self.setCentralWidget(w)
	
		self.show()

		self.threadpool = QThreadPool()
		print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

		self.timer = QTimer()
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self.recurring_timer)
		self.timer.start()
	
	
	

	#time as HH:MM:SS.mm as timeobject, framerate as float
	def timeToFrames(self, t, frameRate):
		return floor(t.hour*60*60*60*frameRate + t.minute*60*60*frameRate + t.second*frameRate + t.microsecond/1000000 * frameRate)

	#time as string as "HH:MM:SS.mm"
	def stringToTime(self, timeString):
		return (datetime.strptime(timeString, "%H:%M:%S.%f"))
	
		
	def progress_fn(self, n):
		#print("%d%% done" % n)
		return n
	
	
	def getProcessPercent(self, process, frameRate, pySignalObj):
		for line in process.stdout:
			frameLine = re.search("^frame=.*fps=", line)
			durationLine = re.search("^  Duration: ", line)
			if (durationLine):
				dTimeString = re.findall("\d{1,2}:\d{2}:\d{2}.\d{2}", line)
				if (dTimeString):
					duration = self.stringToTime(dTimeString[0])
					durationFrames = self.timeToFrames(duration,frameRate)
			if (frameLine):
				frameString = re.findall("[0-9]+", line)
				if (frameString):
					#test for errors here
					try:
						self.worker.signals.progress.emit(int(frameString[0])/durationFrames * 100)
						#pySignalObj.emit(int(frameString[0])/durationFrames * 100)
					except:
						self.worker.signals.progress.emit(100)
						#pySignalObj.emit(100)
						traceback.print_exc()
						exctype, value = sys.exc_info()[:2]
						self.worker.signals.error.emit( (exctype, value, traceback.format_exc()) )
						break
					
					
					
	def execute_this_fn(self, path, codec, alpha, frameRate, progress_callback):
		#print(path)
		pyCompression = pyFFMEGCompress(path,codec,alpha,frameRate, self.worker)
		ffProcess = pyCompression.ffmpegCompress()
		#would be nicer to use the class method instead here but doesn't update only prints the final result
		progress_callback.emit(pyCompression.printProcess(ffProcess))
		#self.getProcessPercent(ffProcess, frameRate, progress_callback)

		return "Done."
 
	def print_output(self, s):
		print("Printing output "+ str(s))
		
	def thread_complete(self, r):
		print("THREAD COMPLETE! WITH ERROR " + str(r) )
	
	def errorPB(self, err, pb):
		pb.setStyleSheet("QProgressBar::chunk {background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #FF0350,stop: 0.4999 #FF0020,stop: 0.5 #FF0019,stop: 1 #FF0000 );border-radius: 3px; border: 1px solid #a60233;}QProgressBar{color:white}")#("QProgressBar::chunk { background-color: red; }")
		#pb.setStyleSheet("QProgressBar::chunk { background-color: red; }")
		pb.setFormat(pb.format()+" - Error")
	
	def resetProgressBar(self, pb, text):
		pb.setValue(0)
		pb.setFormat(text + ' %p%')
		pb.setStyleSheet(self.defaulStyle)
	
	def oh_no(self):
		self.resetProgressBar(self.tempPB,'Test')
		
		self.worker = Worker(self.execute_this_fn, 'H:\\VideoProjectsTemp\\FramesTest\\s01-01', 'utvideo', False, 24) # Any other args, kwargs are passed to the run function
		self.worker.signals.result.connect(self.print_output)
		self.worker.signals.finished.connect(self.thread_complete)
		#worker.signals.progress.connect(self.progress_fn)
		self.worker.signals.progress.connect(self.tempPB.setValue)
		
		#TRY TO FIGURE OUT HOW TO HANDLE ERRORS
		self.worker.signals.error.connect(lambda n: self.errorPB(n,self.tempPB))#,self.tempPB.setFormat))
		
		# Execute
		self.threadpool.start(self.worker) 

		
	def recurring_timer(self):
		self.counter +=1
		self.l.setText("Counter: %d" % self.counter)
	
	
app = QApplication([])
app.setStyle('Fusion')
window = MainWindow()
app.exec_()