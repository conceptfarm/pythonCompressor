#!/usr/bin/python3
# -*- coding: utf-8 -*-

#TODO:
#IF output name from file name then we need to raise error that things will be overwritten
#or do something else

import os
import traceback, sys
from PyQt5.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton, QApplication, QStyleFactory, QGridLayout, QSpacerItem, QSizePolicy, QProgressBar,QPlainTextEdit,QButtonGroup,QRadioButton )
from PyQt5.QtCore import Qt, QCoreApplication, QRect, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool
from subprocessClass import pyFFMEGCompress

'''
import re
import time


from datetime import datetime
from math import floor
'''

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
	#errorString = pyqtSignal(str)

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
		#self.kwargs['errorString_callback'] = self.signals.errorString
		

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
		self.nameFrom = 'Folder'
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
		
		self.groupBox = QButtonGroup(self)
				
		self.radio1 = QRadioButton('Output file name from Folder name',self)
		self.radio2 = QRadioButton('Output file name from File name',self)
		self.groupBox.addButton(self.radio1,1)
		self.groupBox.addButton(self.radio2,2)
		self.radio1.setChecked(True)
		
		self.gridLayout.addWidget(self.radio1, 2, 0, 1, 2)
		self.gridLayout.addWidget(self.radio2, 2, 2, 1, 2)
		
		self.groupBox.buttonClicked[int].connect(self.radioBtnState)

		
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
			
			self.gridLayout.addWidget(self.tempPB, i+3, 0, 1, 4)
			self.pbList.append(self.tempPB)
		
		
		self.errorLlb = QLabel("Output", self)
		self.gridLayout.addWidget(self.errorLlb, len(self.inList)+4, 0, 1, 4)
		
		self.errorText = QPlainTextEdit('',self)
		self.gridLayout.addWidget(self.errorText, len(self.inList)+5, 0, 1, 4)
		
		self.spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.gridLayout.addItem(self.spacerItem, len(self.inList)+6, 0, 1, 1)
		
		self.comboCodec.activated[str].connect(self.chooseCodec)
		self.comboAlpha.activated[str].connect(self.chooseAlpha)
		self.comboFrameRate.activated[str].connect(self.chooseFrameRate)
		
		self.setGeometry(300, 300, 750, 100)
		#self.gridLayout.setGeometry(QRect(19, 19, 581, 100))
		self.setWindowTitle('FFMpeg Python Compressor')
		self.show()
        
		self.threadpool = QThreadPool()
		self.threadpool.setMaxThreadCount(1)
		print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
    


	'''
	Button Functions
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

	def radioBtnState(self, text):
		switcher={
			1:'Folder',
			2:'File'
		}
		self.nameFrom = switcher.get(text,"Invalid day of week")
		#print(self.nameFrom)
	

	'''
	Execution Functions
	'''
	def execute_this_fn(self, path, codec, alpha, frameRate, progress_callback, errorFFMPEG_callback):
		#print(path)
		pyCompression = pyFFMEGCompress(path,codec,alpha,frameRate)
		ffProcess = pyCompression.ffmpegCompress()
		
		#with kwargs
		kwargs = {'progress_callback':progress_callback, 'errorFFMPEG_callback':errorFFMPEG_callback}
		pyCompression.printProcess(ffProcess, **kwargs)

		return pyCompression.debugString
 
	def printOutput(self, s):
		print("Printing output "+ str(s))
		
	def threadComplete(self, r):
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
	

	def compressPress(self):
		for i in range(len(self.pbList)):			
			self.resetProgressBar(self.pbList[i],self.inList[i])
			
			worker = Worker(self.execute_this_fn, self.inList[i], self.codec, self.alpha, self.frameRate) # Any other args, kwargs are passed to the run function
			#worker.signals.result.connect(self.printOutput)
			worker.signals.result.connect(self.errorText.appendPlainText)
			worker.signals.progress.connect(self.pbList[i].setValue)
			worker.signals.errorFFMPEG.connect(self.errorPB)
			worker.signals.error.connect(self.errorPB)
			worker.signals.finished.connect(self.threadComplete)
			#worker.signals.finished.connect(self.errorText.appendPlainText)
			
			# Execute
			self.threadpool.start(worker)


		
if __name__ == '__main__':
	

	dirList = []
	
	for arg in sys.argv:
		if os.path.isdir(arg) == True:
			#print(str(os.path.basename(arg)))
			dirList.append(arg)
	
	#sort the list , chech the code below make sure it's right
	dirList = sorted(dirList, key=lambda i: (os.path.basename(i)))
	
	QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
	QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
	
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	dim = app.desktop().screenGeometry()
	
	print("The screen resolution is ({} X {}):".format(dim.width(), dim.height()))
	print("logicalDpiX ", app.desktop().logicalDpiX())
	print("phyiscalDpiX ", app.desktop().physicalDpiX())
	
	# Enable High DPI display with PyQt5
	app.setAttribute(Qt.AA_EnableHighDpiScaling)
	if hasattr(QStyleFactory, 'AA_UseHighDpiPixmaps'):
		 app.setAttribute(Qt.AA_UseHighDpiPixmaps)
	
	ex = MainWindow(dirList)
	#print(ex.currentData(ex.comboCodec))
	#print(ex.currentData(ex.comboAlpha))
	#print(ex.currentData(ex.comboFrameRate))

	sys.exit(app.exec_())
