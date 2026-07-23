# -*- coding: utf-8 -*-
# Created on : 30/11/2024, 10:10:24 pm
# Author     : Grant Pearson, Eureka Technology Limited

import os
import socket
from urllib.parse import urlsplit
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

if importlib.util.find_spec("linz_schema_utilities"):
    from linz_schema_utilities import MessageBoxes, Utilities
else:
    from .linz_schema_utilities import MessageBoxes, Utilities

DATABASES = ["mysql", "mariadb"]
FILESOURCES = ["sqlite", "gpkg",
               "csv"]
DBA_PASSWORD = None

# attempt to import the relevant database libraries
try:
    import mariadb
    mysql_connect = mariadb.connect
    mysql_error = mariadb
    HAS_MARIADB = True
    # print('using module mariadb')
except ImportError:
    HAS_MARIADB = False

if HAS_MARIADB:
    HAS_MYSQL = False
else:
    try:
        from MySQLdb import _mysql
        mysql_connect = _mysql.connect
        mysql_error = _mysql
        HAS_MYSQL = True
        # print('using module MySQLdb')
    except ImportError:
        HAS_MYSQL = False

if HAS_MARIADB or HAS_MYSQL:
    HAS_PYMYSQL = False
else:
    try:
        import pymysql
        mysql_connect = pymysql.connect
        mysql_error = pymysql
        HAS_PYMYSQL = True
        # print('using module pymysql')
    except ImportError:
        HAS_PYMYSQL = False
if HAS_MARIADB:
    from mariadb.constants.ERR import ER_DUP_ENTRY as ER_DUP_ENTRY
elif HAS_MYSQL:
    from MySQLdb.constants.ER import DUP_ENTRY as ER_DUP_ENTRY
elif HAS_PYMYSQL:
    from pymysql.constants.ER import DUP_ENTRY as ER_DUP_ENTRY
else:
    ER_DUP_ENTRY = -1024


class SQLError(Exception):
    def __init__(self, errType, errText, errNo, errSql):
        self.errType = errType
        self.errText = errText
        self.errNo = errNo
        self.errSql = errSql
        super().__init__(self.errType)

    def __str__(self):
        return f'{self.errType}: {self.errText}'
# /SQLError


class SourceConfig():
    """ Class to store layer database source connection details.
    """
    """'Type' definition for database server connections.
    To avoid warning of "Possible hardcoded password: 'None'":
        'username' is translated to 'u'
        'password' is translated to 'p'
    """
    sourceConfig = {
        "databasetype": None,
        "u": None,
        "p": None,
        "hostname": None,
        "port": None,
        "databasename": None,
        "tablename": None,
        "path": None
    }

    def __init__(self):
        pass

    def __str__(self):
        return f'{self.sourceConfig}'

    # set a key value
    def setKey(self, key, value):
        k = key.lower()
        if k.endswith('type'):
            tp = ('databasetype', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('user') or k == 'usr':
            tp = ('u', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('pass') or k == 'pwd':
            tp = ('p', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('host') or k.startswith('server') or k == 'dsn':
            tp = ('hostname', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('port'):
            tp = ('port', value)
            self.sourceConfig.__setitem__(*tp)
        if k == 'database' or k == 'databasename' or \
           k.startswith('schema') or k.startswith('db'):
            tp = ('databasename', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('table') or k.startswith('view'):
            tp = ('tablename', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('uri') or k.endswith('path'):
            tp = ('path', value)
            self.sourceConfig.__setitem__(*tp)
    # /setKey

    # return the key value
    def get(self, key):
        if key is None:
            return None
        if key == 'username':
            return self.sourceConfig.get('u')
        if key == 'password':
            return self.sourceConfig.get('p')
        return self.sourceConfig.get(key)
    # /get

    def getConfig(self):
        return self.sourceConfig
    # /getConfig

    # clear all key values
    def clearAll(self):
        self.setKey("databasetype", None)
        self.setKey("username", None)
        self.setKey("password", None)
        self.setKey("hostname", None)
        self.setKey("port", None)
        self.setKey("databasename", None)
        self.setKey("tablename", None)
        self.setKey("path", None)
    # /clearAll
# /SourceConfig


class Field():
    """'Type' definition for database field.
    """
    fieldName = None
    fieldSrc = None
    fieldType = None
    fieldWidth = None
    isKey = False

    def __init__(self, name=None, source=None, type=None, width=None,
                 isKey=False):
        self.fieldName = name
        self.fieldSrc = source
        self.fieldType = type
        self.fieldWidth = width
        self.isKey = isKey

    def __str__(self):
        return f'{self.fieldName} : {self.fieldSrc} : ' \
            '{self.fieldType} : {self.fieldWidth} : {self.isKey}'


class Database():
    DUP_ENTRY = ER_DUP_ENTRY

    def isDatabase(storageType):
        """Test if a layer source type is a supported database
        :param storageType: Data source database type.
        :type storageType: str, QString

        :returns: True if database source type is supported.
        :rtype: Boolean
        """
        if storageType:
            if storageType.lower() in DATABASES:
                return True
        return False
    # /isDatabase

    def defaultPort(storageType):
        """Get default port number for database tcp connection.
        :param storageType: Storage database type.
        :type storageType: str

        :returns: Default port number for database type.
        :rtype: str
        """
        if storageType == "mysql" or storageType == "mariadb":
            return '3306'
        return None
    # /defaultPort

    def defaultUsername(storageType):
        """Get default dba username for database tcp connection.
        :param storageType: Storage database type.
        :type storageType: str

        :returns: Default dba username for database type.
        :rtype: str
        """
        if storageType == "mysql" or storageType == "mariadb":
            return 'root'
        return 'system'
    # /defaultUsername

    def defaultPassword(storageType):
        """Get default dba password for database tcp connection.
        :param storageType: Storage database type.
        :type storageType: str

        :returns: Default dba password for database type.
        :rtype: str
        """
        if storageType == "mysql" or storageType == "mariadb":
            return DBA_PASSWORD
        return 'manager'
    # /defaultPassword

    def convertFieldType(value, type):
        """Convert from database field type.
        :param value: Field value.
        :type value: object

        :param type: Field type.
        :type type: str

        :returns: Value converted to python type.
        :rtype: object
        """
        if value:
            if type.lower().startswith('int'):
                newValue = int(value)
            elif type.lower().startswith('dec'):
                newValue = float(value)
            elif type.lower().startswith('real'):
                newValue = float(value)
            elif type.lower().startswith('float'):
                newValue = float(value)
            else:
                newValue = value
            return newValue
        return None
    # /convertFieldType

    def isSchemaExist(parent, cnx, schemaname):
        sql = "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA " \
              f"WHERE SCHEMA_NAME='{schemaname}';"
        result = Database.readDatabaseResult(parent, cnx, sql)
        if result is None:
            return False
        return (schemaname == result)
    # /isSchemaExist

    """
    def isTableExist(self, schemaname, tablename):
        sql = "SELECT t.TABLE_NAME " \
            "FROM information_schema.TABLES t "
        sql += f"WHERE t.TABLE_SCHEMA='{schemaname}' "
        sql += f"AND t.TABLE_NAME='{tablename}';"
        result = Database.readDatabaseResult(self, self.cnx, sql)
        if result:
            if result == tablename:
                return True
        return False
    # /isTableExist
    """

    def isTableExist(parent, cnx, schemaname, tablename):
        """Test if table exists.
        """
        sql = "SELECT count(TABLE_NAME) " \
              "FROM information_schema.TABLES " \
              f"WHERE TABLE_SCHEMA='{schemaname}' "\
              f"AND TABLE_NAME='{tablename}';"
        exist = Database.readDatabaseResult(parent, cnx, sql, True)
        if exist is None:
            return False
        return (exist > 0)
    # /isTableExist

    def isDataExist(parent, cnx, schemaname, tablename):
        """Test if any rows exist in table.
        """
        sql = "SELECT ifnull(EXISTS(" \
              f"SELECT 1 FROM {schemaname}.{tablename}), 0);"
        exist = Database.readDatabaseResult(parent, cnx, sql, True)
        if exist is None:
            return False
        return (exist == 1)
    # /isDataExist

    def readDatabaseResult(parent, cnx, sql, silent=False):
        """Read result from MySQL/MariaDB database server.
        """
        value = None
        try:
            if HAS_MYSQL:
                cnx.query(f"""{sql}""")
                rows = cnx.store_result()
                results = rows.fetch_row(1, 1)
                for result in results:
                    value = result[0]
                # print(f'[0] : {value}')
            else:
                cur = cnx.cursor()
                cur.execute(sql)
                for result in cur:
                    value = result[0]
                cur.close()
                # print(f'[0] : {value}')
        except (mariadb.Error, mariadb.ProgrammingError) as err:
            msg = "Failed to read from MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            if silent:
                pass
            else:
                parent.appendLog(f'{sql}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
        except (mysql_connect.Error) as err:
            msg = "Failed to read from MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            if silent:
                pass
            else:
                parent.appendLog(f'{sql}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
        return value
    # /readDatabaseResult

    def readDatabase(parent, cnx, sql, silent=False):
        """Read data from MySQL/MariaDB database server.
        Calls readDatabase for each supported database.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param cnx: Database connection.
        :type cnx: SourceConfig

        :param sql: SQL query statement.
        :type sql: str
        """

        try:
            if HAS_MYSQL:
                cnx.query(f"""{sql}""")
                rows = cnx.store_result()
                results = rows.fetch_row(rows.rowcount, 1)
                return results
            else:
                cur = cnx.cursor()
                cur.execute(sql)
                results = cur.fetchall()
                cur.close()
                return results
        except (mariadb.Error, mariadb.ProgrammingError) as err:
            msg = "Failed to read from MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            if silent:
                pass
            else:
                parent.appendLog(f'{sql}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
        except (mysql_connect.Error) as err:
            msg = "Failed to read from MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            if silent:
                pass
            else:
                parent.appendLog(f'{sql}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
        return None
    # /readDatabase

    def executeSQL(parent, cnx, sql, silent=False, logOnly=True):
        """Execute SQL statement on MySQL/MariaDB database server.
        """
        try:
            if HAS_MYSQL:
                cnx.query(f"""{sql}""")
            else:
                cur = cnx.cursor()
                cur.execute(sql)
                cur.close()
            if silent:
                pass
            else:
                parent.appendLog('ok')
            success = True
        except (mariadb.IntegrityError,
                mysql_error.IntegrityError) as err:
            # print(f'IntegrityError\n{err}\n{sql}')
            if err:
                if f'{err}'.upper().find("DUPLICATE") < 0:
                    errno = err.errno
                else:
                    errno = ER_DUP_ENTRY
            else:
                errno = 0
            if silent:
                raise SQLError(err.sqlstate, err.msg, errno, sql)
            msg = "Failed to execute SQL statement on " \
                "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\nSQLERR: {errno} {err.msg}')
            # parent.appendLog(f'{sql}')
            if logOnly:
                pass
            else:
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    Utilities.getApptitle(parent),
                    f'{msg}\nSQLERR: {errno} {err.msg}')
            success = False
        except (mariadb.Error,
                mariadb.ProgrammingError,
                mariadb.OperationalError,
                mysql_error.Error) as err:
            if silent:
                raise SQLError(err.sqlstate, err.msg, err.errno, sql)
            msg = "Failed to execute SQL statement on " \
                  "MariaDB/MySQL database:"
            # print(f'{msg}\n{err}\n{sql}')
            parent.appendLog(f'{msg}\nSQLERR: {err.errno} {err.msg}')
            # parent.appendLog(f'{sql}')
            if logOnly:
                pass
            else:
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    Utilities.getApptitle(parent),
                    f'{msg}\nSQLERR: {err.errno} {err.msg}')
            success = False
        return success
    # /executeSQL

    def executeSQLwithWarnings(parent, cnx, sql):
        """Execute SQL statement on MySQL/MariaDB database server.
        """
        try:
            if HAS_MYSQL:
                cnx.query(f"""{sql}""")
            else:
                cur = cnx.cursor()
                cur.execute(sql)
                cur.close()
            sqlW = "SHOW WARNINGS;"
            warnings = Database.readDatabase(parent, cnx, sqlW, True)
            if warnings:
                for w in warnings:
                    parent.appendLog(f"{w}")
            else:
                parent.appendLog("ok")
            success = True
        except (mariadb.IntegrityError,
                mysql_error.IntegrityError) as err:
            if err:
                if f'{err}'.upper().find("DUPLICATE") < 0:
                    errno = err.errno
                else:
                    errno = ER_DUP_ENTRY
            else:
                errno = 0
            msg = "Failed to execute SQL statement on " \
                "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err.sqlstate}: {errno} {err.msg}')
            # parent.appendLog(f'{sql}')
            success = False
        except (mariadb.Error,
                mariadb.ProgrammingError,
                mysql_error.Error) as err:
            msg = "Failed to execute SQL statement on " \
                  "MariaDB/MySQL database:"
            # print(f'{msg}\n{err}\n{sql}')
            parent.appendLog(f'{msg}\n{err.sqlstate}: {err.errno} {err.msg}')
            # parent.appendLog(f'{sql}')
            success = False
        return success
    # /executeSQLwithWarnings

    def commit(parent, cnx):
        """Commit database changes.
        """
        return Database.executeSQL(parent, cnx, 'COMMIT;', True)
    # /commit

    def rollback(parent, cnx):
        """Commit database changes.
        """
        return Database.executeSQL(parent, cnx, 'ROLLBACK;', True)
    # /rollback

    def connectDatabase(parent, sourceConfig):
        """Connect to MySQL/MariaDB database server.
        """
        host = sourceConfig.get("hostname")
        local = host.lower() == "localhost" \
            or host == socket.gethostname() \
            or host == socket.gethostbyname(socket.gethostname()) \
            or host == "127.0.0.1"
        if local:  # force local_infile=True for all load hosts
            config = {
                "host": host,
                "port": int(sourceConfig.get("port")),
                "user": sourceConfig.get("username"),
                "password": sourceConfig.get("password"),
                "database": sourceConfig.get("databasename"),
                "local_infile": 1
            }
        else:
            config = {
                "host": host,
                "port": int(sourceConfig.get("port")),
                "user": sourceConfig.get("username"),
                "password": sourceConfig.get("password"),
                "database": sourceConfig.get("databasename"),
                "local_infile": 1
            }
        try:
            cnx = mysql_connect(**config)
        except (mariadb.OperationalError) as err:
            msg = "Failed to connect to MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
            return None
        except (mariadb.Error, mysql_connect.Error) as err:
            msg = "Failed to connect to MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
            return None
        except () as err:
            msg = "Failed to connect to MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
            return None
        if cnx:  # timeout after 24hours
            sql = "SET SESSION wait_timeout=86400;"
            Database.executeSQL(parent, cnx, sql, False)
        return cnx
    # /connectDatabase

    def disconnectDatabase(parent, cnx):
        """Disconnect from MySQL/MariaDB database server.
        """
        if Database.isConnected(cnx):
            cnx.close()
    # /disconnectDatabase

    def getHostDB(parent, cnx):
        if cnx:
            try:
                sql = "select @@hostname;"
                host = Database.readDatabaseResult(parent, cnx, sql, True)
                return host
            except ():
                return None
        return None
    # /getHostDB

    def getDBVersion(parent, cnx):
        if cnx:
            try:
                sql = "select version();"
                db = Database.readDatabaseResult(parent, cnx, sql, True)
                return db
            except ():
                return None
        return None
    # /getDBVersion

    def getUsername(parent, cnx):
        if cnx:
            try:
                sql = "SELECT SUBSTRING_INDEX(user(), '@', 1);"
                user = Database.readDatabaseResult(parent, cnx, sql, True)
                return user
            except ():
                return None
        return None
    # /getUsername

    def getTables(parent, cnx, schema):
        if cnx:
            sql = "SELECT table_name " \
                "FROM INFORMATION_SCHEMA.TABLES " \
                f"WHERE TABLE_SCHEMA='{schema}' " \
                "AND table_type ='BASE TABLE' " \
                "AND table_name !='geometry_columns' " \
                "AND table_name !='spatial_ref_sys' " \
                "AND table_name !='table_datasets' " \
                "order by table_name asc;"
            tables = Database.readDatabase(parent, cnx, sql)
            return tables
        return None
    # /getTables

    def getTableMetadataCount(parent, cnx, schema, tablename):
        if cnx:
            try:
                sql = "SELECT ifnull(table_rows, -1) " \
                      "FROM INFORMATION_SCHEMA.TABLES " \
                      f"WHERE TABLE_SCHEMA='{schema}' " \
                      f"AND table_name='{tablename}';"
                cnt = Database.readDatabaseResult(parent, cnx, sql, True)
                if cnt is None:
                    return -1
                return cnt
            except ():
                return -1
        return -1
    # /getTableMetadataCount

    def isLocalDB(parent, cnx):
        if cnx:
            try:
                sql = "select @@hostname"
                host = Database.readDatabaseResult(parent, cnx, sql, True)
                local = host == "localhost" \
                    or host == socket.gethostname() \
                    or host == socket.gethostbyname(socket.gethostname()) \
                    or host == "127.0.0.1"
                return local
            except ():
                return False
        return False
    # /isLocalDB

    def isConnected(cnx):
        if cnx:
            if HAS_MARIADB:
                try:
                    cnx.ping()
                except mariadb.InterfaceError:
                    return False
                return True
            if HAS_MYSQL:
                return cnx.isConnected()
            if HAS_PYMYSQL:
                return cnx.open
        return False
    # /isConnected

    def extractSourceURI(storageType, uriComponents):
        """Extract source connection information from a
        vector layer source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        # print(f'extractSourceURI\nuriComponents:\n\t{uriComponents}')
        if uriComponents:
            # print(f'storageType={storageType} : '
            #       'isDatabase={Utilities.isDatabase(storageType)}')
            s = storageType.upper()
            if Database.isDatabase(storageType):
                if s == "ODBC":
                    return Database.extractODBCSourceURI(
                        storageType, uriComponents)
                else:
                    return Database.extractDatabaseSourceURI(
                        storageType, uriComponents)
            elif Database.isFileSource(storageType):
                return Database.extractFileSourceURI(
                    storageType, uriComponents)
            elif s == "GPX" or s == "ESRI SHAPEFILE":
                return Database.extractShapeSourceURI(
                    storageType, uriComponents)
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        return sourceConfig
    # /extractSourceURI

    def extractODBCSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        ODBC layer source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        urlParts = urlsplit(uriComponents["path"])
        username = None
        password = None
        path = uriComponents['databaseName']
        if path is None:
            path = urlParts.path
        sourceConfig.setKey('path', path)
        if path:
            sep = path.find('@')
            length = len(path)
            if sep == 0:
                path = path[1:length]
            elif sep > 0:
                authentication = path[0:sep]
                path = path[sep + 1:length]
                sep = authentication.find('/')
                length = len(authentication)
                if sep == 0:
                    username = authentication[1:length]
                elif sep > 0:
                    username = authentication[0:sep]
                    password = authentication[sep + 1:length]
        sourceConfig.setKey('username', username)
        sourceConfig.setKey('password', password)
        sourceConfig.setKey('databasename', path)
        tableName = uriComponents['layerName']
        sourceConfig.setKey('tablename', tableName)
        if urlParts.hostname:
            sourceConfig.setKey('hostname', urlParts.hostname)
        if urlParts.port:
            sourceConfig.setKey('port', urlParts.port)
        return sourceConfig
    # /extractODBCSourceURI

    def extractDatabaseSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        database layer source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        try:
            databaseName = uriComponents['databaseName']
            sourceConfig.setKey('databasename', databaseName)
            urlParts = urlsplit(uriComponents['path'])
            path = urlParts.path
            sourceConfig.setKey('path', path)
            if urlParts.username:
                sourceConfig.setKey('username', urlParts.username)
            if urlParts.password:
                sourceConfig.setKey('password', urlParts.password)
            if urlParts.hostname:
                sourceConfig.setKey('hostname', urlParts.hostname)
            if urlParts.port:
                sourceConfig.setKey('port', urlParts.port)
            else:
                sourceConfig.setKey(
                    'port', Database.defaultPort(storageType.lower()))
            components = path.split(',')
            for component in components:
                if component.find('=') > 0:
                    c = component.split('=', 1)
                    sourceConfig.setKey(c[0], c[1])
        except KeyError:
            pass
        return sourceConfig
    # /extractDatabaseSourceURI

    def extractFileSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        file source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        databaseName = uriComponents['path']
        sourceConfig.setKey('databasename', databaseName)
        urlParts = urlsplit(uriComponents["path"])
        path = urlParts.path
        sourceConfig.setKey('path', path)
        return sourceConfig
    # /extractFileSourceURI

    def extractShapeSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        file source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """

        # print(f'\tstorageType={storageType}\t{uriComponents}')
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        try:
            path = uriComponents['vsiSuffix']
        except KeyError:
            path = uriComponents['path']
        if path:
            (root, ext) = os.path.splitext(path)
            (root, file) = os.path.split(root)
            sourceConfig.setKey('path', file)
        # print(f'path={path}\troot={root}\tfile={file}\text={ext}')
        return sourceConfig
    # /extractShapeSourceURI

    def isFileSource(storageType):
        """Test if a layer source type is a supported database
        :param storageType: Data source database type.
        :type storageType: str, QString

        :returns: True if database source type is supported.
        :rtype: Boolean
        """
        if storageType:
            if storageType.lower() in FILESOURCES:
                return True
        return False
    # /isFileSource

    def isDatabaseConnector():
        if HAS_MARIADB or HAS_MYSQL or HAS_PYMYSQL:
            return True
        return False
    # /isDatabaseConnector

    def getConnectorVersion():
        if HAS_MARIADB:
            return mariadb.__version__
        elif HAS_MYSQL:
            return _mysql.__version__
        elif HAS_PYMYSQL:
            return pymysql.__version__
        return ''
    # /getConnectorVersion

    def isMariadb():
        return HAS_MARIADB
    # /isMariadb

    def isMysql():
        return HAS_MYSQL
    # /isMysql

    def isPyMysql():
        return HAS_PYMYSQL
    # /isPyMysql
# /Database
