#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton, QApplication, QStyleFactory,QGridLayout,QSpacerItem,QSizePolicy,QProgressBar)
from PyQt5.QtCore import Qt, QCoreApplication, QRect
import sys
import os
import time
TIME_LIMIT = 100

class Example(QWidget):
    
	def __init__(self, inList):
		super().__init__()
		self.inList = inList
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
		self.buttonCompress.clicked[bool].connect(self.pushTest)

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
			self.tempPB.setFormat(str(self.inList[i]))
			self.gridLayout.addWidget(self.tempPB, i+2, 0, 1, 4)
			self.pbList.append(self.tempPB)
		
		spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.gridLayout.addItem(spacerItem, len(self.inList)+2, 0, 1, 1)
		
		self.comboCodec.activated[str].connect(self.onActivated)
		
		self.setGeometry(300, 300, 390, 100)
		self.gridLayout.setGeometry(QRect(19, 19, 581, 94))
		self.setWindowTitle('FFMpeg Python Compressor')
		self.show()
        
        
	def onActivated(self, text):

		self.lblCodec.setText(text)
		self.lblCodec.adjustSize()
		#print (text)
    
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
		

if __name__ == '__main__':
	#delete this later
	#dirList = ["some1","some2"]
	
	dirList = []
	
	for arg in sys.argv:
		if os.path.isdir(arg) == True:
			print(str(os.path.basename(arg)))
			dirList.append(arg)
	
	#sort the list , chech the code below make sure it's right
	sorted(dirList, key=lambda i: int(os.path.basename(i)))
	
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
	
	ex = Example(dirList)
	print(ex.currentData(ex.comboCodec))
	print(ex.currentData(ex.comboAlpha))
	print(ex.currentData(ex.comboFrameRate))

	sys.exit(app.exec_())
