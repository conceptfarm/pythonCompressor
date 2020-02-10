#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
ZetCode PyQt5 tutorial 

This example shows how to use a QComboBox widget.
 
Author: Jan Bodnar
Website: zetcode.com 
Last edited: August 2017
"""

from PyQt5.QtWidgets import (QWidget,QDialog, QLabel, QComboBox, QPushButton, QApplication, QStyleFactory,QHBoxLayout,QVBoxLayout)
from PyQt5.QtCore import Qt, QCoreApplication
from pyCompressTest import Ui_Dialog
import sys
import os



class AppWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.show()  
        		
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    w = AppWindow()
    w.show()
    sys.exit(app.exec_())
