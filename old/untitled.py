# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Python37\untitled.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_mainLayout(object):
    def setupUi(self, mainLayout):
        mainLayout.setObjectName("mainLayout")
        mainLayout.resize(653, 476)
        self.verticalLayout = QtWidgets.QVBoxLayout(mainLayout)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(11)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayoutControlls = QtWidgets.QGridLayout()
        self.gridLayoutControlls.setObjectName("gridLayoutControlls")
        self.radioButton = QtWidgets.QRadioButton(mainLayout)
        self.radioButton.setObjectName("radioButton")
        self.gridLayoutControlls.addWidget(self.radioButton, 2, 0, 1, 2)
        self.alphaComboBox = QtWidgets.QComboBox(mainLayout)
        self.alphaComboBox.setObjectName("alphaComboBox")
        self.gridLayoutControlls.addWidget(self.alphaComboBox, 1, 1, 1, 1)
        self.frameRateComboBox = QtWidgets.QComboBox(mainLayout)
        self.frameRateComboBox.setObjectName("frameRateComboBox")
        self.gridLayoutControlls.addWidget(self.frameRateComboBox, 1, 2, 1, 1)
        self.codecLabel = QtWidgets.QLabel(mainLayout)
        self.codecLabel.setObjectName("codecLabel")
        self.gridLayoutControlls.addWidget(self.codecLabel, 0, 0, 1, 1)
        self.radioButton_2 = QtWidgets.QRadioButton(mainLayout)
        self.radioButton_2.setObjectName("radioButton_2")
        self.gridLayoutControlls.addWidget(self.radioButton_2, 2, 2, 1, 2)
        self.frameRateLabel = QtWidgets.QLabel(mainLayout)
        self.frameRateLabel.setObjectName("frameRateLabel")
        self.gridLayoutControlls.addWidget(self.frameRateLabel, 0, 2, 1, 1)
        self.compressButton = QtWidgets.QPushButton(mainLayout)
        self.compressButton.setObjectName("compressButton")
        self.gridLayoutControlls.addWidget(self.compressButton, 1, 3, 1, 1)
        self.codecComboBox = QtWidgets.QComboBox(mainLayout)
        self.codecComboBox.setObjectName("codecComboBox")
        self.gridLayoutControlls.addWidget(self.codecComboBox, 1, 0, 1, 1)
        self.alphaLabel = QtWidgets.QLabel(mainLayout)
        self.alphaLabel.setObjectName("alphaLabel")
        self.gridLayoutControlls.addWidget(self.alphaLabel, 0, 1, 1, 1)
        self.line = QtWidgets.QFrame(mainLayout)
        self.line.setLineWidth(2)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayoutControlls.addWidget(self.line, 3, 0, 1, 4)
        self.verticalLayout.addLayout(self.gridLayoutControlls)
        self.gridLayoutProgress = QtWidgets.QGridLayout()
        self.gridLayoutProgress.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.gridLayoutProgress.setObjectName("gridLayoutProgress")
        self.label_5 = QtWidgets.QLabel(mainLayout)
        self.label_5.setObjectName("label_5")
        self.gridLayoutProgress.addWidget(self.label_5, 0, 2, 1, 1)
        self.progressBar = QtWidgets.QProgressBar(mainLayout)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName("progressBar")
        self.gridLayoutProgress.addWidget(self.progressBar, 0, 1, 1, 1)
        self.checkBox = QtWidgets.QCheckBox(mainLayout)
        self.checkBox.setText("")
        self.checkBox.setObjectName("checkBox")
        self.gridLayoutProgress.addWidget(self.checkBox, 0, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayoutProgress)
        self.gridLayoutAddMore = QtWidgets.QGridLayout()
        self.gridLayoutAddMore.setContentsMargins(0, 0, 0, 0)
        self.gridLayoutAddMore.setObjectName("gridLayoutAddMore")
        self.dragAndDropLabel = QtWidgets.QLabel(mainLayout)
        self.dragAndDropLabel.setMinimumSize(QtCore.QSize(0, 40))
        self.dragAndDropLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.dragAndDropLabel.setObjectName("dragAndDropLabel")
        self.gridLayoutAddMore.addWidget(self.dragAndDropLabel, 1, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayoutAddMore)
        self.gridLayoutDebug = QtWidgets.QGridLayout()
        self.gridLayoutDebug.setObjectName("gridLayoutDebug")
        self.plainTextEdit = QtWidgets.QPlainTextEdit(mainLayout)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.gridLayoutDebug.addWidget(self.plainTextEdit, 2, 0, 1, 1)
        self.debugLabel = QtWidgets.QLabel(mainLayout)
        self.debugLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.debugLabel.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.debugLabel.setObjectName("debugLabel")
        self.gridLayoutDebug.addWidget(self.debugLabel, 1, 0, 1, 1)
        self.line_2 = QtWidgets.QFrame(mainLayout)
        self.line_2.setLineWidth(2)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayoutDebug.addWidget(self.line_2, 0, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayoutDebug)

        self.retranslateUi(mainLayout)
        QtCore.QMetaObject.connectSlotsByName(mainLayout)

    def retranslateUi(self, mainLayout):
        _translate = QtCore.QCoreApplication.translate
        mainLayout.setWindowTitle(_translate("mainLayout", "Form"))
        self.radioButton.setText(_translate("mainLayout", "Folder Name"))
        self.codecLabel.setText(_translate("mainLayout", "Codec"))
        self.radioButton_2.setText(_translate("mainLayout", "File Name"))
        self.frameRateLabel.setText(_translate("mainLayout", "Frame Rate"))
        self.compressButton.setText(_translate("mainLayout", "Compress"))
        self.alphaLabel.setText(_translate("mainLayout", "Alpha"))
        self.label_5.setText(_translate("mainLayout", "n"))
        self.dragAndDropLabel.setText(_translate("mainLayout", "Drag and Drop more folders here"))
        self.debugLabel.setText(_translate("mainLayout", "Debug:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainLayout = QtWidgets.QWidget()
    ui = Ui_mainLayout()
    ui.setupUi(mainLayout)
    mainLayout.show()
    sys.exit(app.exec_())
