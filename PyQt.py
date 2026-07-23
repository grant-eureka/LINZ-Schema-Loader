# PyQt.py
# Select pyqt version to use and import modules
# If qgis module found, then let qgis select pyqt version.
# Otherwise select, in order of preference, with v.6 over v.5
# and pyqt over pyside.
import sys
import importlib.util

PYQT = False
PYSIDE = False
PYQGIS = False

try:
    if importlib.util.find_spec("qgis"):
        # Let qgis.PyQt select PyQt version
        from qgis.core import Qgis
        import qgis.PyQt as PyQt
        from qgis.PyQt.QtCore import (
            QObject, QCoreApplication, QSettings,
            Qt, QSize, QRect, QMetaObject,
            pyqtSignal as Signal, pyqtSlot as Slot)
        from qgis.PyQt.QtGui import (
            QIcon, QPixmap, QImage, QFont, QColor, QTextCursor, QAction)
        from qgis.PyQt.QtWidgets import (
            QApplication, QMainWindow, QWidget, QFrame,
            QDialog, QMessageBox, QFileDialog,
            QLayout, QFormLayout, QGridLayout,
            QVBoxLayout, QHBoxLayout,
            QSizePolicy, QSpacerItem,
            QAbstractItemView, QAbstractScrollArea, QScrollArea,
            QLabel, QLineEdit, QPlainTextEdit,
            QPushButton, QToolButton, QListWidget, QListWidgetItem,
            QProgressBar, QMenuBar, QStatusBar, QMenu)
        from qgis.PyQt.QtXml import (
            QDomDocument, QDomElement)
        PYQGIS = True
        # print('using module qgis.PyQt')
    elif importlib.util.find_spec("PyQt6"):
        # Use PyQt6
        import PyQt6 as PyQt
        from PyQt6.QtCore import (
            QObject, QCoreApplication, QSettings,
            Qt, QSize, QRect, QMetaObject,
            pyqtSignal as Signal, pyqtSlot as Slot)
        from PyQt6.QtGui import (
            QIcon, QPixmap, QImage, QFont, QColor, QTextCursor, QAction)
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QFrame,
            QDialog, QMessageBox, QFileDialog,
            QLayout, QFormLayout, QGridLayout,
            QVBoxLayout, QHBoxLayout,
            QSizePolicy, QSpacerItem,
            QAbstractItemView, QAbstractScrollArea, QScrollArea,
            QLabel, QLineEdit, QPlainTextEdit,
            QPushButton, QToolButton, QListWidget, QListWidgetItem,
            QProgressBar, QMenuBar, QStatusBar, QMenu)
        from PyQt6.QtXml import (
            QDomDocument, QDomElement)
        PYQT = True
        # print('using module PyQt6')
    elif importlib.util.find_spec("PySide6"):
        # Use PySide6
        import PySide6 as PyQt
        from PySide6.QtCore import (
            QObject, QCoreApplication, QDate, QDateTime, QLocale,
            QMetaObject, QPoint, QRect,
            QSize, QTime, QUrl, Qt, QSettings, Signal, Slot)
        from PySide6.QtGui import (
            QBrush, QColor, QConicalGradient,
            QCursor, QFont, QFontDatabase, QGradient,
            QIcon, QImage, QKeySequence, QLinearGradient,
            QPainter, QPalette, QPixmap, QRadialGradient,
            QTransform, QTextCursor, QAction)
        from PySide6.QtWidgets import (
            QAbstractItemView, QAbstractScrollArea, QScrollArea,
            QApplication, QDialog, QFrame,
            QMessageBox, QFileDialog,
            QFormLayout, QGridLayout, QHBoxLayout, QVBoxLayout, QLayout,
            QMainWindow, QMenu, QMenuBar, QStatusBar, QProgressBar, QHeaderView,
            QLabel, QLineEdit, QPlainTextEdit,
            QPushButton, QToolButton, QListWidget, QListWidgetItem,
            QSpacerItem, QWidget, QSizePolicy)
        from PySide6.QtXml import (
            QDomDocument, QDomElement)
        PYSIDE = True
        # print('using module PySide6')
    elif importlib.util.find_spec("PyQt5"):
        # Use PyQt5
        import PyQt5 as PyQt
        from PyQt5.QtCore import (
            QObject, QCoreApplication, QSettings,
            Qt, QSize, QRect, QMetaObject,
            pyqtSignal as Signal, pyqtSlot as Slot)
        from PyQt5.QtGui import (
            QIcon, QPixmap, QImage, QFont, QColor, QTextCursor)
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QWidget, QFrame,
            QDialog, QMessageBox, QFileDialog,
            QLayout, QFormLayout, QGridLayout,
            QVBoxLayout, QHBoxLayout,
            QSizePolicy, QSpacerItem,
            QAbstractItemView, QAbstractScrollArea, QScrollArea,
            QLabel, QLineEdit, QPlainTextEdit,
            QPushButton, QToolButton, QListWidget, QListWidgetItem,
            QProgressBar, QMenuBar, QStatusBar, QMenu, QAction)
        from PyQt5.QtXml import (
            QDomDocument, QDomElement)
        # from PyQt6.QtWidgets import QMainWindow
        PYQT = True
        # print('using module PyQt6')
    elif importlib.util.find_spec("PySide2"):
        # Use PySide2
        import PySide2 as PyQt
        from PySide2.QtCore import (
            QObject, QCoreApplication, QDate, QDateTime, QLocale,
            QMetaObject, QPoint, QRect,
            QSize, QTime, QUrl, Qt, QSettings, Signal, Slot)
        from PySide2.QtGui import (
            QBrush, QColor, QConicalGradient,
            QCursor, QFont, QFontDatabase, QGradient,
            QIcon, QImage, QKeySequence, QLinearGradient,
            QPainter, QPalette, QPixmap, QRadialGradient,
            QTransform, QTextCursor, QAction)
        from PySide2.QtWidgets import (
            QAbstractItemView, QAbstractScrollArea, QScrollArea,
            QApplication, QDialog, QFrame,
            QMessageBox, QFileDialog,
            QFormLayout, QGridLayout, QHBoxLayout, QVBoxLayout, QLayout,
            QMainWindow, QMenu, QMenuBar, QStatusBar, QProgressBar, QHeaderView,
            QLabel, QLineEdit, QPlainTextEdit,
            QPushButton, QToolButton, QListWidget, QListWidgetItem,
            QSpacerItem, QWidget, QSizePolicy)
        from PySide2.QtXml import (
            QDomDocument, QDomElement)
        PYSIDE = True
        # print('using module PySide2')
except ModuleNotFoundError:
    error = str(sys.exc_info())
    print(f"Error loading Python Qt module: {error}")


# Class definition to get loaded Python module version information
class pyqt():
    def __init__(self):
        pass

    def isPyQGIS():
        return PYQGIS

    def isPyQt():
        return PYQT

    def isPySide():
        return PYSIDE

    def isQt():
        return PYQGIS or PYQT or PYSIDE

    def qtVersion():
        # get active Qt version
        if PYSIDE:
            return PyQt.QtCore.__version__
        if PYQT:
            return PyQt.QtCore.QT_VERSION_STR
        if PYQGIS:
            return PyQt.QtCore.QT_VERSION_STR
        return "module pyqt or pyside not found."

    def pyqtVersion():
        # get pyqt module version
        if PYSIDE:
            return PyQt.__version__
        if PYQT:
            return PyQt.QtCore.PYQT_VERSION_STR
        if PYQGIS:
            return PyQt.QtCore.PYQT_VERSION_STR
        return "module pyqt or pyside not found."

    def pyVersion():
        # get Python version
        return sys.version
# /pyqt


# Log module version information to console
print(f"Python v.{pyqt.pyVersion()}")
if pyqt.isQt():
    print(f"Qt v.{pyqt.qtVersion()}")
    if pyqt.isPyQGIS():
        print(
            f"QGIS.PyQt v.{pyqt.pyqtVersion()}")
    elif pyqt.isPyQt():
        print(
            f"PyQt v.{pyqt.pyqtVersion()}")
    elif pyqt.isPySide():
        print(
            f"PySide v.{pyqt.pyqtVersion()}")
else:
    print(
        "No Python module found for Qt:\n"
        "\tInstall Python PyQt, or Python PySide, "
        "from your operating system distibution.")
if PYQGIS:
    print(f"QGIS v.{Qgis.version()}")
else:
    print(
        "Python module PyQGIS not found:\n"
        "\tAdd the location of your installed QGIS Python modules"
        " to your environment variable PYTHONPATH\n"
        "\teg. for Linux: PYTHONPATH=/usr/share/qgis/python:$PYTHONPATH")
