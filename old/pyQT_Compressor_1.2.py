#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton, QApplication, QStyleFactory,QGridLayout,QSpacerItem,QSizePolicy,QProgressBar)
from PyQt5.QtCore import Qt, QCoreApplication, QRect, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool

import os
import re
import time
import traceback, sys
from subprocessClass import pyFFMEGCompress
from datetime import datetime
from math import floor


TIME_LIMIT = 100

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
	errorFFMPEG = pyqtSignal(str)

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
		self.kwargs['errorFFMPEG_callback'] = self.signals.errorFFMPEG
		

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
		




class MainWindow(QWidget):
    
	def __init__(self, inList):
		super().__init__()
		self.inList = inList
		self.codec = 'utvideo'
		self.alpha = False
		self.frameRate = 24
		self.defaulStyle = ''
		self.initUI()
        
        
	def initUI(self):      

		#self.hbox = QVBoxLayout(self)
		self.gridLayout = QGridLayout(self)
		self.gridLayout.setContentsMargins(11, 11, 11, 11)
        
		self.lblCodec = QLabel("Codec", self)
		self.lblAlpha = QLabel("Alpha", self)
		self.lblFrameRate = QLabel("Frame Rate", self)
		self.gridLayout.addWidget(self.lblCodec, 0, 0, 1, 1)
		self.gridLayout.addWidget(self.lblAlpha, 0, 1, 1, 1)
		self.gridLayout.addWidget(self.lblFrameRate, 0, 2, 1, 1)
		
		
		self.comboCodec = QComboBox(self)
		self.comboCodec.setMinimumWidth(80)
		self.comboCodec.addItem("UT Video")

		self.comboAlpha = QComboBox(self)
		self.comboAlpha.setMinimumWidth(80)
		self.comboAlpha.addItem("No Alpha")
		self.comboAlpha.addItem("with Alpha")
		
		self.comboFrameRate = QComboBox(self)
		self.comboFrameRate.setMinimumWidth(80)
		self.comboFrameRate.addItem("24.00")
		self.comboFrameRate.addItem("30.00")
		
		self.buttonCompress = QPushButton("Compress", self)
		self.buttonCompress.clicked[bool].connect(self.compressPress)

		self.gridLayout.addWidget(self.comboCodec,1, 0, 1, 1)
		self.gridLayout.addWidget(self.comboAlpha, 1, 1, 1, 1)
		self.gridLayout.addWidget(self.comboFrameRate, 1, 2, 1, 1)
		self.gridLayout.addWidget(self.buttonCompress, 1, 3, 1, 1)
		
		self.pbList = []
		
		for i in range(len(self.inList)):
			self.tempPB = QProgressBar(self)
			self.tempPB.setMinimum(0)
			self.tempPB.setMaximum(100)
			self.tempPB.setTextVisible(True)
			self.tempPB.setFormat(str(self.inList[i])+" %p%")
			self.tempPB.setAlignment(Qt.AlignCenter)
			self.tempPB.setValue(0)
			if i==0:
				self.defaulStyle = self.tempPB.styleSheet()
			
			self.gridLayout.addWidget(self.tempPB, i+2, 0, 1, 4)
			self.pbList.append(self.tempPB)
		
		spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.gridLayout.addItem(spacerItem, len(self.inList)+2, 0, 1, 1)
		
		self.comboCodec.activated[str].connect(self.chooseCodec)
		self.comboAlpha.activated[str].connect(self.chooseAlpha)
		self.comboFrameRate.activated[str].connect(self.chooseFrameRate)
		
		self.setGeometry(300, 300, 390, 100)
		self.gridLayout.setGeometry(QRect(19, 19, 581, 94))
		self.setWindowTitle('FFMpeg Python Compressor')
		self.show()
        
		self.threadpool = QThreadPool()
		print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
    


	'''
	Button functions
	'''
	def chooseAlpha(self, text):
		switcher={
			"No Alpha":False,
			"with Alpha":True
		}
		self.alpha = switcher.get(text,"Invalid day of week")
		#print (self.alpha)

	def chooseCodec(self, text):
		switcher={
			"UT Video":"utvideo"
		}
		self.codec =  switcher.get(text,"Invalid day of week")
		#print (self.codec)
		
	def chooseFrameRate(self, text):
		self.frameRate =  float(text)
		#print (self.frameRate)
	
	
	def currentData(self, widget):
		return widget.currentText() 

	def pushTest(self):
		print("pressed")
		for pb in self.pbList:
			count = 0
			while count < TIME_LIMIT:
				count += 2
				time.sleep(0.5)
				pb.setValue(count)
	
	
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
						#self.worker.signals.progress.emit(int(frameString[0])/durationFrames * 100)
						
						pySignalObj.emit(int(frameString[0])/durationFrames * 100)
					except:
						#self.worker.signals.progress.emit(100)
						print('setting to -1')
						raise Exception ('error in ffmepg compression')
						#pySignalObj.emit(-1)
						#traceback.print_exc()
						#exctype, value = sys.exc_info()[:2]
						#self.worker.signals.error.emit( (exctype, value, traceback.format_exc()) )
						#self.worker.signals.error.emit( ('error') )
						break


	def execute_this_fn(self, path, codec, alpha, frameRate, progress_callback, errorFFMPEG_callback):
		#print(path)
		pyCompression = pyFFMEGCompress(path,codec,alpha,frameRate)
		ffProcess = pyCompression.ffmpegCompress()
		
		#with kwargs
		kwargs = {'progress_callback':progress_callback, 'errorFFMPEG_callback':errorFFMPEG_callback}
		pyCompression.printProcess(ffProcess, **kwargs)
		
		#would be nicer to use the class method instead here but doesn't update only prints the final result
		#progress_callback.emit(pyCompression.printProcess(ffProcess))
		'''
		#self.getProcessPercent(ffProcess, frameRate, progress_callback, errorFFMPEG_callback)
		for line in ffProcess.stdout:
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
						#self.worker.signals.progress.emit(int(frameString[0])/durationFrames * 100)
						progress_callback.emit(int(frameString[0])/durationFrames * 100)
						#pySignalObj.emit(int(frameString[0])/durationFrames * 100)
					except:
						#self.worker.signals.progress.emit(100)
						#print('setting to -1')
						errorFFMPEG_callback.emit(path + " %p%")
						#raise Exception ('error in ffmepg compression')
						#pySignalObj.emit(-1)
						#traceback.print_exc()
						#exctype, value = sys.exc_info()[:2]
						#self.worker.signals.error.emit( (exctype, value, traceback.format_exc()) )
						#self.worker.signals.error.emit( ('error') )
						break
		'''
		return "Done."
 
	def print_output(self, s):
		print("Printing output "+ str(s))
		
	def thread_complete(self, r):
		self.i = self.i + 1
		print("THREAD COMPLETE! WITH ERROR " + str(r) )

	def errorPB(self, err):
		for o in self.pbList:
			if o.format() == err:
				o.setValue(100)
				o.setStyleSheet("QProgressBar::chunk {background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #FF0350,stop: 0.4999 #FF0020,stop: 0.5 #FF0019,stop: 1 #FF0000 );border-radius: 3px; border: 1px solid #a60233;}QProgressBar{color:white}")#("QProgressBar::chunk { background-color: red; }")
				#pb.setStyleSheet("QProgressBar::chunk { background-color: red; }")
				o.setFormat(o.format()+" - Error")
				
	def resetProgressBar(self, pb, text):
		pb.setValue(0)
		pb.setFormat(text + ' %p%')
		pb.setStyleSheet(self.defaulStyle)
	
	#figure out how to queue tasks better
	def compressPress(self):
		self.i = 0
		for self.i in range(len(self.pbList)):
			i = self.i
			print(i)
			print(self.i)
			#print(self.pbList[i].format())
			#print(self.pbList[i])
			#print(self.inList[i])
			
			self.resetProgressBar(self.pbList[i],self.inList[i])
			

			worker = Worker(self.execute_this_fn, self.inList[i], self.codec, self.alpha, self.frameRate) # Any other args, kwargs are passed to the run function
			worker.signals.result.connect(self.print_output)
			
			#worker.signals.progress.connect(self.progress_fn)
			worker.signals.progress.connect(self.pbList[i].setValue)
			#worker.signals.errorFFMPEG.connect(lambda n: self.errorPB(n,self.pbList[i]))
			worker.signals.errorFFMPEG.connect(self.errorPB)
			worker.signals.finished.connect(self.thread_complete)
			
			#This sort of worked, lambda function evals at the time of error not at the time of assignment
			#so the i is not the actual i of the erroring signal
			#worker.signals.error.connect(lambda n: self.errorPB(n,self.pbList[i]))#,self.tempPB.setFormat))
			
			# Execute
			self.threadpool.start(worker)

			#self.threadpool.waitForDone()



		
if __name__ == '__main__':
	

	dirList = []
	
	for arg in sys.argv:
		if os.path.isdir(arg) == True:
			#print(str(os.path.basename(arg)))
			dirList.append(arg)
	
	#sort the list , chech the code below make sure it's right
	dirList = sorted(dirList, key=lambda i: (os.path.basename(i)))
	
	#QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
	#QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
	
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	dim = app.desktop().screenGeometry()
	
	print("The screen resolution is ({} X {}):".format(dim.width(), dim.height()))
	print("logicalDpiX ", app.desktop().logicalDpiX())
	print("phyiscalDpiX ", app.desktop().physicalDpiX())
	
	# Enable High DPI display with PyQt5
	# app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
	# if hasattr(QStyleFactory, 'AA_UseHighDpiPixmaps'):
		# app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
	
	ex = MainWindow(dirList)
	#print(ex.currentData(ex.comboCodec))
	#print(ex.currentData(ex.comboAlpha))
	#print(ex.currentData(ex.comboFrameRate))

	sys.exit(app.exec_())
