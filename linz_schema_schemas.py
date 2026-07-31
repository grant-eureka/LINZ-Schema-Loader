# Created on : Dec 26, 2025, 3:07:23 PM
# Author     : Grant

import os
import sys
import tempfile
import zipfile
import io
import csv
import glob
from defusedxml import ElementTree
import datetime
from osgeo import osr
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
    from linz_schema_database import Database, SQLError
else:
    from .linz_schema_utilities import MessageBoxes, Utilities
    from .linz_schema_database import Database, SQLError


class Counters():
    """'Type' definition for database field.
    """
    READ = 0
    WRITE = 1
    FAIL = 2
    DUPLICATE = 4

    readCnt = 0
    writeCnt = 0
    failCnt = 0
    duplicateCnt = 0

    def __init__(self):
        self.readCnt = 0
        self.writeCnt = 0
        self.failCnt = 0
        self.duplicateCnt = 0

    def __str__(self):
        return f'Total read : {self.readCnt} ' \
               f'Total write : {self.writeCnt} ' \
               f'Total fail : {self.failCnt} ' \
               f'Total duplicate : {self.duplicateCnt}'

    def increment(self, field):
        match field:
            case self.READ:
                self.readCnt += 1
            case self.WRITE:
                self.writeCnt += 1
            case self.FAIL:
                self.failCnt += 1
            case self.DUPLICATE:
                self.duplicateCnt += 1
# /Counters


class SchemasActions():
    def __init__(self):
        super().__init__()
    # /__init__

    def init(self):
        pass
    # /init

    def requestSchemaCreate(self, parent, cnx, schemaname, description):
        parent.appendLog(f'requestSchemaCreate {schemaname} : {description}')
        if Database.isSchemaExist(parent, cnx, schemaname):
            if Database.isGISSchemaExist(parent, cnx, schemaname):
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.INFORMATION,
                    Utilities.getApptitle(parent),
                    f'GIS schema "{schemaname}" already exists.',
                    MessageBoxes.OK)
                parent.appendLog('Create schema cancelled')
                return False
            else:
                sql = "SELECT DEFAULT_CHARACTER_SET_NAME " \
                      "FROM information_schema.SCHEMATA " \
                      "WHERE lower(SCHEMA_NAME)=lower(%s)"
                par = tuple([schemaname])
                charset = '' + Database.readDatabaseResult(
                    parent, cnx, sql, par, silent=True)
                if 'utf8' in charset:
                    charsetMsg = ''
                else:
                    charsetMsg = f'Warning: Existing schema "{schemaname}" ' + \
                                 f'uses character set "{charset}", ' + \
                                 '"utf8" recommended.\n\n'
                if MessageBoxes.messageBox(
                   parent,
                   MessageBoxes.QUESTION,
                   Utilities.getApptitle(parent),
                   f'Schema "{schemaname}" already exists.\n\n'
                   f'{charsetMsg}'
                   f'Make "{schemaname}" a GIS schema?',
                   MessageBoxes.YES_NO) != MessageBoxes.YES.value:
                    parent.appendLog('Create schema cancelled')
                    return False
                else:
                    self.createSchema(
                        parent, cnx, schemaname, description, False)
        else:
            if MessageBoxes.messageBox(
               parent,
               MessageBoxes.QUESTION,
               Utilities.getApptitle(parent),
               f'Create new GIS schema "{schemaname}"?',
               MessageBoxes.YES_NO) != MessageBoxes.YES.value:
                parent.appendLog('Create schema cancelled')
                return False
            self.createSchema(parent, cnx, schemaname, description, True)
        return True
    # /requestSchemaCreate

    def createSchema(self, parent, cnx, schemaname, description, new):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f'\nCreating GIS schema "{schemaname}"...')
        if new:
            sql = f"CREATE SCHEMA {schemaname}"
            if Database.executeSQL(parent, cnx, sql,
                                   silent=False, logOnly=False):
                parent.appendLog(f'Created schema "{schemaname}"')
            else:
                return
            parent.appendLog('Define GIS schema...')
            if description:
                comment = description
            else:
                comment = schemaname + " schema"
            sql = f"ALTER SCHEMA {schemaname}\n" \
                  "DEFAULT CHARACTER SET='utf8'\n" \
                  "DEFAULT COLLATE='utf8_general_ci'\n" \
                  "COMMENT=%s"
            par = tuple([comment])
            Database.executeSQL(parent, cnx, sql, par, silent=True)
        else:
            parent.appendLog(f'Schema "{schemaname}" already exists')
        sql = "GRANT select, insert, update, delete, execute " \
              f"ON {schemaname}.* " \
              "TO root@localhost WITH GRANT OPTION"
        Database.executeSQL(parent, cnx, sql, silent=True)
        parent.appendLog('Create geometry tables')
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.geometry_columns\n(" \
              "f_table_catalog    VARCHAR(256), " \
              "f_table_schema     VARCHAR(256), " \
              "f_table_name       VARCHAR(256) NOT NULL, " \
              "f_geometry_column  VARCHAR(256) NOT NULL, " \
              "coord_dimension    INTEGER(11), " \
              "srid               INTEGER(11), " \
              "type               VARCHAR(256) NOT NULL, " \
              "geometry_type      VARCHAR(256) NOT NULL, " \
              "qgis_xmin          FLOAT, " \
              "qgis_ymin          FLOAT, " \
              "qgis_xmax          FLOAT, " \
              "qgis_ymax          FLOAT, " \
              "qgis_pkey          VARCHAR(256), " \
              "INDEX (f_table_name) )"
        Database.executeSQL(parent, cnx, sql, silent=True)
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.spatial_ref_sys\n(" \
              "srid       INTEGER(11) NOT NULL PRIMARY KEY, " \
              "auth_name  VARCHAR(256), " \
              "auth_srid  INTEGER(11), " \
              "srtext     VARCHAR(2048), " \
              "proj4text  VARCHAR(2048) )"
        Database.executeSQL(parent, cnx, sql, silent=True)
        parent.appendLog('Create dataset table')
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.table_datasets\n(" \
              " schemaname VARCHAR(64) NOT NULL, " \
              " tablename VARCHAR(64) NOT NULL, " \
              " dataset_file VARCHAR(256), " \
              " dataset_date DATE, " \
              " dataset_cnt INTEGER, " \
              " dataset_load_seconds INTEGER, " \
              "PRIMARY KEY (schemaname, tablename) )"
        Database.executeSQL(parent, cnx, sql, silent=True)
        parent.loadDatasetTable(schemaname)
        parent.appendLog('Defined GIS schema')
        parent.appendLog(f'Created schema {schemaname}')
        parent.unsetCursor()
    # /createSchema

    def updateSchema(self, parent, cnx, schemaname, description):
        update = MessageBoxes.messageBox(
            parent,
            MessageBoxes.QUESTION,
            Utilities.getApptitle(parent),
            f'Update definitions of schema "{schemaname}"?',
            MessageBoxes.YES_NO)
        purge = MessageBoxes.messageBox(
            parent,
            MessageBoxes.QUESTION,
            Utilities.getApptitle(parent),
            f'Drop depricated tables from schema "{schemaname}"?',
            MessageBoxes.YES_NO)
        parent.appendLog(f'\nUpdating schema {schemaname}...')
        if update == MessageBoxes.YES.value:
            self.updateSchemaDefinition(parent, cnx, schemaname, description)
        if purge == MessageBoxes.YES.value:
            self.updateSchemaPurge(parent, cnx, schemaname)
        parent.appendLog(f'Updated schema {schemaname}')
    # /updateSchema

    def updateSchemaDefinition(self, parent, cnx, schemaname, description):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog('  update schema description...')
        if description:
            comment = description
        else:
            comment = schemaname + " schema"
        sql = f"ALTER SCHEMA {schemaname}\n" \
              "DEFAULT CHARACTER SET='utf8'\n" \
              "DEFAULT COLLATE='utf8_general_ci'\n" \
              "COMMENT=%s"
        par = tuple([comment])
        Database.executeSQL(parent, cnx, sql, par, silent=True)
        parent.appendLog('  update schema privilges...')
        sql = "GRANT select, insert, update, delete, execute " \
              f"ON {schemaname}.* " \
              "TO root@localhost WITH GRANT OPTION"
        Database.executeSQL(parent, cnx, sql, silent=True)
        parent.appendLog('  update geometry tables...')
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.geometry_columns\n(" \
              "f_table_catalog    VARCHAR(256), " \
              "f_table_schema     VARCHAR(256), " \
              "f_table_name       VARCHAR(256) NOT NULL, " \
              "f_geometry_column  VARCHAR(256) NOT NULL, " \
              "coord_dimension    INTEGER(11), " \
              "srid               INTEGER(11), " \
              "type               VARCHAR(256) NOT NULL, " \
              "geometry_type      VARCHAR(256) NOT NULL, " \
              "qgis_xmin          FLOAT, " \
              "qgis_ymin          FLOAT, " \
              "qgis_xmax          FLOAT, " \
              "qgis_ymax          FLOAT, " \
              "qgis_pkey          VARCHAR(256), " \
              "INDEX (f_table_name) )"
        Database.executeSQL(parent, cnx, sql, silent=True)
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.spatial_ref_sys\n(" \
              "srid       INTEGER(11) NOT NULL PRIMARY KEY, " \
              "auth_name  VARCHAR(256), " \
              "auth_srid  INTEGER(11), " \
              "srtext     VARCHAR(2048), " \
              "proj4text  VARCHAR(2048) )"
        Database.executeSQL(parent, cnx, sql, silent=True)
        parent.appendLog('  create/update dataset table...')
        sql = "CREATE TABLE IF NOT EXISTS " \
              f"{schemaname}.table_datasets\n(" \
              " schemaname VARCHAR(64) NOT NULL, " \
              " tablename VARCHAR(64) NOT NULL, " \
              " dataset_file VARCHAR(256), " \
              " dataset_date DATE, " \
              " dataset_cnt INTEGER, " \
              " dataset_load_seconds INTEGER, " \
              "PRIMARY KEY (schemaname, tablename) )"
        Database.executeSQL(parent, cnx, sql, silent=True)
        sql = f"ALTER TABLE {schemaname}.table_datasets\n" \
              "ADD COLUMN IF NOT EXISTS (" \
              " dataset_load_seconds INTEGER )"
        Database.executeSQL(parent, cnx, sql, silent=True)
        parent.loadDatasetTable(schemaname)
        parent.unsetCursor()
    # /updateSchemaDefinition

    def updateSchemaPurge(self, parent, cnx, schemaname):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog('  purge depricated tables...')
        tables = Database.getTables(parent, cnx, schemaname)
        drop = False
        if tables:
            for table in tables:
                if self.isPurgeTable(table[0]):
                    parent.appendLog(f'    drop table {table[0]}')
                    sql = f"DROP TABLE {schemaname}table[0]"
                    Database.executeSQL(parent, cnx, sql)
                    drop = True
        else:
            parent.appendLog(f'    NO tables found in {schemaname}')
        parent.unsetCursor()
        if drop:
            msg = 'Database tables have been dropped from schema ' + \
                f'"{schemaname}".\n' + \
                'Database views may have been invalidated and need ' + \
                're-creating.\n' + \
                'Your QGIS projects may now have invalid data sources for ' + \
                'layers connecting to the dropped tables.\n' + \
                'Delete or update any invalid data sources from QGIS.'
            parent.appendLog(msg)
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.INFORMATION,
                Utilities.getApptitle(parent),
                msg)
    # /updateSchemaPurge

    def isPurgeTable(self, tablename):
        purgeTables = [
            'aims_address',
            'aims_address_class',
            'aims_address_component',
            'aims_address_component_type',
            'aims_address_lifecycle_stage',
            'aims_address_position',
            'aims_address_position_type',
            'aims_address_reference',
            'aims_address_reference_object_type',
            'aims_addressable_object',
            'aims_addressable_object_lifecycle_stage',
            'aims_addressable_object_type',
            'aims_addressable_object_external',
            'aims_alternative_address_type',
            'aims_organisation',
            'nz_addresses_pilot',
            'nz_addresses_roads_pilot',
            'nz_addresses_road_sections_pilot',
            'nz_roads_addressing',
            'nz_roads_addressing_road_name',
            'nz_roads_address_range_road_type',
            'nz_roads_capture_method',
            'nz_roads_geometry_class',
            'nz_roads_road',
            'nz_roads_road_section_geometry',
            'nz_roads_road_name',
            'nz_roads_road_name_association',
            'nz_roads_road_name_class',
            'nz_roads_road_name_prefix',
            'nz_roads_road_name_suffix',
            'nz_roads_road_name_type',
            'nz_roads_road_section',
            'nz_roads_road_section_lifecycle_stage',
            'nz_roads_road_section_type',
            'nz_roads_road_type',
            'nz_roads_route_name',
            'nz_roads_subsections_addressing'
        ]
        # keep as still used:    'nz_roads_organisation'
        if tablename:
            if tablename.endswith('_deprecated'):
                return True
            return tablename in purgeTables
        return False
    # /isPurgeTable

    def requestSchemaDrop(self, parent, cnx, schemaname):
        parent.appendLog(f'\nDrop GIS schema {schemaname}')
        if Database.isSchemaExist(parent, cnx, schemaname):
            option = MessageBoxes.messageBox(
                parent,
                MessageBoxes.QUESTION,
                Utilities.getApptitle(parent),
                f'Schema "{schemaname}" exists.\n\n'
                'Drop existing schema?',
                MessageBoxes.YES_NO)
            if option == MessageBoxes.YES.value:
                if MessageBoxes.messageBox(
                   parent,
                   MessageBoxes.QUESTION,
                   Utilities.getApptitle(parent),
                   f'All contents in schema "{schemaname}" '
                   'will be deleted.\n\n'
                   'Drop schema and all contents?',
                   MessageBoxes.YES_NO) == MessageBoxes.YES.value:
                    self.dropSchema(parent, cnx, schemaname)
                else:
                    parent.appendLog('Drop schema cancelled')
                    return False
            else:
                parent.appendLog('Drop schema cancelled')
                return False
        else:
            parent.appendLog(f'Schema {schemaname} does not exists.\n'
                             'Unable to drop non-existing schema.')
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.INFORMATION,
                Utilities.getApptitle(parent),
                f'Schema "{schemaname}" does not exists.\n'
                'Unable to drop non-existing schema.')
        return True
    # /requestSchemaDrop

    def dropSchema(self, parent, cnx, schemaname):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f'Droping schema {schemaname}...')
        sql = f"DROP SCHEMA {schemaname}"
        Database.executeSQL(parent, cnx, sql)
        sql = "REVOKE ALL " \
              f"ON {schemaname}.* " \
              "FROM root@localhost"
        Database.executeSQL(parent, cnx, sql, silent=True)
        parent.appendLog(f'Dropped schema {schemaname}')
        parent.unsetCursor()
    # /dropSchema

    def requestSchemaLoad(self, parent, cnx, schemaname):
        parent.appendLog(f"\nImport CSV data into schema {schemaname}...")
        if Database.isSchemaExist(parent, cnx, schemaname):
            if MessageBoxes.messageBox(
               parent,
               MessageBoxes.QUESTION,
               Utilities.getApptitle(parent),
               f'Load LINZ dataset files into schema "{schemaname}"?',
               MessageBoxes.YES_NO) == MessageBoxes.YES.value:
                directoryName = self.getLoadDirectory(parent, cnx, schemaname)
                if directoryName:
                    self.processDirectory(parent, cnx,
                                          schemaname, directoryName)
                else:
                    parent.appendLog("\nNo directory selected for loading")
                self.processViews(parent, cnx, schemaname)
            else:
                parent.appendLog('Import CSV data cancelled')
    # /requestSchemaLoad

    def getLoadDirectory(self, parent, cnx, schemaname):
        directoryName = None
        sql = "SELECT dataset_file " \
              f"FROM {schemaname}.table_datasets " \
              "WHERE schemaname=%s "\
              "AND dataset_file IS NOT NULL " \
              "ORDER BY dataset_date DESC"
        par = tuple([schemaname])
        directoryName = Database.readDatabaseResult(parent, cnx, sql, par)
        directoryName = MessageBoxes.openDirectoryBox(
            parent, "Open LINZ Download ZIP Directory", directoryName)
        return directoryName
    # /getLoadDirectory

    def processDirectory(self, parent, cnx, schemaname, directoryName):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f"\nLoad zip data files from {directoryName} "
                         f"into schema {schemaname}...")
        for zipFileName in sorted(glob.glob(f"{directoryName}/*.zip")):
            if zipfile.is_zipfile(zipFileName):
                parent.appendLog(f'\nProcess {zipFileName}...')
                zip = zipfile.ZipFile(zipFileName, 'r')
                vrtfiles = Utilities.getVrtFiles(zip)
                extents = [None, None, None, None]
                for vrtfile in vrtfiles:
                    parent.appendLog(f'    Analysing\t{vrtfile}...')
                    vrtpath = Utilities.getPathDirectory(vrtfile)
                    if vrtpath:
                        vrtpath += "/"
                    vrtname = Utilities.getPathFile(vrtfile)
                    tree = ElementTree.fromstring(zip.read(vrtfile))
                    csvFileName = Utilities.getTreeText(
                        tree, None, 'SrcDataSource')
                    zipDate = self.getZipDate(zip, csvFileName)
                    parent.appendLog(f'    data file\t{vrtpath}{csvFileName}')
                    parent.appendLog(f'    data timestamp\t{zipDate}')
                    layername = Utilities.getTreeText(
                        tree, 'OGRVRTLayer', 'name')
                    tablename = None
                    if layername:
                        tablename = layername.lower().replace('-', '_')
                    if self.isPurgeTable(tablename):
                        parent.appendLog(
                            f'    \t{tablename} has been depricated '
                            'and will not be loaded')
                    else:
                        key = Utilities.getTreeText(
                            tree, None, 'FID')
                        fcnt = Utilities.getTreeInt(
                            tree, None, 'FeatureCount', 0)
                        geometry = Utilities.getTreeText(
                            tree, None, 'GeometryType')
                        if geometry:
                            geometry = geometry.upper().lstrip("WKB")
                            if geometry == "POLYGON":
                                geometry = "MULTIPOLYGON"
                            geometry = self.getTableGeometry(
                                parent, cnx, schemaname, tablename, geometry)
                            parent.appendLog(
                                f'    geometry\t{geometry}')
                            prjId = self.getPrjId(
                                parent, cnx, schemaname, zip, vrtname)
                        else:
                            parent.appendLog('    geometry\tNone')
                            prjId = None
                        extents[0] = Utilities.getTreeText(
                            tree, None, 'ExtentXMin')
                        extents[1] = Utilities.getTreeText(
                            tree, None, 'ExtentYMin')
                        extents[2] = Utilities.getTreeText(
                            tree, None, 'ExtentXMax')
                        extents[3] = Utilities.getTreeText(
                            tree, None, 'ExtentYMax')
                        geofield = Utilities.getTreeText(
                            tree, 'GeometryField', 'field')
                        fields = Utilities.getFields(
                            tree, geometry, geofield, key)
#                        for field in fields:
#                            print(f"{field.fieldName} {field.fieldType}")

                        parent.appendLog(f'    features\t{fcnt:,}')

                        dataset = self.getDataset(
                            parent, cnx, schemaname, tablename, zipFileName)
                        if Database.isTableExist(
                                parent, cnx, schemaname, tablename):
                            if dataset:
                                schemaDate = dataset[3]
                                schemaRows = dataset[4]
                                schemaElapsed = dataset[5]
                                self.logSchemaLoad(
                                    parent, schemaDate, schemaRows,
                                    schemaElapsed)
                            if self.truncateTable(
                               parent, cnx,
                               schemaname, tablename, dataset, zipDate,
                               fields, zipFileName):
                                dataset = self.getDataset(
                                    parent, cnx,
                                    schemaname, tablename, zipFileName)
                                self.setTableGeometry(
                                    parent, cnx,
                                    schemaname, tablename, geometry,
                                    extents, prjId, fields)
                                append = Database.isDataExist(
                                    parent, cnx, schemaname, tablename)
                                self.loadTable(
                                    parent, cnx,
                                    schemaname, tablename, dataset,
                                    fields, geometry, key, append,
                                    directoryName, zipFileName, zip, zipDate,
                                    vrtpath + csvFileName, fcnt)
                        else:
                            ok = True
                            try:
                                self.createTable(
                                    parent, cnx,
                                    schemaname, tablename, fields, zipFileName)
                            except Exception as err:
                                parent.appendLog(
                                    '    Database error creating table '
                                    f'{schemaname}.{tablename}:\n'
                                    f'SQLError: {err}')
                                ok = False
                            if ok:
                                dataset = self.getDataset(
                                    parent, cnx,
                                    schemaname, tablename, zipFileName)
                                self.setTableGeometry(
                                    parent, cnx,
                                    schemaname, tablename, geometry,
                                    extents, prjId, fields)
                                self.loadTable(
                                    parent, cnx,
                                    schemaname, tablename, dataset,
                                    fields, geometry, key, False,
                                    directoryName, zipFileName, zip, zipDate,
                                    vrtpath + csvFileName, fcnt)
                        parent.appendLog(
                            f'    Process {vrtfile} complete')

                if vrtfiles:
                    parent.appendLog(f'Process {zipFileName} complete')
                else:
                    parent.appendLog(
                        f'Error: .vrt file not found in {zipFileName}. - '
                        'not loaded')
                zip.close()
            else:
                parent.appendLog(
                    f'Error: invalid zip file {zipFileName}. - '
                    'not loaded')
        parent.appendLog(f'Loaded data into schema {schemaname}')
        parent.unsetCursor()
    #  \processDirectory

    def logSchemaLoad(self, parent, schemaDate, schemaRows, schemaElapsed):
        if schemaDate:
            parent.appendLog(
                f'    existing date\t{schemaDate}')
        if schemaRows:
            parent.appendLog(
                f'    existing rows\t{schemaRows:,}')
        if schemaElapsed:
            t = datetime.timedelta(seconds=schemaElapsed)
            parent.appendLog(
                f'    previous time\t{t}')
    # /logSchemaLoad

    def loadTable(self, parent, cnx, schemaname, tablename, dataset,
                  fields, geometry, key, append,
                  directoryName, zipFileName, zip, zipDate, csvFileName, fcnt):
        # parent.appendLog(f'\tloadTable {schemaname}.{tablename}')  # debug
        if csvFileName:
            if geometry:
                pass
                geometry = self.loadTableFile(
                    parent, cnx,
                    schemaname, tablename, fields, geometry, key, append,
                    directoryName, zipFileName, zip, zipDate, csvFileName, fcnt)
            else:
                parent.appendLog('    load non-geometry file')
                self.loadTableFileDirect(
                    parent, cnx,
                    schemaname, tablename, fields, key, append,
                    directoryName, zipFileName, zip, zipDate, csvFileName, fcnt)
        else:
            parent.appendLog('    no data file to load')
    # /loadTable

    def loadTableFileDirect(self, parent, cnx,
                            schemaname, tablename, fields, key,
                            append, directoryName, zipFileName, zip, zipDate,
                            csvFileName, fcnt):
        # parent.appendLog(
        #     f'    loadTableFileDirect {schemaname}.{tablename}')  # debug
        startTime = Utilities.getNow()
        self.dropIndexes(parent, cnx, schemaname, tablename)
        parent.appendLog(f'    load table data into {schemaname}.{tablename}')
        parent.appendLog(f'    load data from {csvFileName}')
        csvFilePath = Utilities.getCsvFilepath(zip, csvFileName)
        csv.field_size_limit(sys.maxsize)
        try:
            tempDir = tempfile.TemporaryDirectory()
            parent.appendLog(f'    extract csv file to {tempDir.name}')
            zip.extract(csvFilePath, tempDir.name)
            uzipFileName = f"{tempDir.name}/{csvFilePath}"
            self.loadTableDirect(
                parent, cnx, schemaname, tablename, fields, key,
                zipFileName, zipDate, append, uzipFileName, fcnt)
            tempDir.cleanup()
            parent.appendLog('    count loaded rows')
            loadedCnt = self.featureCount(
                parent, cnx, True, schemaname, tablename, key)
            parent.appendLog(f'    {fcnt:,} records processed')
            parent.appendLog(f'    {loadedCnt:,} records loaded')
            elapsed = Utilities.getElapsedTime(startTime)
            self.setDatasetTable(
                parent, cnx,
                schemaname, tablename, zipFileName, zipDate,
                loadedCnt, elapsed)
            self.createIndexes(parent, cnx, schemaname, tablename, fields)
            parent.readStatus(None)
            parent.appendLog(f'    load completed {Utilities.getNowString()}')
            parent.appendLog(f'    elapsed time {elapsed}')
        except OSError as err:
            try:
                parent.appendLog(
                    f'Error extracting {csvFilePath} to {tempDir}:\n{err}')
                if tempDir:
                    tempDir.cleanup()
                tempDir = os.path.join(
                    os.sep, directoryName, zipFileName.rstrip(".zip"))
                parent.appendLog(
                    f'    extract csv file to {tempDir}')
                os.makedirs(tempDir, exist_ok=True)
                zip.extract(csvFilePath, tempDir)
                uzipFileName = f"{tempDir}/{csvFilePath}"
                self.loadTableDirect(
                    parent, cnx,
                    schemaname, tablename, fields, key,
                    zipFileName, zipDate, append, uzipFileName, fcnt)
                parent.appendLog(
                    '    count loaded rows')
                loadedCnt = self.featureCount(parent, cnx,
                                              True, schemaname, tablename, key)
                parent.appendLog(
                    f'    {fcnt:,} records processed')
                parent.appendLog(
                    f'    {loadedCnt:,} records loaded')
                elapsed = Utilities.getElapsedTime(startTime)
                self.setDatasetTable(
                    parent, cnx,
                    schemaname, tablename, zipFileName, zipDate,
                    loadedCnt, elapsed)
                self.createIndexes(parent, cnx, schemaname, tablename, fields)
                parent.readStatus(None)
                parent.appendLog(
                    '    load completed {Utilities.getNowString()}')
                parent.appendLog(f'    elapsed time {elapsed}')
            except OSError as err:
                parent.appendLog(
                    f'Error extracting {csvFilePath} to {tempDir}:\n{err}')
    # /loadTableFileDirect

    def loadTableDirect(self, parent, cnx,
                        schemaname, tablename, fields, key,
                        zipFileName, zipDate, append, uzipFileName, fcnt):
        parent.appendLog('    count existing rows')
        appendCnt = self.featureCount(
            parent, cnx, append, schemaname, tablename, key) + 1
        parent.appendLog(f'    load data from {uzipFileName}')
        if appendCnt > 1:
            parent.appendLog(f'    skip {appendCnt:,} lines')
        # todo: convert all to strings?
        pars = [uzipFileName, appendCnt]
        sql = "LOAD DATA "
        # local = Database.isLocalDB(parent, cnx)
        # if not local:  # force infile local for file security
        sql += "LOCAL "
        sql += "INFILE %s\n"
        sql += f"IGNORE INTO TABLE {schemaname}.{tablename}\n" + \
            "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY 0x22 " + \
            "ESCAPED BY 0x5c\n" + \
            "LINES TERMINATED BY 0x0d0a\n" \
            "IGNORE %s LINES\n"
        isFirst = True
        hasTmps = False
        for field in fields:
            isTmp = field.fieldType == 'TEXT' \
                or field.fieldType == 'VARCHAR' \
                or field.fieldType == 'STRING' \
                or field.fieldType == 'TEXT'
            isTmp = (isTmp and field.fieldWidth) \
                or Utilities.isNumberField(field.fieldType) \
                or Utilities.isDateField(field.fieldType)
            if isTmp and not field.isKey:
                fieldName = "@temp_" + field.fieldName
                hasTmps = True
            else:
                fieldName = field.fieldName
            if isFirst:
                sql += f"({fieldName}"
                isFirst = False
            else:
                sql += f", {fieldName}"
        sql += ")\n"
        if hasTmps:
            isFirst = True
            for field in fields:
                if not field.isKey:
                    isTmp = field.fieldType == 'TEXT' \
                        or field.fieldType == 'VARCHAR' \
                        or field.fieldType == 'STRING' \
                        or field.fieldType == 'TEXT'
                    if isTmp and field.fieldWidth:
                        if isFirst:
                            sql += "SET "
                            isFirst = False
                        else:
                            sql += ",\n    "
                        fieldName = "@temp_" + field.fieldName
                        sql += f"{field.fieldName} = " \
                            f"nullif(substring({fieldName}, 1," \
                            " %s), '')"
                        pars.append(field.fieldWidth)
                    isTmp = Utilities.isNumberField(field.fieldType) \
                        or Utilities.isDateField(field.fieldType)
                    if isTmp:
                        if isFirst:
                            sql += "SET "
                            isFirst = False
                        else:
                            sql += ",\n    "
                        fieldName = "@temp_" + field.fieldName
                        sql += f"{field.fieldName} = " \
                            f"IF({fieldName}='' OR {fieldName}='\n' OR " \
                            f"{fieldName}='\r', NULL, {fieldName})"
        par = tuple(pars)
        parent.appendLog(f'    load started {Utilities.getNowString()}...')
        # parent.appendLog(f'{sql}\n{par}')  # debug
        Database.executeSQLwithWarnings(parent, cnx, sql, par)
        Database.commit(parent, cnx)
        parent.appendLog(f'    load finished {Utilities.getNowString()}...')
    # /loadTableDirect

    def loadTableFile(self, parent, cnx,
                      schemaname, tablename, fields, geometry, key,
                      append, directoryName, zipFileName, zip, zipDate,
                      csvFileName, fcnt):
        # parent.appendLog(f'\tloadTableFile {schemaname}.{tablename}')  # debug
        startTime = Utilities.getNow()
        self.dropIndexes(parent, cnx, schemaname, tablename)
        parent.appendLog(f'    load feature data into {schemaname}.{tablename}')
        parent.appendLog(f'    load data from {csvFileName}')
        counters = Counters()
        appendCnt = self.featureCount(parent, cnx,
                                      append, schemaname, tablename, key)
        startTimeLoad = Utilities.getNow()
        parent.appendLog(f'    load started {Utilities.getNowString()}...')
        parent.readStatus(f"{schemaname}.{tablename}",
                          startTimeLoad, fcnt, counters.readCnt)
        csvFilePath = Utilities.getCsvFilepath(zip, csvFileName)
        csv.field_size_limit(sys.maxsize)
        csvFile = io.TextIOWrapper(zip.open(csvFilePath), encoding="utf-8-sig")
        reader = csv.DictReader(csvFile)
        cursor = Database.openSqlCursor(parent, cnx)
        sql = self.loadTableFileSql(schemaname, tablename, fields)
        # if True:
        if cursor:
            for row in reader:
                # sql = self.loadTableFileSql(schemaname, tablename, fields)
                counters.increment(counters.READ)
                keyValue = self.getKeyValue(row, fields)
                if self.isFeatureExist(parent, cnx,
                                       append, appendCnt, counters.readCnt,
                                       schemaname, tablename,
                                       key, keyValue):
                    counters.increment(counters.DUPLICATE)
                else:
                    pars = []
                    geoMissing = False
                    for field in fields:
                        if field.fieldSrc == "1":
                            value = f"{counters.readCnt}"
                            pars.append(value)
                        else:
                            value = row[field.fieldSrc]
                            if Utilities.isGeometryField(field.fieldType):
                                if Utilities.isNull(value):
                                    geoMissing = True
                                else:
                                    geotype = value[0:value.find('(') - 1] \
                                        .rstrip().upper()
                                    if Utilities.isGeometryField(geotype):
                                        geometry = self.modGeometryType(
                                            parent, cnx,
                                            counters.readCnt, geometry, geotype,
                                            schemaname, tablename)
                                        (geoFromText, val) = \
                                            Utilities.getGeometryValue(
                                                geometry, geotype, value)
                                        sql = sql.replace(
                                            'ST_GeomFromText', geoFromText)
                                        pars.append(val)
                                    else:
                                        geoMissing = True
                            elif Utilities.isNull(value):
                                value = None
                                pars.append(value)
                            elif Utilities.isTextField(field.fieldType):
                                value = Utilities.getTextValue(
                                    value, field.fieldWidth)
                                pars.append(value)
                            else:
                                # may need more conversions for field types
                                pars.append(value)
                    if geoMissing:
                        counters.increment(counters.FAIL)
                        parent.appendLog(
                            f'Error inserting record {counters.readCnt} '
                            f'(id={keyValue}) into '
                            f'{schemaname}.{tablename}'
                            f' - Invalid feature geometry')
                    else:
                        par = tuple(pars)
                        # parent.appendLog(f"{sql}\n{par}")  # debug
                        # self.insertFeature(
                        #     parent, cnx, None, schemaname, tablename,
                        #     sql, par, counters)
                        self.insertFeature(
                            parent, cnx, cursor, schemaname, tablename,
                            sql, par, counters)
                parent.readStatus(
                    f"{schemaname}.{tablename}",
                    startTimeLoad, fcnt, counters.readCnt)
        Database.commit(parent, cnx)
        Database.closeSqlCursor(parent, cursor)
        csvFile.close()
        parent.appendLog(f'    load finished {Utilities.getNowString()}...')
        parent.appendLog(
            f'    {counters.readCnt:,} records processed out of {fcnt:,}')
        parent.appendLog(
            f'        {counters.writeCnt:,} loaded'
            f'        {counters.failCnt:,} failed'
            f'        {counters.duplicateCnt:,} duplicates skipped')
        elapsed = Utilities.getElapsedTime(startTime)
        self.setDatasetTable(
            parent, cnx,
            schemaname, tablename, zipFileName, zipDate,
            counters.writeCnt + counters.duplicateCnt, elapsed)
        self.createIndexes(parent, cnx, schemaname, tablename, fields)
        parent.readStatus(None)
        parent.appendLog(f'    load completed {Utilities.getNowString()}')
        parent.appendLog(f'    elapsed time {elapsed}')
        return geometry
    # /loadTableFile

    def insertFeature(self, parent, cnx, cursor, schemaname, tablename,
                      sql, parameters, counters):
        try:
            # if Database.executeSQL(parent, cnx, sql, parameters, silent=True):
            if Database.executeSqlCursor(parent, cursor, sql, parameters):
                counters.increment(counters.WRITE)
                if counters.writeCnt % 1000 == 0:
                    Database.commit(parent, cnx)
            else:
                counters.increment(counters.FAIL)
                parent.appendLog(
                    f'Error inserting record {counters.readCnt:} into '
                    f'{schemaname}.{tablename}')
        except (SQLError) as err:
            if err.errNo == Database.DUP_ENTRY:
                counters.increment(counters.DUPLICATE)
            else:
                counters.increment(counters.FAIL)
                parent.appendLog(
                    f'Error inserting record {counters.readCnt:} into '
                    f'{schemaname}.{tablename}'
                    f'\nSQLERR:{err.errNo} {err.errText}')
                # parent.appendLog(err.errSql)  # debug
    # /insertFeature

    def loadTableFileSql(self, schemaname, tablename, fields):
        sql = f"INSERT INTO {schemaname}.{tablename} \n"
        isFirst = True
        for field in fields:
            if isFirst:
                sql1 = f"({field.fieldName}"
                if Utilities.isGeometryField(field.fieldType):
                    sql2 = "(ST_GeomFromText(%s)"
                else:
                    sql2 = "(%s"
                isFirst = False
            else:
                sql1 += f", {field.fieldName}"
                if Utilities.isGeometryField(field.fieldType):
                    sql2 += ", ST_GeomFromText(%s)"
                else:
                    sql2 += ", %s"
        sql += sql1 + ")\nVALUES\n" + sql2 + ")"
        return sql
    # /loadTableFileSql

    def getZipDate(self, zip, csvFileName):
        zipDate = None
        for fileName in zip.namelist():
            if fileName.endswith(csvFileName):
                t = list(zip.getinfo(fileName).date_time)
                dt = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
                zipDate = Utilities.getLatestInfoDate(
                    zipDate,
                    dt)
        return zipDate
    # /getZipDate

    def getTableGeometry(self, parent, cnx, schemaname, tablename, geometry):
        if schemaname and tablename:
            sql = "SELECT upper(c.COLUMN_TYPE) AS COLUMN_TYPE " \
                  "FROM information_schema.COLUMNS c " \
                  "INNER JOIN information_schema.TABLES t " \
                  "ON c.TABLE_CATALOG = t.TABLE_CATALOG " \
                  "AND c.TABLE_SCHEMA = t.TABLE_SCHEMA " \
                  "AND c.TABLE_NAME = t.TABLE_NAME " \
                  "WHERE t.TABLE_SCHEMA=%s " \
                  "AND t.TABLE_NAME=%s " \
                  "AND c.COLUMN_NAME='SHAPE'"
            par = tuple([schemaname, tablename])
            g = Database.readDatabaseResult(parent, cnx, sql, par)
            if g:
                return g
        return geometry
    # /getTableGeometry

    def getPrjId(self, parent, cnx, schemaname, zip, vrtname):
        prjfile = None
        prjText = None
        prjId = None
        projName = None
        for fileName in zip.namelist():
            if fileName.endswith(f'{vrtname}.prj'):
                prjfile = fileName
                parent.appendLog(f'    analysing\t{prjfile}...')
                for line in zip.open(prjfile):
                    prjText = line.decode('utf-8')
        if prjText:
            osr.UseExceptions()
            try:
                srs = osr.SpatialReference()
                srs.ImportFromWkt(prjText)
                srs.AutoIdentifyEPSG()
                projName = srs.GetName()
                epsg = srs.GetAuthorityCode(None)
                authority = srs.GetAuthorityName(None)
                parent.appendLog(
                    f'    projection\t{projName} '
                    f'({authority}:{epsg})')
            except RuntimeError:
                q1 = prjText.find('"')
                if q1 < 0:
                    q2 = q1
                else:
                    q2 = prjText.find('"', q1 + 1)
                if q2 < 0:
                    projName = prjText
                else:
                    projName = prjText[q1 + 1:q2]
                parent.appendLog(f'    projection\t{projName} (EPSG:unknowen)')
            sql = f"SELECT SRID FROM {schemaname}.spatial_ref_sys " \
                  "WHERE SRTEXT=%s"
            par = tuple([prjText])
            prjId = Database.readDatabaseResult(parent, cnx, sql, par)
            if prjId:
                parent.appendLog('    found existing projection')
            else:
                parent.appendLog('    insert new projection')
                sql = "SELECT max(SRID) " \
                      f"FROM {schemaname}.spatial_ref_sys"
                prjId = Database.readDatabaseResult(parent, cnx, sql)
                if prjId:
                    prjId += 1
                else:
                    prjId = 1
                sql = f"INSERT INTO {schemaname}.spatial_ref_sys\n" \
                      "(SRID, AUTH_NAME, AUTH_SRID, SRTEXT)\nVALUES\n" \
                      "(%s, NULL, NULL, %s)"
                par = tuple([prjId, prjText])
                Database.executeSQL(parent, cnx, sql, par, True)
                Database.commit(parent, cnx)
        else:
            parent.appendLog('    proj file not found, use default projection')
            sql = f"SELECT min(SRID) FROM {schemaname}.spatial_ref_sys"
            prjId = Database.readDatabaseResult(parent, cnx, sql)
        return prjId
    # /getPrjId

    def truncateTable(self, parent, cnx,
                      schemaname, tablename, dataset, zipDate,
                      fields, zipFileName):
        if dataset:
            pass
        else:
            sql = f"DROP TABLE {schemaname}.{tablename}"
            if Database.executeSQL(parent, cnx, sql, silent=True):
                sql = f"DELETE FROM {schemaname}.geometry_columns\n" \
                      "WHERE F_TABLE_SCHEMA=%s " \
                      "AND F_TABLE_NAME=%s"
                par = tuple([schemaname, tablename])
                Database.executeSQL(parent, cnx, sql, par, silent=True)
                self.createTable(
                    parent, cnx, schemaname, tablename, fields, zipFileName)
            return True
        schemaDate = dataset[3]
        datacnt = int(dataset[4])
        if datacnt > 0 and not Utilities.isNewer(zipDate, schemaDate):
            parent.appendLog('    \tlatest data already loaded into '
                             f'{schemaname}.{tablename}')
            return False
        if Utilities.isNewer(zipDate, schemaDate) and datacnt == 0:
            parent.appendLog(
                '    restart incomplete data load into '
                f'{schemaname}.{tablename}')
        elif Utilities.isNewer(zipDate, schemaDate):
            parent.appendLog(
                f'    delete old data from {schemaname}.{tablename}')
            sql = f"DROP TABLE {schemaname}.{tablename}"
            if Database.executeSQL(parent, cnx, sql, silent=True):
                sql = f"DELETE FROM {schemaname}.geometry_columns\n" \
                      "WHERE F_TABLE_SCHEMA=%s " \
                      "AND F_TABLE_NAME=%s"
                par = tuple([schemaname, tablename])
                Database.executeSQL(parent, cnx, sql, par, silent=True)
                sql = f"DELETE FROM {schemaname}.table_datasets\n" \
                      "WHERE schemaname=%s " \
                      "AND tablename=%s"
                par = tuple([schemaname, tablename])
                Database.executeSQL(parent, cnx, sql, par, silent=True)
                self.createTable(
                    parent, cnx, schemaname, tablename, fields, zipFileName)
        return True
    # /truncateTable

    def createTable(self, parent, cnx,
                    schemaname, tablename, fields, filename):
        parent.appendLog(
            f'    create table {schemaname}.{tablename}')
        sql = f"CREATE TABLE IF NOT EXISTS {schemaname}.{tablename}\n"
        isFirst = True
        hasPK = False
        for field in fields:
            if isFirst:
                sql += "("
                isFirst = False
            else:
                sql += ", "
            sql += f"{field.fieldName} {field.fieldType}"
            if field.fieldWidth:
                sql += f"({field.fieldWidth})"
            if field.fieldSrc == '1' or field.isKey:
                if hasPK:
                    sql += " NOT NULL UNIQUE KEY"
                else:
                    sql += " PRIMARY KEY"
                    hasPK = True
            elif Utilities.isGeometryField(field.fieldType):
                sql += " NOT NULL"
        sql += ")"
        # parent.appendLog(sql)  # debug
        Database.executeSQL(parent, cnx, sql, silent=True)
        self.setDatasetTable(parent, cnx, schemaname, tablename, filename)
    # /createTable

    def setTableGeometry(self, parent, cnx, schemaname, tablename,
                         geometry, extents, prjId, fields):
        if geometry and prjId:
            shapeField = None
            keyField = None
            if fields:
                for field in fields:
                    if Utilities.isGeometryField(field.fieldType):
                        shapeField = field
                    if field.isKey:
                        keyField = field.fieldName
                if keyField:
                    pass
                else:
                    keyField = "OGR_FID"
            if shapeField:
                try:
                    sql = f"SELECT TYPE FROM {schemaname}.geometry_columns " \
                          "WHERE F_TABLE_SCHEMA=%s " \
                          "AND F_TABLE_NAME=%s"
                    par = tuple([schemaname, tablename])
                    geometryType = Database.readDatabaseResult(
                        parent, cnx, sql, par)
                    if geometryType:
                        parent.appendLog(
                            f'    existing geometry layer {tablename}')
                        if self.isGeometryExtra(parent, cnx,
                                                schemaname, tablename):
                            parent.appendLog('    updating geometry extents')
                            sql = f"UPDATE {schemaname}.geometry_columns\n" \
                                  "SET GEOMETRY_TYPE=%s, " \
                                  "QGIS_XMIN=%s, " \
                                  "QGIS_YMIN=%s, " \
                                  "QGIS_XMAX=%s, " \
                                  "QGIS_YMAX=%s, " \
                                  "QGIS_PKEY=%s " \
                                  "\nWHERE F_TABLE_SCHEMA=%s " \
                                  "AND F_TABLE_NAME=%s"
                            par = tuple([geometryType, extents[0],
                                        extents[1], extents[2], extents[3],
                                        keyField, schemaname, tablename])
                        else:
                            parent.appendLog('    updating geometry type')
                            sql = f"UPDATE {schemaname}.geometry_columns\n" \
                                  "SET GEOMETRY_TYPE=%s " \
                                  "\nWHERE F_TABLE_SCHEMA=%s " \
                                  "AND F_TABLE_NAME=%s"
                            par = tuple([geometryType, schemaname, tablename])
                        Database.executeSQL(parent, cnx, sql, par, silent=True)
                        Database.commit(parent, cnx)
                    else:
                        parent.appendLog(
                            f'    create geometry layer {tablename}')
                        if self.isGeometryExtra(parent, cnx,
                                                schemaname, tablename):
                            sql = "INSERT INTO " \
                                  f"{schemaname}.geometry_columns\n(" \
                                  "F_TABLE_CATALOG, F_TABLE_SCHEMA, " \
                                  "F_TABLE_NAME, F_GEOMETRY_COLUMN, " \
                                  "COORD_DIMENSION, SRID, " \
                                  "TYPE, GEOMETRY_TYPE, " \
                                  "QGIS_XMIN, QGIS_YMIN, " \
                                  "QGIS_XMAX, QGIS_YMAX, " \
                                  "QGIS_PKEY) " \
                                  "\nVALUES\n(" \
                                  "NULL, %s, %s, " \
                                  "%s, 2, " \
                                  "%s, " \
                                  "%s, " \
                                  "%s, " \
                                  "%s, %s, %s, %s, " \
                                  "%s )"
                            par = tuple([schemaname, tablename,
                                        shapeField.fieldName, prjId,
                                        shapeField.fieldType,
                                        shapeField.fieldType,
                                        extents[0], extents[1],
                                        extents[2], extents[3],
                                        keyField])
                        else:
                            sql = "INSERT INTO " \
                                  f"{schemaname}.geometry_columns\n(" \
                                  "F_TABLE_CATALOG, F_TABLE_SCHEMA, " \
                                  "F_TABLE_NAME, F_GEOMETRY_COLUMN, " \
                                  "COORD_DIMENSION, SRID, TYPE) " \
                                  "\nVALUES\n(" \
                                  "NULL, %s, %s, " \
                                  "%s, 2, " \
                                  "%s, %s )"
                            par = tuple([schemaname, tablename,
                                        shapeField.fieldName, prjId,
                                        shapeField.fieldType])
                        Database.executeSQL(parent, cnx, sql, par, silent=True)
                        Database.commit(parent, cnx)
                except (SQLError) as err:
                    msg = "Failed to execute SQL statement on " \
                          "MariaDB/MySQL database:"
                    parent.appendLog(
                        f'{msg}\nSQLERR: {err.errText}\n{err.errSql}')
                    MessageBoxes.messageBox(
                        parent,
                        MessageBoxes.WARNING,
                        Utilities.getApptitle(parent),
                        f'{msg}\nSQLERR: {err.errText}\n{err.errSql}')
            else:
                parent.appendLog('    no geometry')
    # /setTableGeometry

    def updateTableGeometry(self, parent, cnx, schemaname, tablename, geometry):
        sql = f"SELECT TYPE FROM {schemaname}.geometry_columns " \
              "WHERE F_TABLE_SCHEMA=%s " \
              "AND F_TABLE_NAME=%s"
        par = tuple([schemaname, tablename])
        result = Database.readDatabaseResult(parent, cnx, sql, par)
        if result:
            if result != geometry:
                parent.appendLog(f'    updating geometry type to {geometry}')
                if self.isGeometryExtra(parent, cnx, schemaname, tablename):
                    sql = f"UPDATE {schemaname}.geometry_columns\n" \
                          "SET TYPE=%s, " \
                          "GEOMETRY_TYPE=%s " \
                          "\nWHERE F_TABLE_SCHEMA=%s " \
                          "AND F_TABLE_NAME=%s"
                    par = tuple([geometry, geometry,
                                 schemaname, tablename])
                else:
                    sql = f"UPDATE {schemaname}.geometry_columns\n" \
                          "SET TYPE=%s " \
                          "\nWHERE F_TABLE_SCHEMA=%s " \
                          "AND F_TABLE_NAME=%s"
                    par = tuple([geometry, schemaname, tablename])
                Database.executeSQL(parent, cnx, sql, par, silent=True)
                Database.commit(parent, cnx)
        else:
            parent.appendLog(f'    missing geometry layer {tablename}')
    # /updateTableGeometry

    def isGeometryExtra(self, parent, cnx, schemaname, tablename):
        sql = "SELECT count(*) AS cnt " \
              "FROM information_schema.COLUMNS c " \
              "WHERE c.TABLE_SCHEMA=%s " \
              "AND c.TABLE_NAME='geometry_columns' " \
              "AND upper(c.COLUMN_NAME) IN ('geometry_type', " \
              "'qgis_xmin', 'qgis_ymin', 'qgis_xmax', 'qgis_ymax', 'qgis_pkey')"
        par = tuple([schemaname])
        fcnt = Database.readDatabaseResult(parent, cnx, sql, par)
        return (fcnt > 5)
    # /isGeometryExtra

    def modGeometryType(self, parent, cnx,
                        cnt, geometry, geotype, schemaname, tablename):
        if geometry == geotype:
            return geometry
        if geometry == 'MULTI' + geotype or geometry == geotype + 'COLLECTION':
            return geometry
        if cnt == 0:
            parent.appendLog(f'    change geometry to {geotype}')
            sql = f"ALTER TABLE {schemaname}.{tablename}\n" \
                  f"MODIFY SHAPE {geotype} NOT NULL"
            Database.executeSQL(parent, cnx, sql, silent=True)
            self.updateTableGeometry(parent, cnx,
                                     schemaname, tablename, geotype)
            return geotype
        if geotype == 'MULTI' + geometry \
           or geotype == geometry + 'COLLECTION':
            #  modify up table
            parent.appendLog(f'    change geometry to {geotype}')
            match geotype:
                case 'POINT':
                    c1 = "ST_PointFromText"
                case 'MULTIPOINT':
                    c1 = "ST_MPointFromText"
                case 'LINESTRING':
                    c1 = "ST_LineFromText"
                case 'MULTILINESTRING':
                    c1 = "ST_MLineFromText"
                case 'POLYGON':
                    c1 = "ST_PolyFromText"
                case 'MULTIPOLYGON':
                    c1 = "ST_MPolyFromText"
                case 'GEOMETRY':
                    c1 = "ST_GeomFromText"
                case 'GEOMETRYCOLLECTION':
                    c1 = "ST_GeomCollFromText('"
            sql = f"ALTER TABLE {schemaname}.{tablename}\n" \
                  "RENAME COLUMN SHAPE TO TEMP, " \
                  f"ADD COLUMN SHAPE {geotype}"
            Database.executeSQL(parent, cnx, sql, silent=True)
            sql = f"UPDATE {schemaname}.{tablename}\n" \
                  f"SET SHAPE={c1}(concat(replace(ST_AsText(TEMP), " \
                  "%s, '%s('), ')'))"
            """
            sql = f"UPDATE {schemaname}.{tablename} " \
                  f"SET SHAPE={c1}(concat(replace(ST_AsText(TEMP), " \
                  f"'{geometry}', '{geotype}('), ')'));"
            """

            par = tuple([geometry, geotype] + '(')
            Database.executeSQL(parent, cnx, sql, par, silent=True)
            Database.commit(parent, cnx)
            sql = f"ALTER TABLE {schemaname}.{schemaname}\n" \
                  "DROP COLUMN TEMP, " \
                  f"MODIFY COLUMN SHAPE {geotype} NOT NULL;"
            Database.executeSQL(parent, cnx, sql, silent=True)
            self.updateTableGeometry(parent, cnx,
                                     schemaname, tablename, geotype)
            return geotype
            #  invalid data, can not convert
        return geometry
    # /modGeometryType

    def getKeyValue(self, row, fields):
        keyValue = None
        for field in fields:
            if field.isKey:
                value = row[field.fieldSrc]
                if Utilities.isTextField(field.fieldType):
                    keyValue = Utilities.getTextValue(value, field.fieldWidth)
                elif Utilities.isDateField(field.fieldType):
                    keyValue = "'" + value + "'"
                else:
                    keyValue = value
        return keyValue
    # /getKeyValue

    def featureCount(self, parent, cnx, append, schemaname, tablename, key):
        if append:
            if key:
                sql = f"SELECT count({key}) FROM {schemaname}.{tablename}"
            else:
                sql = f"SELECT count(1) FROM {schemaname}.{tablename}"
            cnt = Database.readDatabaseResult(
                parent, cnx, sql, silent=True)
            return int(cnt)
        return 0
    # /featureCount

    def isFeatureExist(self, parent, cnx, append, appendCnt, readCnt,
                       schemaname, tablename, key, keyValue):
        if append:
            if appendCnt > readCnt:
                return True
            if key and keyValue:
                sql = "SELECT ifnull(EXISTS(" \
                      f"SELECT 1 FROM {schemaname}.{tablename} " \
                      f"WHERE {key}=%s" \
                      "), 0)"
                par = tuple([keyValue])
                exist = Database.readDatabaseResult(
                    parent, cnx, sql, par, silent=True)
                return (exist == 1)
        return False
    # /isFeatureExist

    def getDataset(self, parent, cnx, schemaname, tablename, filename=None):
        sql = "SELECT schemaname, tablename, " \
              "dataset_file, dataset_date, ifnull(dataset_cnt, 0), " \
              "dataset_load_seconds " \
              f"FROM {schemaname}.table_datasets " \
              "WHERE schemaname=%s " \
              "AND tablename=%s LIMIT 1"
        par = tuple([schemaname, tablename])
        datasets = Database.readDatabase(parent, cnx, sql, par)
        if datasets:
            dataset = datasets[0]
        else:
            dataset = None
        if filename:
            sql = f"UPDATE {schemaname}.table_datasets\n" \
                  "SET dataset_file=%s " \
                  "\nWHERE schemaname=%s " \
                  "AND tablename=%s " \
                  "AND dataset_file IS NULL;"
            par = tuple([filename, schemaname, tablename])
            Database.executeSQL(parent, cnx, sql, par, silent=True)
            Database.commit(parent, cnx)
        return dataset
    # /getDataset

    def setDatasetTable(self, parent, cnx, schemaname, tablename,
                        filename=None, filedate=None, cnt=0, elapsed=None):
        sql = f"SELECT schemaname FROM {schemaname}.table_datasets " \
              "WHERE schemaname=%s " \
              "AND tablename=%s"
        par = tuple([schemaname, tablename])
        result = Database.readDatabaseResult(parent, cnx, sql, par)
        pars = []
        if result:
            sql = f"UPDATE {schemaname}.table_datasets\n" \
                  "SET dataset_file="
            if filename:
                sql += "%s"
                pars.append(filename)
            else:
                sql += "NULL"
            sql += ", dataset_date="
            if filedate:
                sql += "%s"
                pars.append(filedate)
            else:
                sql += "NULL"
            sql += ", dataset_cnt=%s"
            pars.append(cnt)
            if elapsed is not None:
                t = int(elapsed.total_seconds())
                sql += ", dataset_load_seconds=%s"
                pars.append(t)
            sql += "\nWHERE schemaname=%s " \
                "AND tablename=%s"
            pars.extend([schemaname, tablename])
        else:
            sql = f"INSERT INTO {schemaname}.table_datasets\n" \
                  "(schemaname, tablename, " \
                  "dataset_file, dataset_date, dataset_cnt, " \
                  "dataset_load_seconds) " \
                  "\nVALUES\n(%s, %s, "
            pars.extend([schemaname, tablename])
            if filename:
                sql += "%s, "
                pars.append(filename)
            else:
                sql += "NULL, "
            if filedate:
                sql += "%s, "
                pars.append(filedate)
            else:
                sql += "NULL, "
            sql += "%s, "
            pars.append(cnt)
            if elapsed is not None:
                t = int(elapsed.total_seconds())
                sql += ", dataset_load_seconds=%s"
                pars.append(t)
            else:
                sql += "NULL)"
        par = tuple(pars)
        Database.executeSQL(parent, cnx, sql, par, silent=True)
        Database.commit(parent, cnx)
    # /setDatasetTable

    def dropIndexes(self, parent, cnx, schemaname, tablename):
        parent.appendLog('    drop indexes...')
        sql = "SELECT INDEX_NAME " \
              "FROM information_schema.statistics " \
              "WHERE TABLE_SCHEMA=%s " \
              "AND TABLE_NAME=%s " \
              "AND INDEX_NAME!='PRIMARY' " \
              "AND INDEX_NAME!='UNIQUE'"
        par = tuple([schemaname, tablename])
        indexes = Database.readDatabase(parent, cnx, sql, par)
        for index in indexes:
            sql = f"ALTER TABLE {schemaname}.{tablename}\n" \
                  f"DROP INDEX {index[0]}"
            Database.executeSQL(parent, cnx, sql, silent=True)
        parent.appendLog('    dropped indexes')
    # /dropIndexes

    def createMissingIndexes(self, parent, cnx, schemaname):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f'\nCreating indexes in {schemaname}...')
        sql = "SELECT c.TABLE_NAME, c.COLUMN_NAME, " \
              "c.ORDINAL_POSITION, c.DATA_TYPE\n" \
              "FROM information_schema.COLUMNS c " \
              "INNER JOIN information_schema.TABLES t " \
              "ON c.TABLE_CATALOG = t.TABLE_CATALOG " \
              "AND c.TABLE_SCHEMA = t.TABLE_SCHEMA " \
              "AND c.TABLE_NAME = t.TABLE_NAME\n" \
              "WHERE t.TABLE_SCHEMA = %s " \
              "AND t.TABLE_TYPE='BASE TABLE' " \
              "AND t.TABLE_NAME not in ('geometry_columns', " \
              "'apatial_ref_sys', 'table_datasets')\n" \
              "EXCEPT\n" \
              "SELECT c.TABLE_NAME, c.COLUMN_NAME, " \
              "c.ORDINAL_POSITION, c.DATA_TYPE\n" \
              "FROM information_schema.COLUMNS c " \
              "INNER JOIN information_schema.TABLES t " \
              "ON c.TABLE_CATALOG = t.TABLE_CATALOG " \
              "AND c.TABLE_SCHEMA = t.TABLE_SCHEMA " \
              "AND c.TABLE_NAME = t.TABLE_NAME\n" \
              "INNER JOIN information_schema.statistics s " \
              "ON c.TABLE_CATALOG = s.TABLE_CATALOG " \
              "AND c.TABLE_SCHEMA = s.TABLE_SCHEMA " \
              "AND c.TABLE_NAME = s.TABLE_NAME " \
              "AND c.COLUMN_NAME = s.COLUMN_NAME\n" \
              "WHERE t.TABLE_SCHEMA = %s " \
              "AND t.TABLE_TYPE='BASE TABLE' " \
              "AND t.TABLE_NAME not in ('geometry_columns', " \
              "'apatial_ref_sys', 'table_datasets')\n" \
              "ORDER BY TABLE_NAME ASC, ORDINAL_POSITION ASC"
        par = tuple([schemaname, schemaname])
        fields = Database.readDatabase(parent, cnx, sql, par)
        for field in fields:
            if Utilities.isGeometryField(field[3]):
                log = '    ' \
                      f'{str("create feature shape index ").ljust(48)}' \
                      f'  on {field[0].ljust(40)}' \
                      f'  {Utilities.getNowString()}...'
                parent.appendLog(log)
                sql = f"ALTER TABLE {schemaname}.{field[0]}\n" \
                      f"ADD SPATIAL INDEX ({field[1]});"
                Database.executeSQL(parent, cnx, sql, silent=True)
            elif Utilities.isCreateFieldIndex(field[1], field[3]):
                parent.appendLog(f'    create index {field[1].ljust(35)}'
                                 f'  on {field[0].ljust(40)}'
                                 f'  {Utilities.getNowString()}...')
                sql = f"ALTER TABLE {schemaname}.{field[0]}\n" \
                      f"ADD INDEX ({field[1]})"
                Database.executeSQL(parent, cnx, sql, silent=True)
        parent.appendLog(f'Created indexes in {schemaname}')
        parent.unsetCursor()
    # /createMissingIndexes

    def createIndexes(self, parent, cnx, schemaname, tablename, fields):
        parent.appendLog('    create indexes...')
        for field in fields:
            if Utilities.isGeometryField(field.fieldType):
                parent.appendLog('    create feature shape index '
                                 f'\t{Utilities.getNowString()}...')
                sql = f"ALTER TABLE {schemaname}.{tablename}\n" \
                      f"ADD SPATIAL INDEX ({field.fieldName})"
                Database.executeSQL(parent, cnx, sql, silent=True)
            elif Utilities.isCreateFieldIndex(
                    field.fieldName,
                    field.fieldType,
                    field.isKey,
                    field.fieldSrc):
                parent.appendLog(f'    create {field.fieldName} index '
                                 f'\t{Utilities.getNowString()}...')
                sql = f"ALTER TABLE {schemaname}.{tablename}\n" \
                      f"ADD INDEX ({field.fieldName})"
                Database.executeSQL(parent, cnx, sql, silent=True)
        parent.appendLog('    created indexes')
    # /createIndexes

    def processViews(self, parent, cnx, schemaname):
        parent.setCursor(Qt.CursorShape.WaitCursor)
        parent.appendLog(f'\nCreating views in {schemaname}...')
        scriptName = 'linz_schema_views.sql'
        try:
            sqlFile = open(scriptName, 'rt')
            parent.appendLog(f'{scriptName} found')
            self.processViewsScript(parent, cnx, schemaname, sqlFile)
            sqlFile.close()
            parent.appendLog(f'Created views in {schemaname}')
        except IOError:
            try:
                (root, ext) = os.path.split(__file__)
                (file, ext) = os.path.splitext(root)
                if ext == '.zip' or ext == '.pyz':
                    with zipfile.ZipFile(root, 'r') as zip:
                        sqlFile = zip.open(scriptName, 'r')
                        parent.appendLog(f'{scriptName} found')
                        self.processViewsScript(parent, cnx,
                                                schemaname, sqlFile, True)
                        sqlFile.close()
                        parent.appendLog(f'Created views in {schemaname}')
                else:
                    (root, file) = os.path.split(__file__)
                    sqlFile = open(os.path.join(root, scriptName), 'rt')
                    parent.appendLog(f'{scriptName} found')
                    self.processViewsScript(parent, cnx, schemaname, sqlFile)
                    sqlFile.close()
                    parent.appendLog(f'Created views in {schemaname}')
            except IOError as err:
                parent.appendLog(f'Failed to open sql script {scriptName}'
                                 f'\n    {__file__}/{scriptName}\n{err}')
        parent.unsetCursor()
    # /processViews

    def processViewsScript(self, parent, cnx,
                           schemaname, sqlFile, zipped=False):
        parent.appendLog('Run sql script...')
        try:
            sql = None
            dependencies = None
            for zline in sqlFile:
                if zipped:
                    line = zline.decode('utf-8')
                else:
                    line = zline
                if line:
                    line = line.replace('\r\n', '\n').lstrip().rstrip()
                    if line.startswith('#') or line.startswith('--'):
                        if line.find("--DEPENDENCIES--") >= 0:
                            d1 = line.find("{") + 1
                            d2 = line.find("}")
                            dependencies = line[d1:d2]
                    else:
                        if sql:
                            sql += '\n' + line
                        else:
                            sql = line
                        if sql.endswith(';'):
                            sql = self.processViewsScriptSql(
                                parent, cnx, schemaname, sql, dependencies)
                            dependencies = None
        except IOError as err:
            parent.appendLog(f'Failed to read sql script\n{err}')
    # /processViewsScript

    def processViewsScriptSql(self, parent, cnx, schemaname, sql, dependencies):
        sqlT = sql.replace('{schema}', schemaname)
        viewname = Utilities.createViewname(sqlT)
        if Utilities.isDropSql(sqlT):
            parent.appendLog(f'    Drop view {viewname}')
            Database.executeSQL(parent, cnx, sqlT)
        else:
            isDependent = False
            parent.appendLog(f'    Create view {viewname}')
            if dependencies:
                for dependency in dependencies.split():
                    if Database.isTableExist(parent, cnx,
                                             schemaname, dependency):
                        pass
                    else:
                        isDependent = True
                        parent.appendLog(
                            "        dependency not found: "
                            f"{schemaname}.{dependency}")
            if isDependent:
                parent.appendLog('    view not created')
            else:
                Database.executeSQL(parent, cnx, sqlT)
        return None
    # /processViewsScriptSql
# /SchemasActions
