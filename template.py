#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TODO: What the module is doing
"""

__version__ = 231208_003600
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

STRICT_TYPES = True # If you want to have stict type checking: pip install typeguard

from typing import Union, Any, Dict, List
import logging
from types import ModuleType
import harding_utils as hu
try:
    if not STRICT_TYPES:
        raise ImportError("Skipping the import of typeguard reason: STRICT_TYPES == False")
    from typeguard import typechecked
except:
    from typing import TypeVar
    _T = TypeVar("_T")

    def typechecked(target: _T, **kwargs) -> _T:
        return target if target else typechecked

_g_logger = logging.getLogger(__name__)
_g_logger.setLevel(logging.DEBUG) # This is the level that is actually used
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.DEBUG)
_console_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(module)s:%(funcName)s:%(lineno)d - %(message)s'))
if _g_logger.handlers:
    _g_logger.removeHandler(_g_logger.handlers[0]) # When you importlib.reload() a module, we need to clear out the old logger
_g_logger.addHandler(_console_handler)

@typechecked
def _reload(arg_module: Union[str, ModuleType, None] = None):
    ''' Internal function. During development, this is nice to have '''

    import importlib
    import sys

    l_module: str = arg_module if isinstance(arg_module, str) else getattr(arg_module, '__name__', __name__)
    return importlib.reload(sys.modules[l_module])

@typechecked
def file_work(arg_file: str, arg_update: bool = False) -> str:
    ''' This is all the work done on each file '''

    _g_logger.debug("TODO: Starting work on %s", arg_file)
    if arg_update:
        _g_logger.debug("TODO: it should be an update")
    _g_logger.debug("TODO: Ending work on %s", arg_file)
    return f"{arg_file} is done!"

@typechecked
def module_work(arg_files: List[str], arg_update: bool = False) -> List[str]:
    ''' This is all the work the module is doing '''

    _g_logger.info("Welcome to TODO: Template!")
    res: List[str] = []
    for file in arg_files:
        res.append(file_work(file, arg_update))
    return res

@typechecked
def module_main(arg_argv: Union[Dict[str, Any], None] = None) -> List[str]:
    ''' This function can be used from an interactive prompt such as Ipython or Jupyter '''

    if arg_argv is None:
        arg_argv = {}
    debug_mode: bool = arg_argv.get("debug_mode", False)

    _g_logger.debug("TODO: Sanity check on the keys in the arg_argv")
    _g_logger.debug("arg_argv looks like:")
    _g_logger.debug(hu.dict_to_json_string_pretty(arg_argv))

    l_files = []
    if "-" == arg_argv.get('files', [""])[0]:
        l_files.append("-")
    else:
        l_files = hu.adv_glob(arg_argv.get('files', ""), arg_argv.get('check_subfolders', False))

    if not l_files:
        error_msg: str = "arg_files[] is empty!"
        _g_logger.critical(error_msg)
        return [error_msg]

    if debug_mode:
        _g_logger.debug("Entering debug mode")

    return module_work(arg_files=l_files, arg_update=arg_argv.get('update', False))

if __name__ == "__main__":
    import argparse

    version = f"version {__version__} by {__author__} {__email__}"
    parser = argparse.ArgumentParser(
        description=f"{__description__} {version}")
    parser.add_argument("-s", "--subfolders", action="store_true",
                        dest="check_subfolders", help="Look in subfolders", default=False)
    parser.add_argument("-u", "--update", action="store_true",
                        dest="update", help="Update the file", default=False)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    l_main_res: List[str] = module_main(args.__dict__)
    for r in l_main_res:
        _g_logger.info(r)
