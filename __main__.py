# This is a sample Python script.
# Press Shift+F6 to execute it or replace it with your code.

import importlib.util
if importlib.util.find_spec("linz_schema_loader"):
    from linz_schema_loader import linz_schema_loader
else:
    from .linz_schema_loader import linz_schema_loader

if __name__ == '__main__':
    # print('__main__ ')
    linz_schema_loader.run()
