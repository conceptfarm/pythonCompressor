from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QRegularExpression, QRegularExpressionMatchIterator
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor, QTextCharFormat, QPalette, QTextBlock, QFont

class LogReportHighlighter(QtGui.QSyntaxHighlighter):
	"""Syntax highlighter for the Python language.
	"""
	headingBorderColour = QColor(158, 158, 158)
	headingTitleColour = QColor(158, 158, 158)
	timestampColour = QColor(158, 158, 158)
	errorColour = QColor(255, 69, 0)
	infoColour = QColor(128, 200, 255)
	pythonColour = QColor(160, 160, 255)
	stdoutColour = QColor(37, 200, 25)
	warningColour = QColor(255, 192, 128)
	markerColour = QColor(158, 158, 158)
	
	
	def __init__(self, parent: QtGui.QTextDocument) -> None:
		super().__init__(parent)
		self.rules = []
		self.addRules()
		self.rules = [ (QRegularExpression(pat), self.createFormat(col,*var)) for (pat, (col,*var)) in self.rules ]

	def addRule(self, pattern, col):
		self.rules = self.rules + [(pattern, col)]
	
	def addRules(self):
		"""Setup syntax highlighting rules and add them to a list. The order in which the rules are added is important 
		   and can affect how nested highlighting works (multiple rules which may match a given text)."""
		self.addHeadingRules()
		self.addTimestampRules()
		self.addKeywordBodyRules()
		self.addKeywordRules()
		self.addMarkerRules()

	def addHeadingRules(self):
		"""Matches log/report headings, such as Error, StackTrace, Log, Details, Worker Information, etc. Applies to all render logs."""
		self.addRule('={55,}', (self.headingBorderColour, True))
		self.addRule('^(\\s*[A-Za-z])+$', (self.headingTitleColour, True))

	def addTimestampRules(self):
		"""Matches timestamps at the beginning of each line in the log/report. Applies to all render logs."""
		self.addRule('^\\d{4}-\\d{2}-\\d{2}\\s+(\\d{1,2}:\\s*){3,}', (self.timestampColour, True))

	def addKeywordRules(self):
		"""Matches logging type keywords. Applies to most render logs."""
		self.addRule('\\bERROR\\b', (self.errorColour, True))
		self.addRule('\\bINFO\\b', (self.infoColour, True))
		self.addRule('\\bWARNING\\b', (self.warningColour, True))
		keywords = [4, 5, 6, 7, 8]
		format = (self.errorColour, True)
		# for patternStr in keywords:
		# 	pattern = QRegularExpression(patternStr, QRegularExpression.CaseInsensitiveOption)
		# 	self.addRule(pattern, format)

		self.addRule('\\(?[\\w\\.]*Exception\\)?', format)
		self.addRule('\\b(\\w)*WARNING:\\s*', (self.warningColour, True))
		self.addRule('\\bINFO:\\s*', (self.infoColour, True))
		# self.addRule('(?<=[\\]:])[\\w\\s]*\\Info:\\s*', (self.infoColour, True))
		self.addRule('\\bSTDOUT:\\s*', (self.stdoutColour, True))
		self.addRule('\\bPYTHON:\\s*', (self.pythonColour, True))

	def addKeywordBodyRules(self):
		"""Matches the text that follows logging type keywords. Applies to most render logs."""
		self.addRule('(?<=STDOUT:).*', (self.toSecondaryColor(self.stdoutColour),))
		self.addRule('(?<=PYTHON:).*', (self.toSecondaryColor(self.pythonColour),))
		self.addRule('(?<=INFO:).*', (self.toSecondaryColor(self.infoColour),))
		
		keywords = ['^\\s*at\\s+.*', '(?<=:)\\s+at\\s+.*', '(?<=ERROR:).*', '(?<=FAILED:).*']
		format = (self.toSecondaryColor(self.errorColour),)
		for patternStr in keywords:
			self.addRule(patternStr, format)

		self.addRule('(?<=WARNING:).*', (self.toSecondaryColor(self.warningColour),))

	def addMarkerRules(self):
		"""Matches indentation markers. Applies to Conda logs."""
		self.addRule('\\s(<{3,}|>{3,}|\\+{1,})\\s', (self.markerColour,))

	def createFormat(self, foreground, bold=False, italics=False):
		"""Helper function to return a QTextCharFormat with specified colour, bold, and italics options."""
		format = QTextCharFormat()
		format.setForeground(foreground)
		format.setFontWeight(QFont.Bold if bold else QFont.Normal)
		format.setFontItalic(italics)
		return format
	
	def toSecondaryColor(self, color):
		"""Generates a secondary colour from a given colour. This secondary colour is used to colour the secondary text
		(i.e. the text that comes after keywords like ERROR, INFO, STDOUT, etc.) a different intensity so that users can
		differentiate between keywords and body text.

		Returns a darker shade if Monitor's default text colour is black (i.e. General Palette colour is light).
		Returns a lighter shade if Monitor's default text colour is white (i.e. General Palette colour is dark)."""
		BLACK = QColor(0, 0, 0)
		WHITE = QColor(255, 255, 255)
		secColor = QColor(color)
		textColor = QApplication.palette().color(QPalette.Text)
		if textColor == BLACK:
			secColor.setHsv(color.hue(), 208, 128)
		elif textColor == WHITE:
			secColor.setHsv(color.hue(), 48, 255)
		return secColor
	
	def highlightBlock(self, text):
		for expression, format in self.rules:
			matchIter = expression.globalMatch(text)
			while (matchIter.hasNext()):
				match = matchIter.next()
				self.setFormat(match.capturedStart(), match.capturedLength(), format)

		self.setCurrentBlockState(0)

