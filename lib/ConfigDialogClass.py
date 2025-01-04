import os, sys
import configparser
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QVBoxLayout , QLabel , QPushButton , QLineEdit , QLabel , QGridLayout , QDialogButtonBox , QSpacerItem , QSizePolicy , QFileDialog , QDialog, QApplication

class ConfigDialog(QDialog):
	DEFAULT_WIDTH = 35
	def __init__(self, _appIcon = QIcon(), _windowWidth = 600, parent = None):
		super().__init__(parent)
		
		self.verticalLayout = QVBoxLayout(self)
		self.gridLayoutControlls = QGridLayout()

		# Poliigon Thumbs
		order = 0
		self.gridLayoutControlls.addWidget(QLabel('Select Export Folder'), order, 0, 1, 1)
		self.exportDir_btn = QPushButton("...")
		self.exportDir_btn.setFixedWidth(self.DEFAULT_WIDTH)
		self.exportDir_btn.clicked.connect(lambda: self.getDir(self.exportDir_le))
		self.exportDir_le = QLineEdit()
		self.exportDir_le.setReadOnly(True)
		self.gridLayoutControlls.addWidget(self.exportDir_btn, order+1, 1)
		self.gridLayoutControlls.addWidget(self.exportDir_le, order+1, 0)
		
		# 3dsmax Path
		order = order + 2
		self.gridLayoutControlls.addWidget(QLabel('Select FFMpeg Executable'), order, 0, 1, 1)
		self.ffmpegPath_btn = QPushButton("...")
		self.ffmpegPath_btn.setFixedWidth(self.DEFAULT_WIDTH)
		self.ffmpegPath_btn.clicked.connect(lambda: self.getFile(self.ffmpegPath_le))
		self.ffmpegPath_le = QLineEdit()
		self.ffmpegPath_le.setReadOnly(True)
		self.gridLayoutControlls.addWidget(self.ffmpegPath_btn, order+1, 1)
		self.gridLayoutControlls.addWidget(self.ffmpegPath_le, order+1, 0)

		# OK/Cancel buttons
		self.gridLayoutOKCancel = QGridLayout()
		self.okCancel = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
		self.okButton = self.okCancel.button(QDialogButtonBox.Ok)
		self.okButton.setEnabled(False)
		self.okCancel.accepted.connect(self.okPressed)
		self.okCancel.rejected.connect(self.cancelPressed)
		self.gridLayoutOKCancel.addWidget(self.okCancel, 0, 0)

		self.spacerItem = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.gridLayoutOKCancel.addItem(self.spacerItem, 1, 0)

		# Add up all the layouts in order
		self.verticalLayout.addLayout(self.gridLayoutControlls)
		self.verticalLayout.addLayout(self.gridLayoutOKCancel)

		self.setWindowTitle("pyFFMpeg Compressor Settings")
		self.setModal(True)
		self.setFixedWidth(_windowWidth)
		self.setWindowIcon(_appIcon)
		self.adjustSize()
		self.setFixedHeight(self.height())
		
	
	@pyqtSlot()
	def checkValid(self):
		if all([self.exportDir_le.text() != '', self.ffmpegPath_le.text() != '']):
			self.okButton.setEnabled(True)
		else:
			self.okButton.setEnabled(False)
	
	@pyqtSlot()
	def getDir(self, _widget):
		dirPath = QFileDialog.getExistingDirectory(self, 'Select a directory', QDir.home().dirName(), QFileDialog.ShowDirsOnly)
		
		if dirPath:
			_widget.setText(dirPath)

		self.checkValid()
	
	@pyqtSlot()
	def getFile(self, _widget):
		dirPath = QFileDialog.getOpenFileName(self, 'Select the ffmpeg.exe', QDir.home().dirName(), "*ffmpeg.exe")
		
		if dirPath[0]:
			_widget.setText(dirPath[0])

		self.checkValid()

	@pyqtSlot()
	def okPressed(self):
		config = configparser.ConfigParser()
		config['ffmpegCompressorSettings'] = {'exportDir':self.exportDir_le.text(),'ffmpegPath':self.ffmpegPath_le.text()}
		
		with open('pyFFMpegCompressorSettings.ini', 'w') as configfile:
			config.write(configfile)

		self.accept()

	@pyqtSlot()
	def cancelPressed(self):
		self.reject()


#use
def main(): 
	app = QApplication(sys.argv)
	ex = PoliigonBrowserConfigDialog()
	var = ex.exec()
	if var == 1:
		print(var)
		print(ex.ffmpegPath_le.text())
		print(ex.exportDir_le.text())
	sys.exit(app.exec_())
	
if __name__ == '__main__':
	main()

