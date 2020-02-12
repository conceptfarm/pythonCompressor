#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
ZetCode PyQt5 tutorial 

This example shows how to use a QComboBox widget.
 
Author: Jan Bodnar
Website: zetcode.com 
Last edited: August 2017
"""

from PyQt5.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton, QApplication, QStyleFactory,QHBoxLayout,QVBoxLayout)
from PyQt5.QtCore import Qt, QCoreApplication
import sys
import os



class Example(QWidget):
    
	def __init__(self, inList):
		super().__init__()
		self.inList = inList
		self.initUI()
        
        
	def initUI(self):      

		#self.hbox = QVBoxLayout(self)
		self.hBoxLables = QHBoxLayout(self)
		
		self.lblCodec = QLabel("Codec", self)
		self.lblAlpha = QLabel("Alpha", self)
		self.lblFrameRate = QLabel("Frame Rate", self)
		self.hBoxLables.addWidget(self.lblCodec)
		self.hBoxLables.addWidget(self.lblAlpha)
		self.hBoxLables.addWidget(self.lblFrameRate)
		
		self.hBoxButtons = QHBoxLayout(self)
		
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

		self.hBoxButtons.addWidget(self.comboCodec)
		self.hBoxButtons.addWidget(self.comboAlpha)
		self.hBoxButtons.addWidget(self.comboFrameRate)
		self.hBoxButtons.addWidget(self.buttonCompress)
		
		#self.lblCodec.move(20, 25)
		#self.comboCodec.move(20, 40)
		#self.lblAlpha.move(110, 25)
		#self.comboAlpha.move(110, 40)
		#self.lblFrameRate.move(200, 25)
		#self.comboFrameRate.move(200, 40)
		#self.buttonCompress.move(290,40)
		
		#self.hbox.addWidget(self.vBoxLables)
		#self.hbox.addWidget(self.vBoxButtons)
		
		self.vbox = QVBoxLayout(self)
		
		for dir in self.inList:
			self.tempLbl = QLabel(str(dir), self)
			self.vbox.addWidget(self.tempLbl)
			print(str(dir))
		
		self.comboCodec.activated[str].connect(self.onActivated)        
		 
		#self.hbox.addWidget(self.vbox)
		
		self.setGeometry(300, 300, 390, 100)
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



		
if __name__ == '__main__':
	

	dirList = ['some','some2','some3']
	
	#for arg in sys.argv:
	#	if os.path.isdir(arg) == True:
	#		print(str(os.path.basename(arg)))
	#		dirList.append(arg)
	
	
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
