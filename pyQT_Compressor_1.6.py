#!/usr/bin/python3
# -*- coding: utf-8 -*-

#TODO:
#need to check for same name collision
#check on high dpi monitors
#interface still glitchy
#cancel ffmpeg process 
#lock interface
#	disable checkboxes, disable delete buttons - maybe disable everything except progress bar and show log button
'''
	error:
	Error while decoding stream #0:0: Invalid data found when processing input
	Error while decoding stream #0:0: Invalid data found when processing input-0.0kbits/s speed=N/A
	    Last message repeated 13 times
	Cannot determine format of input stream 0:0 after EOF
	Error marking filters as finished
	Conversion failed!

	success:
	video:44611kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.013489%
	Output stream .+ (video): [0-9][0-9]+ packets muxed \([0-9][0-9]+ bytes\)
'''
import os
import traceback, sys
import platform

from PyQt5.QtWidgets import (QWidget, QStyle,QLabel, QComboBox, QPushButton, QApplication, QStyleFactory, QGridLayout, QVBoxLayout, QLayout, QSizePolicy, QProgressBar, QPlainTextEdit, QButtonGroup, QRadioButton, QCheckBox, QFrame, QSpacerItem )
from PyQt5.QtCore import Qt, QCoreApplication, QRect, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QSize
from PyQt5.QtGui import QIcon,QPixmap
from subprocessClass import pyFFMEGCompress
import time



# Use NSURL as a workaround to pyside/Qt4 behaviour for dragging and dropping on OSx
op_sys = platform.system()
if op_sys == 'Darwin':
	from Foundation import NSURL

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
	finished = pyqtSignal(tuple)
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
		#self.nameFrom = nameFrom
		#self.index = index
		
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
			self.finishResult = True
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit( (exctype, value, traceback.format_exc()) )
		else:
			self.signals.result.emit(result[0])  # Return the result of the processing
		finally:
			self.signals.finished.emit(result)  # Done
		

class MainWindow(QWidget):
    
	def __init__(self, inList):
		super().__init__()
		self.inList = inList
		self.nameFrom = 'Folder'
		self.codec = 'utvideo'
		self.alpha = False
		self.frameRate = 24
		self.defaulStyle = ''
		
		self.okIcon = QIcon(self.style().standardIcon(QStyle.SP_CustomBase))
		self.okPix = QPixmap(self.okIcon.pixmap(QSize(13, 13)))
		self.goodIcon = QIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
		self.goodPix = QPixmap(self.goodIcon.pixmap(QSize(13, 13)))
		self.badIcon = QIcon(self.style().standardIcon(QStyle.SP_MessageBoxCritical))
		self.badPix = QPixmap(self.badIcon.pixmap(QSize(13, 13)))
		self.processingIcon = QIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
		self.processingPix = QPixmap(self.processingIcon.pixmap(QSize(13, 13)))
		self.removeIcon = QIcon(self.style().standardIcon(QStyle.SP_DockWidgetCloseButton))
		self.removePix = QPixmap(self.removeIcon.pixmap(QSize(19, 19)))
		self.folderIcon = QIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
		self.folderPix = QPixmap(self.folderIcon.pixmap(QSize(19, 19)))
		
		self.pbList = []
		self.chList = []
		self.lblList = []
		self.rmbList = []
		#self.newFolders = []
		self.initUI()

	def initUI(self):
		self.resize(720, 300)
		self.setWindowTitle('FFMpeg Python Compressor')
		self.verticalLayout = QVBoxLayout(self)
		self.verticalLayout.setContentsMargins(11, 11, 11, 11)
		self.verticalLayout.setSpacing(11)
		
		#COMBOBOX LABELS
		self.gridLayoutControlls = QGridLayout()
		self.codecLabel = QLabel('Codec', self)
		self.codecLabel.setMinimumHeight(13)
		self.alphaLabel = QLabel('Alpha' , self)
		self.alphaLabel.setMinimumHeight(13)
		self.frameRateLabel = QLabel('Frame Rate' , self)
		self.frameRateLabel.setMinimumHeight(13)
		self.gridLayoutControlls.addWidget(self.codecLabel, 0, 0, 1, 1)
		self.gridLayoutControlls.addWidget(self.alphaLabel, 0, 1, 1, 1)
		self.gridLayoutControlls.addWidget(self.frameRateLabel, 0, 2, 1, 1)
		
		#COMBOBOXES AND COMPRESS BUTTON
		self.codecComboBox = QComboBox(self)
		self.codecComboBox.setMinimumSize(80,23)
		self.codecComboBox.addItem("UT Video")
		self.codecComboBox.activated[str].connect(self.chooseCodec)
		
		self.alphaComboBox = QComboBox(self)
		self.alphaComboBox.setMinimumSize(80,23)
		self.alphaComboBox.addItem("No Alpha")
		self.alphaComboBox.addItem("with Alpha")
		self.alphaComboBox.activated[str].connect(self.chooseAlpha)
		
		self.frameRateComboBox = QComboBox(self)
		self.frameRateComboBox.setMinimumSize(80,23)
		self.frameRateComboBox.addItem("24.00")
		self.frameRateComboBox.addItem("30.00")
		self.frameRateComboBox.activated[str].connect(self.chooseFrameRate)
		
		self.compressButton = QPushButton('Compress', self)
		self.compressButton.setMinimumSize(80,23)
		self.compressButton.clicked[bool].connect(self.compressPress)
			
		self.gridLayoutControlls.addWidget(self.codecComboBox, 1, 0, 1, 1)
		self.gridLayoutControlls.addWidget(self.alphaComboBox, 1, 1, 1, 1)
		self.gridLayoutControlls.addWidget(self.frameRateComboBox, 1, 2, 1, 1)
		self.gridLayoutControlls.addWidget(self.compressButton, 1, 3, 1, 1)
			
		#RADIO BUTTON GROUP
		self.groupBox = QButtonGroup(self)
		self.radio1 = QRadioButton('Output file name from Folder name', self)
		self.radio1.setMinimumSize(80,25)
		self.radio2 = QRadioButton('Output file name from File name', self)
		self.radio2.setMinimumSize(80,25)
		self.radio1.setChecked(True)
		self.groupBox.addButton(self.radio1,1)
		self.groupBox.addButton(self.radio2,2)
		self.groupBox.buttonClicked[int].connect(self.radioBtnState)
		
		self.gridLayoutControlls.addWidget(self.radio1, 2, 0, 1, 2)
		self.gridLayoutControlls.addWidget(self.radio2, 2, 2, 1, 2)
		
		#LINE
		self.line = QFrame(self)
		self.line.setLineWidth(2)
		self.line.setMinimumHeight(3)
		self.line.setFrameShape(QFrame.HLine)
		self.line.setFrameShadow(QFrame.Sunken)
		
		self.gridLayoutControlls.addWidget(self.line, 3, 0, 1, 4)
		
		#PROGRESS BAR 
		self.gridLayoutProgress = QGridLayout()
		self.gridLayoutProgress.setVerticalSpacing(11)
		self.gridLayoutProgress.setHorizontalSpacing(6)
		self.gridLayoutProgress.setSizeConstraint(QLayout.SetNoConstraint)
		
		self.removeGroupBox = QButtonGroup(self)
		self.addProgressBarUI(self.inList)			
		self.removeGroupBox.buttonClicked[int].connect(self.removeButtonClicked)

		#ADD MORE AREA
		self.gridLayoutAddMore = QGridLayout()
		self.gridLayoutAddMore.setContentsMargins(0, 0, 0, 0)
		
		self.dragAndDropLabel_1 = QLabel("Drag and Drop folders here", self)
		self.dragAndDropLabel_1.setMinimumSize(QSize(120, 40))
		self.dragAndDropLabel_1.setAlignment(Qt.AlignCenter)
		
		self.dragAndDropLabel_2 = QLabel("", self)
		self.dragAndDropLabel_2.setFixedSize(QSize(20, 40))
		self.dragAndDropLabel_2.setAlignment(Qt.AlignCenter)
		self.dragAndDropLabel_2.setPixmap(self.folderPix)
		
		sI = QSpacerItem(40, 40,QSizePolicy.Expanding, QSizePolicy.Minimum)
		sI2 = QSpacerItem(40, 40,QSizePolicy.Expanding, QSizePolicy.Minimum)
		
		self.gridLayoutAddMore.addItem(sI, 1, 0, 1, 1)
		self.gridLayoutAddMore.addWidget(self.dragAndDropLabel_2, 1, 1, 1, 1)
		self.gridLayoutAddMore.addWidget(self.dragAndDropLabel_1, 1, 2, 1, 1)
		self.gridLayoutAddMore.addItem(sI2, 1, 3, 1, 1)
		
		#DEBUG AREA
		self.gridLayoutDebug = QGridLayout()
		self.line_2 = QFrame(self)
		self.line_2.setLineWidth(2)
		self.line_2.setFrameShape(QFrame.HLine)
		self.line_2.setFrameShadow(QFrame.Sunken)
		
		self.hideShowLog = QPushButton('Show Log',self)
		self.hideShowLog.setCheckable(True)
		self.hideShowLog.clicked[bool].connect(self.showDebugLog)
		#self.hideShowLog.setMinimumSize(QSize(0, 20))
		
		self.logText = QPlainTextEdit('',self)
		self.logText.setReadOnly(True)
		self.logText.hide()
		
		self.spacerItem = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		
		self.gridLayoutDebug.addWidget(self.line_2, 0, 0, 1, 1)
		self.gridLayoutDebug.addWidget(self.hideShowLog, 1, 0, 1, 1)
		self.gridLayoutDebug.addWidget(self.logText, 2, 0, 1, 1)
		self.gridLayoutDebug.addItem(self.spacerItem, 3, 0, 1, 1)
		
		self.verticalLayout.addLayout(self.gridLayoutControlls)
		self.verticalLayout.addLayout(self.gridLayoutProgress)
		self.verticalLayout.addLayout(self.gridLayoutAddMore)
		self.verticalLayout.addLayout(self.gridLayoutDebug)
		
		# Enable dragging and dropping onto the GUI
		self.setAcceptDrops(True)
		
		#QtCore.QMetaObject.connectSlotsByName(self)
		self.show()
		self.setMinimumSize(self.size())
		
		self.threadpool = QThreadPool()
		self.threadpool.setMaxThreadCount(1)
		print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
    
	
	
	'''
	Progress bar populate function
	'''
	def addProgressBarUI(self, arr):
		pbCount = len(self.pbList)
		for i in range(len(arr)):
			tempCheckBox = QCheckBox(self)
			tempCheckBox.setChecked(True)
			tempCheckBox.setMinimumSize(14,21)
			
			tempRemoveButton = QPushButton(self)
			tempRemoveButton.setIcon(self.removeIcon)
			tempRemoveButton.setFlat(True)
			tempRemoveButton.setIconSize(QSize(19,19))
			tempRemoveButton.setFixedSize(QSize(19,21))
			
			
			tempPB = QProgressBar(self)
			tempPB.setMinimumSize(50,21)
			tempPB.setMinimum(0)
			tempPB.setMaximum(100)
			tempPB.setTextVisible(True)
			tempPB.setFormat(str(arr[i])+" %p%")
			tempPB.setAlignment(Qt.AlignCenter)
			tempPB.setValue(0)
			if i==0:
				self.defaulStyle = tempPB.styleSheet()
			
			tempStatusLabel = QLabel(self)			
			tempStatusLabel.setPixmap(self.okPix)
			tempStatusLabel.setMinimumSize(13,21)
			
			self.gridLayoutProgress.addWidget(tempCheckBox, pbCount+i, 0, 1, 1)
			self.gridLayoutProgress.addWidget(tempPB, pbCount+i, 1, 1, 1)
			self.gridLayoutProgress.addWidget(tempStatusLabel, pbCount+i, 2, 1, 1)
			self.gridLayoutProgress.addWidget(tempRemoveButton, pbCount+i, 3, 1, 1)
			self.removeGroupBox.addButton(tempRemoveButton, pbCount+i)
			
			self.pbList.append(tempPB)
			self.chList.append(tempCheckBox)
			self.lblList.append(tempStatusLabel)
			self.rmbList.append(tempRemoveButton)
	
		
	'''
	Drag+Drop Functions
	'''
	# The following three methods set up dragging and dropping for the app
	def dragEnterEvent(self, e):
		if e.mimeData().hasUrls:
			e.accept()
		else:
			e.ignore()

	def dragMoveEvent(self, e):
		if e.mimeData().hasUrls:
			e.accept()
		else:
			e.ignore()

	def dropEvent(self, e):
		"""
		Drop files directly onto the widget
		File locations are stored in fname
		:param e:
		:return:
		"""
		newFolders = []
		if e.mimeData().hasUrls:
			e.setDropAction(Qt.CopyAction)
			e.accept()
			# Workaround for OSx dragging and dropping
			for url in e.mimeData().urls():
				if op_sys == 'Darwin':
					#check for dir here as well
					fname = str(NSURL.URLWithString_(str(url.toString())).filePathURL().path())
				else:
					fname = str(url.toLocalFile())
					if os.path.isdir(fname) == True:
						newFolders.append(fname)
					#print(fname)

			#self.fname = fname
			#print(self.fname)
			#self.load_image()
			self.addNewFolders(newFolders)
			self.inList = self.inList + newFolders
		else:
			e.ignore()
	

	def addNewFolders(self, newFolders):
		self.addProgressBarUI(newFolders)
		self.setMinimumHeight(self.height()+len(newFolders)*32)
		#self.resize(self.width(),self.height()+200)
		self.update()
		self.adjustSize()
		self.setMinimumSize(self.size())
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
	
	def removeButtonClicked(self, i):
		#print('remove trigger on id '+str(i))
		
		#self.pbList.pop(i)
		'''
		self.pbList[i].hide()
		self.chList[i].setChecked(False)
		self.chList[i].hide()
		self.lblList[i].hide()
		self.rmbList[i].hide()
		'''
		print(self.gridLayoutProgress.rowCount())
		self.pbList[i].setParent(None)
		self.chList[i].setChecked(False)
		self.chList[i].setParent(None)
		self.lblList[i].setParent(None)
		self.rmbList[i].setParent(None)
		
		self.removeGroupBox.removeButton(self.rmbList[i])

		self.gridLayoutProgress.removeWidget(self.pbList[i])
		self.gridLayoutProgress.removeWidget(self.chList[i])
		self.gridLayoutProgress.removeWidget(self.lblList[i])
		self.gridLayoutProgress.removeWidget(self.rmbList[i])
		self.gridLayoutProgress.invalidate()
		self.gridLayoutProgress = QGridLayout()
		self.gridLayoutProgress.setVerticalSpacing(11)
		self.gridLayoutProgress.setHorizontalSpacing(6)
		self.gridLayoutProgress.setSizeConstraint(QLayout.SetDefaultConstraint)
		self.verticalLayout.insertLayout(1,self.gridLayoutProgress)
		
		print(self.gridLayoutProgress.rowCount())
		'''
		print(self.pbList)
		print(self.chList)
		print(self.lblList)
		print(self.rmbList)
		'''
		
		self.pbList.pop(i)
		self.chList.pop(i)
		self.lblList.pop(i)
		self.rmbList.pop(i)
		self.inList.pop(i)		
		

		#clear the gridLayout
		for j in reversed(range(len(self.pbList))):
			self.pbList[j].setParent(None)
			self.chList[j].setParent(None)
			self.lblList[j].setParent(None)
			self.rmbList[j].setParent(None)
		
		
		#reorder the gridLayout
		for j in range(len(self.pbList)):
			self.gridLayoutProgress.addWidget(self.chList[j], j, 0, 1, 1)
			self.gridLayoutProgress.addWidget(self.pbList[j], j, 1, 1, 1)
			self.gridLayoutProgress.addWidget(self.lblList[j], j, 2, 1, 1)
			self.gridLayoutProgress.addWidget(self.rmbList[j], j, 3, 1, 1)
			self.removeGroupBox.setId(self.rmbList[j],j)

		
		
		self.setMinimumHeight(self.height()-30)
		#self.setMinimumHeight(100)
		self.adjustSize()
		self.setMinimumSize(self.size())
		print(self.gridLayoutProgress.rowCount())
		#self.correctSize()
		'''
		for j in range(len(self.removeGroupBox.buttons())):
			button = self.removeGroupBox.buttons()[j]
			#print(button)
			#print('original id '+str(self.removeGroupBox.id(button)))
			#print('new id '+str(j))
			self.removeGroupBox.setId(button,j)
		'''
	
	def correctSize(self):
			self.logText.show()
			self.gridLayoutDebug.removeItem(self.spacerItem)
			self.adjustSize()
			self.setMinimumSize(self.size())
			self.repaint()
			self.gridLayoutDebug.addItem(self.spacerItem)
			self.logText.hide()
			self.setMinimumHeight(100)
			self.adjustSize()
			self.setMinimumSize(self.size())
	
	def showDebugLog(self, bol):
		if bol:
			self.logText.show()
			self.hideShowLog.setText('Hide Log')
			self.gridLayoutDebug.removeItem(self.spacerItem)
			self.adjustSize()
			#self.resize(self.width(), self.height()+80)
			self.setMinimumSize(self.size())
		else:
			self.gridLayoutDebug.addItem(self.spacerItem)
			self.logText.hide()
			self.hideShowLog.setText('Show Log')
			self.setMinimumHeight(100)
			self.adjustSize()
			self.setMinimumSize(self.size())
			#self.resize(self.width(), 100)
			#self.setGeometry(0,0,self.width(),100)
	
	'''
	Execution Functions
	'''
	def execute_this_fn(self, path, codec, alpha, frameRate, nameFrom, i, progress_callback, errorFFMPEG_callback):
		#print(path)
		pyCompression = pyFFMEGCompress(path, codec, alpha, frameRate, nameFrom)
		ffProcess = pyCompression.ffmpegCompress()
		self.lblList[i].setPixmap(self.processingPix)
		
		#with kwargs
		kwargs = {'progress_callback':progress_callback, 'errorFFMPEG_callback':errorFFMPEG_callback}
		pyCompression.printProcess(ffProcess, **kwargs)

		return (pyCompression.debugString,pyCompression.error,i)
 
	def printOutput(self, s):
		print("Printing output "+ str(s))
		
	def threadComplete(self, r):
		#print("THREAD COMPLETE! WITH ERROR " + str(r[2]) )
		if r[1]==False:
			self.lblList[r[2]].setPixmap(self.goodPix)
			self.pbList[r[2]].setStyleSheet("QProgressBar::chunk {background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #44dd14,stop: 0.4999 #39c10f,stop: 0.5 #39c10f,stop: 1 #39c10f );border-radius: 3px; border: 1px solid #29880b;}QProgressBar{color:white}")

	def errorPB(self, err):
		for i in range(len(self.pbList)):
			if self.pbList[i].format() == err:
				self.pbList[i].setValue(100)
				self.pbList[i].setStyleSheet("QProgressBar::chunk {background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #FF0350,stop: 0.4999 #FF0020,stop: 0.5 #FF0019,stop: 1 #FF0000 );border-radius: 3px; border: 1px solid #a60233;}QProgressBar{color:white}")
				self.pbList[i].setFormat(self.pbList[i].format()+" - Error")
				self.chList[i].setChecked(False)
				self.lblList[i].setPixmap(self.badPix)
				
	def resetProgressBar(self, pb, text, lbl):
		pb.setValue(0)
		pb.setFormat(text + ' %p%')
		pb.setStyleSheet(self.defaulStyle)
		lbl.setPixmap(self.okPix)
	

	def compressPress(self):
		for i in range(len(self.pbList)):				
			if self.chList[i].isChecked():
				self.resetProgressBar(self.pbList[i],self.inList[i],self.lblList[i])
				
				worker = Worker(self.execute_this_fn, self.inList[i], self.codec, self.alpha, self.frameRate, self.nameFrom, i) # Any other args, kwargs are passed to the run function
				#worker.signals.result.connect(self.printOutput)
				worker.signals.result.connect(self.logText.appendPlainText)
				worker.signals.progress.connect(self.pbList[i].setValue)
				worker.signals.errorFFMPEG.connect(self.errorPB)
				worker.signals.error.connect(self.errorPB)
				worker.signals.finished.connect(self.threadComplete)
				#worker.signals.finished.connect(self.logText.appendPlainText)
				
				# Execute
				self.threadpool.start(worker)


if __name__ == '__main__':
	#dirList = []
	dirList = ['H:\VideoProjectsTemp\FramesTest\s01-01','H:\VideoProjectsTemp\FramesTest\s01-02','H:\VideoProjectsTemp\FramesTest\s01-03']
	
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
	sys.exit(app.exec_())
