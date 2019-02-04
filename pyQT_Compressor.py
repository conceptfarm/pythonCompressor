#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
ZetCode PyQt5 tutorial 

This example shows how to use a QComboBox widget.
 
Author: Jan Bodnar
Website: zetcode.com 
Last edited: August 2017
"""

from PyQt5.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton, QApplication)
import sys

class Example(QWidget):
    
	def __init__(self):
		super().__init__()

		self.initUI()
        
        
	def initUI(self):      

		self.lblCodec = QLabel("Codec", self)
		self.lblAlpha = QLabel("Alpha", self)
		self.lblFrameRate = QLabel("Frame Rate", self)

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

		self.lblCodec.move(20, 35)
		self.comboCodec.move(20, 50)
		self.lblAlpha.move(110, 35)
		self.comboAlpha.move(110, 50)
		self.lblFrameRate.move(200, 35)
		self.comboFrameRate.move(200, 50)
		self.buttonCompress.move(290,50)
		

		self.comboCodec.activated[str].connect(self.onActivated)        
		 
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
   
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	ex = Example()
	print(ex.currentData(ex.comboCodec))
	print(ex.currentData(ex.comboAlpha))
	print(ex.currentData(ex.comboFrameRate))
	sys.exit(app.exec_())