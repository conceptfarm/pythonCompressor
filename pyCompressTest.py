# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pyCompressTest.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(629, 137)
        
        self.gridLayoutWidget = QtWidgets.QWidget(Dialog)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(19, 19, 581, 94))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        
        self.lblFrameRate = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lblFrameRate.setObjectName("lblFrameRate")
        self.gridLayout.addWidget(self.lblFrameRate, 0, 2, 1, 1)
        
        self.lblCodec = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lblCodec.setObjectName("lblCodec")
        self.gridLayout.addWidget(self.lblCodec, 0, 0, 1, 1)
        
        self.lblNone = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lblNone.setEnabled(False)
        self.lblNone.setText("")
        self.lblNone.setObjectName("lblNone")
        self.gridLayout.addWidget(self.lblNone, 0, 3, 1, 1)
        
        self.comboCodec = QtWidgets.QComboBox(self.gridLayoutWidget)
        self.comboCodec.setObjectName("comboCodec")
        self.gridLayout.addWidget(self.comboCodec, 1, 0, 1, 1)
        
        self.lblAlpha = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lblAlpha.setObjectName("lblAlpha")
        self.gridLayout.addWidget(self.lblAlpha, 0, 1, 1, 1)
        
        self.comboFrameRate = QtWidgets.QComboBox(self.gridLayoutWidget)
        self.comboFrameRate.setObjectName("comboFrameRate")
        self.gridLayout.addWidget(self.comboFrameRate, 1, 2, 1, 1)
        
        self.comboAlpha = QtWidgets.QComboBox(self.gridLayoutWidget)
        self.comboAlpha.setObjectName("comboAlpha")
        self.gridLayout.addWidget(self.comboAlpha, 1, 1, 1, 1)
        
        self.lblListFiles = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lblListFiles.setObjectName("lblListFiles")
        self.gridLayout.addWidget(self.lblListFiles, 3, 0, 1, 4)
        
        self.buttonCompress = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.buttonCompress.setObjectName("buttonCompress")
        self.gridLayout.addWidget(self.buttonCompress, 1, 3, 1, 1)
        
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.lblFrameRate.setText(_translate("Dialog", "Frame Rate"))
        self.lblCodec.setText(_translate("Dialog", "Codec"))
        self.lblAlpha.setText(_translate("Dialog", "Alpha"))
        self.lblListFiles.setText(_translate("Dialog", "TextLabel"))
        self.buttonCompress.setText(_translate("Dialog", "Compress"))
        Dialog.show() 
