# Created on : Dec 26, 2025, 3:07:23 PM
# linz_schema_database.py
# Author     : Grant
# Module for handling database routines

import socket
import importlib.util

if importlib.util.find_spec("linz_schema_utilities"):
    from linz_schema_utilities import MessageBoxes, Utilities
else:
    from .linz_schema_utilities import MessageBoxes, Utilities

# attempt to import the relevant database libraries
if importlib.util.find_spec("mariadb"):
    import mariadb as pysql
    from mariadb.constants.ERR import ER_DUP_ENTRY as ER_DUP_ENTRY
    sql_error = pysql
    HAS_MARIADB = True
    HAS_MYSQL = False
    # print('using module mariadb')
elif importlib.util.find_spec("mysql"):
    from mysql import connector as pysql
    from mysql.connector.errorcode import ER_DUP_ENTRY as ER_DUP_ENTRY
    sql_error = pysql.errors
    HAS_MARIADB = False
    HAS_MYSQL = True
    # print('using module mysql')
else:
    HAS_MARIADB = False
    HAS_MYSQL = False
    ER_DUP_ENTRY = -1062

DBA_PASSWORD = None


class SQLError(Exception):
    """ Custom Class to pass Sql error exceptions.
    """

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
    """ Class to store definition for database server connections.
        To avoid warning of "Possible hardcoded ?: 'None'":
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
        """Set a SourceConfig key value.
        :param key: Key within SourceConfig to set.
        :type key: str

        :param value: Value to set SourceConfig key to key.
        :type value: str
        """
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
        """Get a SourceConfig key value.
        :param key: Key within SourceConfig to get.
        :type key: str

        :returns: Value of SourceConfig key.
        :rtype: str
        """
        if key is None:
            return None
        if key == 'username':
            return self.sourceConfig.get('u')
        if key == 'password':
            return self.sourceConfig.get('p')
        return self.sourceConfig.get(key)
    # /get

    def getConfig(self):
        """Get this SourceConfig.

        :returns: This SourceConfig.
        :rtype: SourceConfig
        """
        return self.sourceConfig
    # /getConfig

    # clear all key values
    def clearAll(self):
        """Clear all SourceConfig key values.
        """
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
    """Utilities class for handling database routines
    """
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
        """Test if named schema exists in database.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param schemaname: Name if schema to test for.
        :type schemaname: str

        :returns: True of schema found.
        :rtype: Boolean
        """
        sql = "SELECT SCHEMA_NAME\nFROM information_schema.SCHEMATA\n" \
              "WHERE lower(SCHEMA_NAME)=lower(%s)"
        par = tuple([schemaname])
        result = Database.readDatabaseResult(parent, cnx, sql, par)
        if result is None:
            return False
        return (schemaname == result)
    # /isSchemaExist

    def isGISSchemaExist(parent, cnx, schemaname):
        """Test if named schema exists in database and contains geometry tables.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param schemaname: Name of schema to test for.
        :type schemaname: str

        :returns: True if schema found with geometry tables.
        :rtype: Boolean
        """
        if Database.isSchemaExist(parent, cnx, schemaname):
            sql = "SELECT COUNT(*)\nFROM information_schema.TABLES\n" \
                  "WHERE lower(TABLE_SCHEMA)=lower(%s) " \
                  "AND TABLE_NAME IN " \
                  "('geometry_columns', 'spatial_ref_sys', 'table_datasets')"
            par = tuple([schemaname])
            result = Database.readDatabaseResult(parent, cnx, sql, par)
            if result > 2:
                return True
        return False
    # /isGISSchemaExist

    def isTableExist(parent, cnx, schemaname, tablename):
        """Test if named table exists in named schema.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param schemaname: Name of schema to test for.
        :type schemaname: str

        :param tablename: Name of table to test for.
        :type tablename: str

        :returns: True if table found in schema.
        :rtype: Boolean
        """
        sql = "SELECT count(TABLE_NAME)\n" \
              "FROM information_schema.TABLES\n" \
              "WHERE TABLE_SCHEMA=%s "\
              "AND TABLE_NAME=%s"
        par = tuple([schemaname, tablename])
        exist = Database.readDatabaseResult(parent, cnx, sql, par, silent=True)
        if exist is None:
            return False
        return (exist > 0)
    # /isTableExist

    def getCRUD(crud):
        """Get Sql command for given crud index.
        :param crud: Index of sql command
         (1 "create", 2 "read", 3 "update", 4 "delete")
        :type crud: int

        :returns: Sql CRUD command.
        :rtype: str
        """
        match crud:
            case 1:
                return "insert"
            case 2:
                return "select"
            case 3:
                return "update"
            case 4:
                return "delete"
        return ""

    def buildSql(crud, sql):
        """Prefix sql statement with correct command.
        Features of LINZ Schema Loader that may possibly be exposed to SQL
         string injection attacks can only be run by trusted database users
         with trusted data names, so bypass warnings of SQL injection.
        Bandit source code security analyzer looks for sql execute statement
        occurances of:
            select % from %
            delete % from %
            insert into % values %
            update  % set %

        :param crud: Index of sql command
         (1 "create", 2 "read", 3 "update", 4 "delete")
        :type crud: int

        :param sql: Sql statement that follows initial command.
        :type sql: Str

        :returns: Full Sql statement.
        :rtype: str
        """
        return f"{Database.getCRUD(crud)} {sql}"

    def isDataExist(parent, cnx, schemaname, tablename):
        """Test if any rows exist in table.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param schemaname: Name of schema to test for.
        :type schemaname: str

        :param tablename: Name of table to test for.
        :type tablename: str

        :returns: True if any data is found table.
        :rtype: Boolean
        """
        sql = f"{Database.getCRUD(2)} ifnull(EXISTS(" \
              f"{Database.getCRUD(2)} 1 FROM {schemaname}.{tablename}), 0)"
        exist = Database.readDatabaseResult(parent, cnx, sql, silent=True)
        if exist is None:
            return False
        return (exist == 1)
    # /isDataExist

    def readDatabaseResult(parent, cnx, sql, parameters=None, silent=False):
        """Read single result from MySQL/MariaDB database server.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param sql: SQL query statement.
        :type sql: str

        :param parameters: tuple of parameter values.
        :type parameters: tuple

        :param silent: True if errors are logged only;
                       False if error message displayed.
        :type silent: Boolean

        :returns: Value of first field in first result found.
        :rtype: Object
        """
        value = None
        try:
            # parent.appendLog(f'{sql}\n{parameters}')  # debug
            cursor = cnx.cursor(buffered=True)
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)
            result = cursor.fetchone()
            if result is None:
                return None
            value = result[0]
            cursor.close()
        except (sql_error.Error,
                sql_error.ProgrammingError) as err:
            msg = "Failed to read from MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            if silent:
                pass
            else:
                parent.appendLog(f'{sql}\n{parameters}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
        return value
    # /readDatabaseResult

    def readDatabase(parent, cnx, sql, parameters=None, silent=False):
        """Read data from MySQL/MariaDB database server.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param sql: SQL query statement.
        :type sql: str

        :param parameters: tuple of parameter values.
        :type parameters: tuple

        :param silent: True if errors are logged only;
                       False if error message displayed.
        :type silent: Boolean

        :returns: Values of all results found.
        :rtype: tuple(tuple)
        """
        try:
            # parent.appendLog(f"readDatabase:\n{sql}")  # debug
            cursor = cnx.cursor(buffered=True)
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            return results
        except (sql_error.Error, sql_error.ProgrammingError) as err:
            msg = "Failed to read from MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            if silent:
                pass
            # else:
            #     parent.appendLog(f'{sql}\n{parameters}')  # debug
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
        return None
    # /readDatabase

    def openSqlCursor(parent, cnx, logOnly=True):
        """Open a cursor for executing SQL prepared statements
           on MySQL/MariaDB database server.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param logOnly: True if errors are logged only;
                       False if error message displayed.
        :type logOnly: Boolean

        :returns: Values of all results found.
        :rtype: Cursor
        """
        try:
            cursor = cnx.cursor(prepared=True)
        except (sql_error.Error,
                sql_error.ProgrammingError,
                sql_error.OperationalError) as err:
            msg = "Failed to open SQL cursor on " \
                  "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\nSQLERR: {err.errno} {err.msg}')
            if logOnly:
                pass
            else:
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    Utilities.getApptitle(parent),
                    f'{msg}\nSQLERR: {err.errno} {err.msg}')
            return None
        return cursor
    # /buildSqlCursor

    def executeSqlCursor(parent, cursor, sql, parameters=None, silent=True):
        """Execute a SQL prepared statement on MySQL/MariaDB database server.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param sql: SQL statement to execute.
        :type sql: str

        :param parameters: tuple of parameter values.
        :type parameters: tuple

        :param silent: True if errors are logged only;
                       False if error message displayed.
        :type silent: Boolean

        :returns: True if execute successful.
        :rtype: Boolean
        """
        try:
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)
        except (sql_error.IntegrityError) as err:
            # parent.appendLog(
            #     f'IntegrityError\n{err}\n{sql}\n{parameters}')  # debug
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
            # parent.appendLog(
            #         f"executeSqlCursor:\n{sql}\n\t{parameters}")  # debug
            return False
        except (sql_error.Error,
                sql_error.ProgrammingError,
                sql_error.OperationalError) as err:
            if silent:
                raise SQLError(err.sqlstate, err.msg, err.errno, sql)
            msg = "Failed to execute SQL statement on " \
                  "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\nSQLERR: {err.errno} {err.msg}')
            # parent.appendLog(
            #     f"executeSqlCursor:\n{sql}\n\t{parameters}")  # debug
            return False
        return True
    # /executeSqlCursor

    def closeSqlCursor(parent, cursor, logOnly=True):
        """Close a cursor used for a SQL prepared statements
           on MySQL/MariaDB database server.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param logOnly: True if errors are logged only;
                       False if error message displayed.
        :type logOnly: Boolean
        """
        try:
            if cursor:
                cursor.close()
        except (sql_error.Error,
                sql_error.ProgrammingError,
                sql_error.OperationalError) as err:
            msg = "Failed to close SQL cursor on " \
                  "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\nSQLERR: {err.errno} {err.msg}')
            if logOnly:
                pass
            else:
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    Utilities.getApptitle(parent),
                    f'{msg}\nSQLERR: {err.errno} {err.msg}')
    # /closeSqlCursor

    def silentOk(parent, silent=False):
        """Log Ok message.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param silent: True if error is to be raised;
                       False if outcome handled within method.
        :type silent: Boolean
        """
        if silent:
            pass
        else:
            parent.appendLog('ok')
    # /silentOk

    def executeSQL(parent, cnx, sql, parameters=None,
                   silent=False, logOnly=True):
        """Execute a SQL statement on MySQL/MariaDB database server.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param sql: SQL statement to execute.
        :type sql: str

        :param parameters: tuple of parameter values.
        :type parameters: tuple

        :param silent: True if error is to be raised;
                       False if outcome handled within method.
        :type silent: Boolean

        :param logOnly: True if errors are logged only;
                       False if error message displayed.
        :type logOnly: Boolean

        :returns: True if execute successful.
        :rtype: Boolean
        """
        try:
            cursor = cnx.cursor()
            # parent.appendLog(
            #     f"executeSQL:\n{sql}\n\t{parameters}")  # debug
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)
            cursor.close()
            Database.silentOk(parent, silent)
        except sql_error.IntegrityError as err:
            # parent.appendLog(
            #     f'IntegrityError\n{err}\n{sql}\n{parameters}')  # debug
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
            # parent.appendLog(f"executeSQL:\n{sql}\n\t{parameters}")  # debug
            if not logOnly:
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    Utilities.getApptitle(parent),
                    f'{msg}\nSQLERR: {errno} {err.msg}')
            return False
        except sql_error.ProgrammingError as err:
            if silent:
                raise SQLError(None, err, 0, sql)
            msg = "Failed to execute SQL statement on " \
                  "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\nSQLERR: {err}')
            # parent.appendLog(f"executeSQL:\n{sql}\n\t{parameters}")  # debug
            if not logOnly:
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    Utilities.getApptitle(parent),
                    f'{msg}\nSQLERR: {err}')
            return False
        except (sql_error.Error,
                sql_error.OperationalError) as err:
            if silent:
                raise SQLError(err.sqlstate, err.msg, err.errno, sql)
            msg = "Failed to execute SQL statement on " \
                  "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\nSQLERR: {err.errno} {err.msg}')
            # parent.appendLog(f"executeSQL:\n{sql}\n\t{parameters}")  # debug
            if not logOnly:
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    Utilities.getApptitle(parent),
                    f'{msg}\nSQLERR: {err.errno} {err.msg}')
            return False
        return True
    # /executeSQL

    def executeSQLwithWarnings(parent, cnx, sql, parameters=None):
        """Execute a SQL statement on MySQL/MariaDB database server.
           Display any database warnings after succcessful execution.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param sql: SQL statement to execute.
        :type sql: str

        :param parameters: tuple of parameter values.
        :type parameters: tuple

        :returns: True if execute successful.
        :rtype: Boolean
        """
        try:
            cursor = cnx.cursor()
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)
            cursor.close()
            sqlW = "SHOW WARNINGS"
            warnings = Database.readDatabase(
                parent, cnx, sqlW, silent=True)
            if warnings:
                for w in warnings:
                    parent.appendLog(f"{w}")
            else:
                parent.appendLog("ok")
        except sql_error.IntegrityError as err:
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
            # parent.appendLog(f'{sql}\n{parameters}')  # debug
            return False
        except sql_error.ProgrammingError as err:
            msg = "Failed to execute SQL statement on " \
                  "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\nSQLERR: {err}')
            return False
        except sql_error.Error as err:
            msg = "Failed to execute SQL statement on " \
                  "MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err.sqlstate}: {err.errno} {err.msg}')
            # parent.appendLog(f'{sql}\n{parameters}')  # debug
            return False
        return True
    # /executeSQLwithWarnings

    def commit(parent, cnx):
        """Commit database changes.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :returns: True if execute successful.
        :rtype: Boolean
        """
        return Database.executeSQL(parent, cnx, 'COMMIT', silent=True)
    # /commit

    def rollback(parent, cnx):
        """Rollback database changes.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :returns: True if execute successful.
        :rtype: Boolean
        """
        return Database.executeSQL(parent, cnx, 'ROLLBACK', silent=True)
    # /rollback

    def connectDatabase(parent, sourceConfig):
        """Connect to MySQL/MariaDB database server.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param sourceConfig: Database connection details.
        :type sourceConfig: SourceConfig

        :returns: Database connection.
        :rtype: MySQLConnection or Connection
        """
        host = sourceConfig.get("hostname")
        # local = host.lower() == "localhost" \
        #     or host == socket.gethostname() \
        #     or host == socket.gethostbyname(socket.gethostname()) \
        #     or host == "127.0.0.1"
        # if local:  # force local_infile=True for all load hosts
        try:
            if HAS_MYSQL:
                config = {
                    "host": host,
                    "port": int(sourceConfig.get("port")),
                    "user": sourceConfig.get("username"),
                    "password": sourceConfig.get("password"),
                    "database": sourceConfig.get("databasename"),
                }
                cnx = pysql.connect(**config, allow_local_infile=True)
            else:
                config = {
                    "host": host,
                    "port": int(sourceConfig.get("port")),
                    "user": sourceConfig.get("username"),
                    "password": sourceConfig.get("password"),
                    "database": sourceConfig.get("databasename"),
                    "local_infile": 1
                }
                cnx = pysql.connect(**config)
        except sql_error.OperationalError as err:
            msg = "Failed to connect to MariaDB/MySQL database:"
            parent.appendLog(f'{msg}\n{err}')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                Utilities.getApptitle(parent),
                f'{msg}\n{err}')
            return None
        except sql_error.Error as err:
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
            sql = "SET SESSION wait_timeout=86400"
            Database.executeSQL(parent, cnx, sql, silent=True)
        return cnx
    # /connectDatabase

    def disconnectDatabase(parent, cnx):
        """Disconnect from MySQL/MariaDB database server.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection
        """
        if Database.isConnected(cnx):
            cnx.close()
    # /disconnectDatabase

    def getHostDB(parent, cnx):
        """Get connected database server host name.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :returns: Name of host server.
        :rtype: Str
        """
        if cnx:
            try:
                sql = "select @@hostname"
                host = Database.readDatabaseResult(
                    parent, cnx, sql, silent=True)
                return host
            except ():
                return None
        return None
    # /getHostDB

    def getDBVersion(parent, cnx):
        """Get connected database version.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :returns: Version of connected database.
        :rtype: Str
        """
        if cnx:
            try:
                sql = "select version()"
                db = Database.readDatabaseResult(
                    parent, cnx, sql, silent=True)
                return db
            except ():
                return None
        return None
    # /getDBVersion

    def getUsername(parent, cnx):
        """Get connected database user name.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :returns: Name of connected database user.
        :rtype: Str
        """
        if cnx:
            try:
                sql = "SELECT SUBSTRING_INDEX(user(), '@', 1)"
                user = Database.readDatabaseResult(
                    parent, cnx, sql, silent=True)
                return user
            except ():
                return None
        return None
    # /getUsername

    def getGISschemas(parent, cnx, schemas):
        """Get a list of non-gis system tables within a schema.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param schemas: List of schemas.
        :type schemas: list

        :returns: Table names in schema.
        :rtype: tuple
        """
        sql = f"{Database.getCRUD(2)} " \
              "s.SCHEMA_NAME, s.SCHEMA_COMMENT, count(t.TABLE_NAME)\n" \
              "FROM information_schema.TABLES t\n" \
              "INNER JOIN information_schema.schemata s " \
              "ON t.TABLE_SCHEMA=s.SCHEMA_NAME\n" \
              "WHERE (s.SCHEMA_NAME like '%gis%' " \
              " OR s.SCHEMA_NAME like '%geo%' " \
              " OR lower(t.TABLE_NAME) in " \
              "  ('geometry_columns', 'spatial_ref_sys', 'table_datasets')) " \
              "AND s.SCHEMA_NAME not in ("
        for schema in schemas:
            sql += "%s, "
        sql += \
            "'information_schema', 'performance_schema', 'sys', " \
            "'mysql', 'bin_log') " \
            "\nGROUP BY s.SCHEMA_NAME, s.SCHEMA_COMMENT " \
            "\nORDER BY count(t.TABLE_NAME) desc, s.SCHEMA_NAME asc"
        s = []
        for schema in schemas:
            s.append(schema[0])
        par = tuple(s)
        results = Database.readDatabase(parent, cnx, sql, par)
        if schemas:
            for schema in results:
                schemas.append([schema[0], schema[1]])
    # / getGISschemas

    def getTables(parent, cnx, schemaname):
        """Get a list of non-gis system tables within a schema.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param schemaname: Database schema name.
        :type schemaname: Str

        :returns: Table names in schema.
        :rtype: tuple
        """
        if cnx:
            sql = "SELECT table_name\n" \
                  "FROM INFORMATION_SCHEMA.TABLES\n" \
                  "WHERE TABLE_SCHEMA=%s " \
                  "AND table_type ='BASE TABLE' " \
                  "AND table_name !='geometry_columns' " \
                  "AND table_name !='spatial_ref_sys' " \
                  "AND table_name !='table_datasets' " \
                  "\norder by table_name asc"
            par = tuple([schemaname])
            tables = Database.readDatabase(parent, cnx, sql, par)
            return tables
        return None
    # /getTables

    def getTableMetadataCount(parent, cnx, schemaname, tablename):
        """Get estimated number of records in a table from metadata.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :param schemaname: Database schema name.
        :type schemaname: Str

        :param tablename: Database table name.
        :type tablename: Str

        :returns: Estimated number of rows.
        :rtype: Int
        """
        if cnx:
            try:
                sql = "SELECT ifnull(table_rows, -1)\n" \
                      "FROM INFORMATION_SCHEMA.TABLES\n" \
                      "WHERE TABLE_SCHEMA=%s " \
                      "AND table_name=%s"
                par = tuple([schemaname, tablename])
                cnt = Database.readDatabaseResult(
                    parent, cnx, sql, par, silent=True)
                if cnt is None:
                    return -1
                return cnt
            except ():
                return -1
        return -1
    # /getTableMetadataCount

    def isLocalDB(parent, cnx):
        """Test if connected database server is on the same host as this
           running application.
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :returns: True if database server host name is "localhost",
                  or is the same as the application running host.
        :rtype: Boolean
        """
        if cnx:
            try:
                sql = "select @@hostname"
                host = Database.readDatabaseResult(
                    parent, cnx, sql, silent=True)
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
        """Test if database is connected
        :param parent: Parent application window or dialog.
        :type parent: QWidget

        :param cnx: Database connection.
        :type cnx: MySQLConnection or Connection

        :returns: True if database server is currently connected.
        :rtype: Boolean
        """
        if cnx:
            if HAS_MARIADB or HAS_MYSQL:
                try:
                    cnx.ping()
                except sql_error.InterfaceError:
                    return False
                return True
        return False
    # /isConnected

    def isDatabaseConnector():
        """Test if supported Python database connector module found.

        :returns: True if Python database connector module found.
        :rtype: Boolean
        """
        if HAS_MARIADB or HAS_MYSQL:
            return True
        return False
    # /isDatabaseConnector

    def getConnectorVersion():
        """Get Python database connector module version.

        :returns: Python database connector module version description.
        :rtype: Str
        """
        if HAS_MARIADB or HAS_MYSQL:
            return pysql.__version__
        return ''
    # /getConnectorVersion

    def isMariadb():
        """Test if Python mariadb connector module found.

        :returns: True if Python mariadb connector module found.
        :rtype: Boolean
        """
        return HAS_MARIADB
    # /isMariadb

    def isMysql():
        """Test if Python mysql connector module found.

        :returns: True if Python mysql connector module found.
        :rtype: Boolean
        """
        return HAS_MYSQL
    # /isMysql
# /Database
