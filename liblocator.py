# Helper Module to locate libraries in system
# Place this module in the path on the filesystem you want to find out
# and import it. Then call the path() methode to get the absolute path
# to the modules location.

def path():
    """ Returns the absolute path to the modules location """
    import os
    return os.path.dirname(__file__)