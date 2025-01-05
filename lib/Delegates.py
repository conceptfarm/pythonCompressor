#####################
## DELEGATES
#####################


# QtPy
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lib.AppIcons import AppIcons
from lib.DarkPalette import QtDarkPalette

APPICONS = AppIcons()
PALETTE = QtDarkPalette()

class ProgressDelegate(QStyledItemDelegate):
	def paint(self, painter, option, index):
		progress = index.data(Qt.DisplayRole)
		status = index.data(Qt.UserRole)

		opt = QStyleOptionProgressBar()
		opt.rect = option.rect.adjusted(5,5,-5,-5)
		opt.minimum = 0
		opt.maximum = 100

		opt.progress = progress
		opt.text = "{}%".format(progress)
		opt.textAlignment = Qt.AlignCenter
		opt.textVisible = True
		if status == 'error':
			pal = opt.palette
			pal.setColor(QPalette.Highlight, PALETTE.errorColour) # or QPalette::Window doesnt matter
			opt.palette = pal
		QApplication.style().drawControl(QStyle.CE_ProgressBar, opt, painter)


class CheckboxDelegate(QStyledItemDelegate):
	# https://stackoverflow.com/questions/36778577/qstyleditemdelegate-how-to-make-checkbox-button-to-change-its-state-on-click
	def paint(self, painter, option, index):
		isChecked = index.data(Qt.DisplayRole)

		opt = QStyleOptionButton()
		opt.rect = option.rect.adjusted(10,5,-10,-5)
		opt.textAlignment = Qt.AlignCenter

		if isChecked:
			opt.state |= QStyle.State_On
		else:
			opt.state |= QStyle.State_Off

		QApplication.style().drawControl(QStyle.CE_CheckBox, opt, painter)

	def editorEvent(self, event, model, option, index):
		if event.type() == QEvent.MouseButtonRelease:
			value = index.data(Qt.DisplayRole)
			# invert checkbox state
			model.setData(index, not value, Qt.DisplayRole)
			return True

		return QStyledItemDelegate.editorEvent(self, event, model, option, index)


class IconDelegate(QStyledItemDelegate):
	def __init__(self, Parent=None):
		super().__init__()
		
		self.emptyIcon = QIcon(QApplication.style().standardIcon(QStyle.SP_CustomBase))
		self.goodIcon = APPICONS.qIconFromBase64(APPICONS.tickIconB)
		self.errorIcon = APPICONS.qIconFromBase64(APPICONS.crossIconB)
		self.processingIcon = APPICONS.qIconFromBase64(APPICONS.arrowIconB)

		self._iconDict = {'empty':self.emptyIcon,'good':self.goodIcon,'error':self.errorIcon,'proc':self.processingIcon}
	
	def paint(self, painter, option, index):
		d = index.data(Qt.DecorationRole)
		icon = self._iconDict[d]
		#option.rect = option.rect.adjusted(5,5,-5,-5)
		#option.rect.setSize(QSize(15,15))
		icon.paint(painter, option.rect, Qt.AlignCenter)


class RemoveButton(QPushButton):		
	def __init__(self, Parent=None):
		super().__init__()
		self.trashIcon = APPICONS.qIconFromBase64(APPICONS.trashIconB)
		self.setIcon(self.trashIcon)
		self.setIconSize(self.trashIcon.actualSize(QSize(50,50)))
		self.setFlat(True)
		self.setMaximumWidth(40)