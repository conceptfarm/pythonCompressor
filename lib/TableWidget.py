from dataclasses import dataclass
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lib.DarkPalette import QtDarkPalette
from lib.AppIcons import AppIcons
from lib.Delegates import RemoveButton, CheckboxDelegate, ProgressDelegate, IconDelegate
# from lib.ContextMenu import ContextMenu

APPICONS = AppIcons()

@dataclass
class Columns():
	CHECKBOX: int = 0
	FILENAME: int = 1
	ICON: int = 2
	PROGRESS: int = 3
	BUTTON: int = 4

class FileTable(QTableWidget):
	
	PALETTE = QtDarkPalette()
	PALETTE.setColor(QPalette.Highlight, QColor(40, 40, 40))
	PALETTE.setColor(QPalette.HighlightedText, Qt.white)
	
	def __init__(self, rows, columns, Parent=None):
		super().__init__(rows, columns, Parent)
		self.droppedFiles: set = set()
		self.parent = self.parent()

		# Delegates
		self.progDelegate = ProgressDelegate(self)
		self.iconDelegate = IconDelegate(self)
		self.cbDelegate = CheckboxDelegate(self)
		self.setItemDelegateForColumn(Columns.ICON, self.iconDelegate)
		self.setItemDelegateForColumn(Columns.PROGRESS, self.progDelegate)
		self.setItemDelegateForColumn(Columns.CHECKBOX, self.cbDelegate)

		# Defaul Settings
		self.horizontalHeader().setSectionResizeMode(Columns.FILENAME, QHeaderView.Stretch)
		self.horizontalHeader().hide()
		self.verticalHeader().hide()
		self.setColumnWidth(Columns.CHECKBOX, 10)
		self.setColumnWidth(Columns.ICON, 10)
		self.setColumnWidth(Columns.PROGRESS, 250)
		self.setColumnWidth(Columns.BUTTON, 40)
		self.setSelectionMode(QAbstractItemView.NoSelection)
		self.setState(QAbstractItemView.NoState)

		# Tweaked selection style colours
		fileTablePal = QtDarkPalette()
		fileTablePal.setColor(QPalette.Highlight, QColor(40, 40, 40))
		fileTablePal.setColor(QPalette.HighlightedText, Qt.white)
		self.setPalette(self.PALETTE)

		self.threadpool = QThreadPool().globalInstance()
	
	def addFilesToView(self, files: set):
		'''
		Progress bar populate function
		'''
		existingRows = self.rowCount()
		for r, file in enumerate(files):
			newRow = r + existingRows
			
			# checkbox
			it_cb = QTableWidgetItem()
			it_cb.setTextAlignment(Qt.AlignCenter)
			it_cb.setData(Qt.DisplayRole, True)

			# file name
			it_file = QTableWidgetItem(file)
			
			# status icon
			it_id = QTableWidgetItem()
			it_id.setData(Qt.DecorationRole, 'empty')
			
			# progress bar
			it_progress = QTableWidgetItem()
			it_progress.setData(Qt.DisplayRole, 0)
			
			# remove button
			it_button = QTableWidgetItem()
						
			self.insertRow(self.rowCount())
			
			for c, item in enumerate((it_cb, it_file, it_id, it_progress, it_button)):
				self.setItem(newRow, c, item)
				
				# No item flag for everything but checkbox and progress
				if c != Columns.CHECKBOX and c != Columns.BUTTON: 
					item.setFlags(Qt.NoItemFlags)
				
				removeButton = RemoveButton(self)
				removeButton.clicked.connect(self.removeTableItem)
				self.setCellWidget(newRow, 4, removeButton)
			
			self.adjustMainWindowSize()

		self.droppedFiles.update(files)
		
	def adjustMainWindowSize(self):
		newTableHeight = self.rowCount() * (self.rowHeight(0)+1)
		self.setFixedHeight(newTableHeight)
		self.parent.setMinimumHeight((self.parent.height() + newTableHeight))
		self.parent.setMinimumHeight(100)
		w = self.parent.width()
		self.parent.adjustSize()
		# self.parent.setMinimumSize(w, self.parent.size().height())
		self.parent.resize(w, self.parent.height())
	
	def setPBData(self, data: tuple):
		'''
		Sets the process bar 
		data: tuple (row: int, process %: int)
		'''
		row, percent = data
		self.item(row, Columns.PROGRESS).setData(Qt.DisplayRole, percent)

	def setIconData(self, data: tuple):
		row , icon = data
		self.item(row, Columns.ICON).setData(Qt.DecorationRole, icon)
	
	def resetAllProgressBars(self):
		for row in range(self.rowCount()):
			self.item(row, Columns.PROGRESS).setData(Qt.DisplayRole, 0)
			self.item(row, Columns.ICON).setData(Qt.DecorationRole,'empty')
	
	def resetProgressBar(self, row):
		self.item(row,Columns.PROGRESS).setData(Qt.DisplayRole, 0)
		self.item(row,Columns.ICON).setData(Qt.DecorationRole,'empty')

	@pyqtSlot()
	def removeTableItem(self):
		row = self.currentRow()
		fileName = self.item(row, Columns.FILENAME).data(0)
		self.droppedFiles.remove(fileName)
		self.removeRow(row)

		self.adjustMainWindowSize()