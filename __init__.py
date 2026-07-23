"""
Initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    from .linz_schema_loader import linz_schema_loader
    return linz_schema_loader(iface)
