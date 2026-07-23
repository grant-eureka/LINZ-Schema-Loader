#   *******************************************************************
# -*- coding: utf-8 -*-

#   *******************************************************************
#   Updated Qt5/Qt6 imports to be used with generated file from
#   PyQt UI code generator
#   Enables either pyqt5, pyqt6 or PySide2 modules to be used
#   *******************************************************************

import importlib.util

if importlib.util.find_spec("PyQt"):
    # from PyQt import uic, loadUi
    # from PyQt import QtGui, QtWidgets, QtCore
    from PyQt import (
        pyqt, QObject, QCoreApplication, QSettings,
        Qt, QSize, QRect, QMetaObject,
        Signal, Slot,
        QIcon, QPixmap, QImage, QFont,
        QApplication, QMainWindow, QWidget, QFrame,
        QDialog, QMessageBox, QFileDialog,
        QLayout, QFormLayout, QGridLayout,
        QVBoxLayout, QHBoxLayout,
        QSizePolicy, QSpacerItem,
        QAbstractItemView, QAbstractScrollArea, QScrollArea,
        QLabel, QLineEdit, QPlainTextEdit,
        QPushButton, QToolButton, QListWidget, QListWidgetItem,
        QProgressBar, QMenuBar, QStatusBar,
        QMenu, QAction,
        QDomDocument, QDomElement, QTextCursor)
else:
    # from .PyQt import uic, loadUi
    # from .PyQt import QtGui, QtWidgets, QtCore
    from .PyQt import (
        pyqt, QObject, QCoreApplication, QSettings,
        Qt, QSize, QRect, QMetaObject,
        Signal, Slot,
        QIcon, QPixmap, QImage, QFont,
        QApplication, QMainWindow, QWidget, QFrame,
        QDialog, QMessageBox, QFileDialog,
        QLayout, QFormLayout, QGridLayout,
        QVBoxLayout, QHBoxLayout,
        QSizePolicy, QSpacerItem,
        QAbstractItemView, QAbstractScrollArea, QScrollArea,
        QLabel, QLineEdit, QPlainTextEdit,
        QPushButton, QToolButton, QListWidget, QListWidgetItem,
        QProgressBar, QMenuBar, QStatusBar,
        QMenu, QAction,
        QDomDocument, QDomElement, QTextCursor)

#   *******************************************************************
