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
import subprocess
import time
import configparser
from typing import Optional, Union, Any, List

# QtPy
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Custom
from lib.subprocessClass import pyFFMEGCompress
from lib.DarkPalette import QtDarkPalette
from lib.Delegates import RemoveButton, IconDelegate, ProgressDelegate, CheckboxDelegate
from lib.Threading import Worker, Callbacks
from logging.LogTextEdit import LogPlainTextEdit
from lib.ConfigDialogClass import ConfigDialog

PALETTE = QtDarkPalette()
INI_PATH: str = os.path.join(os.path.dirname(__file__),'pyFFMpegCompressorSettings.ini')

# Use NSURL as a workaround to pyside/Qt4 behaviour for dragging and dropping on OSx
op_sys = platform.system()
if op_sys == 'Darwin':
	from Foundation import NSURL
		
class MainWindow(QWidget):
	
	def __init__(self, exportDir: str, ffmpegPath: str, droppedFiles: list):
		super().__init__()
		self.exportDir: str = exportDir
		self.ffmpegPath: str = ffmpegPath
		self.droppedFiles: list = droppedFiles
		self.nameFrom: str = 'Folder'
		self.codec: str = 'ProRes'
		self.alpha: bool = False
		self.frameRate: float = 24.0
		
		# File process columns
		self.cbColumn = 0
		self.fileColumn = 1
		self.iconColumn = 2
		self.pbColumn = 3
		self.btnColumn = 4

		self.folderIcon = QIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
		self.folderPix = QPixmap(self.folderIcon.pixmap(QSize(19, 19)))

		self.processData: list = []
		self.mutex = QMutex()
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
		self.codecComboBox.addItems(["ProRes","UTVideo","HAP","H.264","H.265"])
		self.codecComboBox.setCurrentIndex(0)
		self.codecComboBox.activated[str].connect(self.chooseCodec)
		
		self.alphaComboBox = QComboBox(self)
		self.alphaComboBox.setMinimumSize(80,23)
		self.alphaComboBox.addItem("No Alpha")
		self.alphaComboBox.addItem("with Alpha")
		self.alphaComboBox.activated[str].connect(self.chooseAlpha)
		
		self.frameRateComboBox = QComboBox(self)
		self.frameRateComboBox.setMinimumSize(80,23)
		self.frameRateComboBox.addItems(["23.976","24","25","29.98","30","47.952","48","59.96","60"])
		self.frameRateComboBox.setCurrentIndex(1)
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
		self.gridLayoutProgress.setContentsMargins(-1, -1, -1, 8)
		self.gridLayoutProgress.setSpacing(6)
		self.gridLayoutProgress.setObjectName('table_gl')
		
		self.w = QTableWidget(0,5)
		self.w.setObjectName('table')
		self.w.setSelectionMode(QAbstractItemView.NoSelection)
		self.w.setState(QAbstractItemView.NoState)

		self.progDelegate = ProgressDelegate(self.w)
		self.iconDelegate = IconDelegate(self.w)
		self.cbDelegate = CheckboxDelegate(self.w)
		self.w.setItemDelegateForColumn(self.iconColumn, self.iconDelegate)
		self.w.setItemDelegateForColumn(self.pbColumn, self.progDelegate)
		self.w.setItemDelegateForColumn(self.cbColumn,self.cbDelegate)
		self.w.horizontalHeader().setSectionResizeMode(self.fileColumn, QHeaderView.Stretch)
		self.w.horizontalHeader().hide()
		self.w.verticalHeader().hide()
		self.w.setColumnWidth(self.cbColumn, 10)
		self.w.setColumnWidth(self.iconColumn, 10)
		self.w.setColumnWidth(self.pbColumn, 250)
		self.w.setColumnWidth(self.btnColumn, 40)
		
		self.gridLayoutProgress.addWidget(self.w, 0, 0, 1, 1)	

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
		
		self.exploreOutputBtn = QPushButton('Explore Output',self)
		self.exploreOutputBtn.clicked[bool].connect(self.exploreOutput)

		self.hideShowLog = QPushButton('Show Log',self)
		self.hideShowLog.setCheckable(True)
		self.hideShowLog.clicked[bool].connect(self.showDebugLog)
		#self.hideShowLog.setMinimumSize(QSize(0, 20))
		
		self.logText = LogPlainTextEdit(self)
		self.logText.setReadOnly(True)
		self.logText.hide()
		self.logText.setMonospaceFont()
		
		self.spacerItem = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		
		self.gridLayoutDebug.addWidget(self.line_2, 0, 0, 1, 1)
		self.gridLayoutDebug.addWidget(self.exploreOutputBtn, 1, 0, 1, 1)
		self.gridLayoutDebug.addWidget(self.hideShowLog, 2, 0, 1, 1)
		self.gridLayoutDebug.addWidget(self.logText, 3, 0, 1, 1)
		self.gridLayoutDebug.addItem(self.spacerItem, 4, 0, 1, 1)
		
		self.verticalLayout.addLayout(self.gridLayoutControlls)
		self.verticalLayout.addLayout(self.gridLayoutProgress)
		self.verticalLayout.addLayout(self.gridLayoutAddMore)
		self.verticalLayout.addLayout(self.gridLayoutDebug)
		
		# Enable dragging and dropping onto the GUI
		self.setAcceptDrops(True)
		
		#QtCore.QMetaObject.connectSlotsByName(self)
		self.show()
		self.setMinimumSize(self.size())
		self.addFilesToView(self.droppedFiles, self.w)
		
		self.threadpool = QThreadPool()
		self.threadpool.setMaxThreadCount(1)
		print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
	
	
	######################
	## FUNCTIONS        ##
	######################

	def addFilesToView(self, files, view):
		'''
		Progress bar populate function
		'''
		existingRows = view.rowCount()
		for r, file in enumerate(files):
			newRow = r + existingRows
			
			# checkbox
			it_cb = QTableWidgetItem()
			it_cb.setTextAlignment(Qt.AlignCenter)
			it_cb.setData(Qt.UserRole+1000, True)

			# file name
			it_file = QTableWidgetItem(file)
			
			# status icon
			it_id = QTableWidgetItem()
			it_id.setData(Qt.UserRole+1001, 'empty')
			
			# progress bar
			it_progress = QTableWidgetItem()
			it_progress.setData(Qt.UserRole+1000, 0)
			
			# remove button
			it_button = QTableWidgetItem()
						
			view.insertRow(view.rowCount())
			
			for c, item in enumerate((it_cb, it_file, it_id, it_progress, it_button)):
				view.setItem(newRow, c, item)
				
				# No item flag for everything but checkbox and progress
				if c != self.cbColumn and c != self.btnColumn: 
					item.setFlags(Qt.NoItemFlags)
				
				removeButton = RemoveButton(self.w)
				removeButton.clicked.connect(self.removeRow)
				view.setCellWidget(newRow, 4, removeButton)
			
			newTableHeight = self.w.rowCount() * (self.w.rowHeight(0)+1)
			self.w.setFixedHeight(newTableHeight)
			self.setMinimumHeight((self.height() + newTableHeight))
			self.setMinimumHeight(100)
			self.adjustSize()
			self.setMinimumSize(self.size())
		
	def setPBData(self, data:tuple):
		'''
		Sets the process bar 
		data: tuple (row: int, process %: int)
		'''
		row, percent = data
		self.w.item(row,self.pbColumn).setData(Qt.UserRole+1000, percent)

	def setIconData(self, data: tuple):
		row , icon = data
		self.w.item(row,self.iconColumn).setData(Qt.UserRole+1001, icon)

	def setEnabledControlls(self, state):
		'''
		Enables/Disables controls
		'''
		affectedControlTypes = ['QLabel', 'QComboBox', 'QPushButton', 'QRadioButton', 'QTableWidget']

		for child in self.children():
			if type(child).__name__ in affectedControlTypes:
				child.setEnabled(state)
		self.setAcceptDrops(state)
	
	def resetProgressBars(self):
		for row in range(self.w.rowCount()):
			self.w.item(row,self.pbColumn).setData(Qt.UserRole+1000,0)
			self.w.item(row,self.iconColumn).setData(Qt.UserRole+1001,'empty')
	
	def resetProgressBar(self, row):
		self.w.item(row,self.pbColumn).setData(Qt.UserRole+1000, 0)
		self.w.item(row,self.iconColumn).setData(Qt.UserRole+1001,'empty')


	######################
	## BUTTON FUNCTIONS ##
	######################
	
	def removeRow(self):
		r = (self.sender().parent().parent().currentRow())
		self.droppedFiles.pop(r)
		self.sender().parent().parent().removeRow(r)

		newTableHeight = self.w.rowCount() * (self.w.rowHeight(0)+1)
		self.w.setFixedHeight(newTableHeight)

		self.setMinimumHeight((self.height() + newTableHeight))
		self.setMinimumHeight(100)
		self.adjustSize()
		self.setMinimumSize(self.size())
	
	def chooseAlpha(self, text):
		switcher={
			"No Alpha":False,
			"with Alpha":True
		}
		self.alpha = switcher.get(text,"Invalid day of week")
		#print (self.alpha)

	def chooseCodec(self, text):
		switcher={
			"ProRes":"ProRes",
			"UTvideo":"UTvideo",
			"HAP":"HAP",
			"H.264":"H.264",
			"H.265":"H.265"
		}
		self.codec =  switcher.get(text,"Invalid day of week")
		
		if self.codec == "H.264" or self.codec == "H.265":
			self.alphaComboBox.setCurrentIndex(0)
			self.alphaComboBox.setEnabled(False)
		else:
			self.alphaComboBox.setEnabled(True)
			
		#print (self.codec)
		
	def chooseFrameRate(self, text):
		self.frameRate =  float(text)

	def radioBtnState(self, text):
		switcher={
			1:'Folder',
			2:'File'
		}
		self.nameFrom = switcher.get(text,"Invalid day of week")
		
	def showDebugLog(self, bol):
		'''
		Shows/Hides the Debug log
		'''
		if bol:
			self.logText.show()
			self.hideShowLog.setText('Hide Log')
			self.gridLayoutDebug.removeItem(self.spacerItem)
			self.adjustSize()
			self.setMinimumSize(self.size())
		else:
			self.gridLayoutDebug.addItem(self.spacerItem)
			self.logText.hide()
			self.hideShowLog.setText('Show Log')
			self.setMinimumHeight(100)
			self.adjustSize()
			self.setMinimumSize(self.size())
	
	def exploreOutput(self):
		FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
		explorePath = os.path.normpath(self.exportDir)
		subprocess.run([FILEBROWSER_PATH, explorePath])


	###########################
	## DRAG + DROP FUNCTIONS ##
	###########################
		
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
		'''
		Drop files directly onto the widget
		File locations are stored in fname
		:param e:
		:return:
		'''
		newFiles = set()
		if e.mimeData().hasUrls:
			e.setDropAction(Qt.CopyAction)
			e.accept()
			for url in e.mimeData().urls():
				fname = url.toLocalFile()
				if os.path.isdir(fname) and fname not in self.droppedFiles:
					newFiles.add(fname)

			self.addFilesToView(newFiles, self.w)
			self.droppedFiles = self.droppedFiles + list(newFiles)
			print(self.droppedFiles)
		else:
			e.ignore()
	
		
	#########################
	## EXECUTION FUNCTIONS ##
	#########################
				
	def compressPress(self):
		self.setEnabledControlls(False)

		#collect row data into a dict
		self.processData = [{'row':row, 'dirPath': self.w.item(row,self.fileColumn).data(0)} for row in range(self.w.rowCount()) if self.w.item(row,self.cbColumn).data(Qt.UserRole+1000)]

		for data in self.processData:		
			row = data['row']
			self.resetProgressBar(row)
			
			worker = Worker(self.execute_this_fn, 'val', data, self.codec, self.alpha, self.frameRate, self.nameFrom) # Any other args, kwargs are passed to the run function
			worker.signals.progressStarted.connect( self.setIconData )
			worker.signals.progressValue.connect( self.setPBData )
			worker.signals.progressLog.connect( self.logText.appendPlainText )
			worker.signals.finished.connect( self.threadComplete )
			
			# Execute
			self.threadpool.start(worker)
		
	def execute_this_fn(self, data:dict, codec:str, alpha:bool, frameRate:float, nameFrom:str, **kwargs):
		'''
		Returns tuple ( hasError: bool , row: int)
		'''
		callbacks = Callbacks(**kwargs)
		callbacks.setstarted((data['row'], 'proc'))
		pyCompression = pyFFMEGCompress(self.ffmpegPath, self.exportDir, data, codec, alpha, frameRate, nameFrom)
		hasError = pyCompression.printProcess(callbacks)

		return (hasError, data['row'])

	def threadComplete(self, result: tuple):
		'''
		On thread complete
		'''
		hasError, row = result
		if hasError:
			self.w.item(row,self.cbColumn).setData(Qt.UserRole+1000, False)
			self.w.item(row,self.iconColumn).setData(Qt.UserRole+1001, 'error')
			self.w.item(row,self.pbColumn).setData(Qt.UserRole+1001, 'error')
			self.w.item(row,self.pbColumn).setData(Qt.UserRole+1000, 100)
		else:
			self.w.item(row,self.iconColumn).setData(Qt.UserRole+1001, 'good')

		for i in range(len(self.processData)):
			if self.processData[i]['row'] == row:
				self.mutex.lock()
				self.processData.pop(i)
				self.mutex.unlock()
				break

		if len(self.processData) == 0:
			self.setEnabledControlls(True)


	#########################
	## MAIN                ##
	#########################

if __name__ == '__main__':
	dirList: list = [r'Z:\24-2231_RealCold-Lockhart Facility\01_Frames\FINAL\01_FusionOutput\s01-07']
	
	for arg in sys.argv:
		if os.path.isdir(arg) == True:
			#print(str(os.path.basename(arg)))
			dirList.append(arg)
	
	#sort the list , chech the code below make sure it's right
	dirList = sorted(dirList, key=lambda i: (os.path.basename(i)))
	
	print(dirList)
	
	QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
	QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
	
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	app.setPalette(PALETTE)
	dim = app.desktop().screenGeometry()
	
	print("The screen resolution is ({} X {}):".format(dim.width(), dim.height()))
	print("logicalDpiX ", app.desktop().logicalDpiX())
	print("phyiscalDpiX ", app.desktop().physicalDpiX())
	
	# Enable High DPI display with PyQt5
	app.setAttribute(Qt.AA_EnableHighDpiScaling)
	if hasattr(QStyleFactory, 'AA_UseHighDpiPixmaps'):
		app.setAttribute(Qt.AA_UseHighDpiPixmaps)
	
	config = configparser.ConfigParser()
	config.read(INI_PATH)
	exportDir: str = ''
	ffmpegPath: str = ''

	try:
		
		exportDir = config['ffmpegCompressorSettings']['exportDir']
		ffmpegPath = config['ffmpegCompressorSettings']['ffmpegPath']
		
		if not os.path.isfile(ffmpegPath):
			raise Exception(f'FFMpeg exe is not found at location {ffmpegPath}')

	except:
		configDialog = ConfigDialog()
		var = configDialog.exec()
		#return 1 if accepted, 0 if rejected
		if var == 1:
			exportDir: str = configDialog.exportDir_le.text()
			ffmpegPath: str = configDialog.ffmpegPath_le.text()
			
			# config.read(INI_PATH)
			config['ffmpegCompressorSettings'] = {}
			config['ffmpegCompressorSettings']['exportDir'] = exportDir
			config['ffmpegCompressorSettings']['ffmpegPath'] = ffmpegPath
			
			with open(INI_PATH, 'w') as configfile:
				config.write(configfile)

	if all([os.path.isdir(exportDir), os.path.isfile(ffmpegPath)]):
		print('INFO: Thumb Location is:', exportDir)
		print('INFO: Maps Assets Location is:', ffmpegPath)
	
		ex = MainWindow(exportDir, ffmpegPath, dirList)
	else:
		print("ERROR: Configuration Error")
		print('INFO: Thumb Location is:', exportDir, ' Path is Found:', os.path.isdir(exportDir))
		print('INFO: Asset Maps Location is:', ffmpegPath, ' Path is Found:', os.path.isfile(ffmpegPath))
		sys.exit(1)


	sys.exit(app.exec_())
