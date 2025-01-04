#PyQt Classes
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from logging.LogReportHighlighter import LogReportHighlighter
# from LogReportHighlighter import LogReportHighlighter

class LogPlainTextEdit(QPlainTextEdit):
		numberbarSpace = 4

		def __init__(self, systemDefaultFont=None, useMonospace=True, *args):
			super(QPlainTextEdit, self).__init__(parent=None)
			self.setFrameStyle(QFrame.NoFrame)
			self.setMouseTracking(False)
			self.setWordWrapMode(QTextOption.NoWrap)
			self.setTabStopDistance(20)
			self.highlight = LogReportHighlighter(self.document())

			self.defaultFont = systemDefaultFont
			
			if self.defaultFont == None:
				self.defaultFont = QApplication.font()
			
			if systemDefaultFont == None:
				self.defaultFont = QApplication.font()
			else:
				self.defaultFont = systemDefaultFont
			
			if useMonospace:
				self.setMonospaceFont()
			else:
				self.setFont(self.defaultFont)
			
			return
		
		
		def setMonospaceFont(self):
			font = self.loadMonospaceFont()
			self.setFont(font)

		
		def loadMonospaceFont(self):
			font = QFont('monospace')
			if self.isFixedPitch(font):
				return font
			font.setStyleHint(QFont.Monospace)
			
			if self.isFixedPitch(font):
				return font
			font.setStyleHint(QFont.TypeWriter)
			
			if self.isFixedPitch(font):
				return font
			
			font.setFamily('courier')
			return font

		def isFixedPitch(self, font):
			fontInfo = QFontInfo(font)
			return fontInfo.fixedPitch()