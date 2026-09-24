"""
TODO: What the module is doing
"""

from __future__ import annotations

__version__ = "2026-09-10 01:44:10"
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2026"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

import sys
from typing import Union, Any, Dict, List
import logging # TODO: Change to loguru? https://github.com/Delgan/loguru
from types import ModuleType
from pydantic import validate_call
import harding_utils as _harding_utils

_g_logger = logging.getLogger(__name__)
_g_logger.setLevel(logging.DEBUG) # This is the level that is actually used
_g_console_handler = logging.StreamHandler()
_g_console_handler.setLevel(logging.DEBUG)
_g_console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
if _g_logger.handlers:
    _g_logger.removeHandler(_g_logger.handlers[0]) # When you importlib.reload() a module, we need to clear out the old logger
_g_logger.addHandler(_g_console_handler)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def _reload(arg_module: Union[str, ModuleType, None] = None):
    ''' Internal function. During development, this is nice to have '''

    import importlib
    import sys

    l_module: str = arg_module if isinstance(arg_module, str) else getattr(arg_module, '__name__', __name__)
    return importlib.reload(sys.modules[l_module])

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def print_file_content(arg_file: str) -> bool:
    ''' Openes a file and prints the content '''
    print("This is the content in the file:\n")
    with open(arg_file, "rb") as f:
        print(f.read().decode("utf-8"))
    return True

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def file_work(arg_file: str, arg_update: bool = False) -> str:
    ''' This is all the work done on each file '''
    arg_file = arg_file.strip()

    _g_logger.debug("TODO: Starting work on %s", arg_file)
    if arg_update:
        _g_logger.debug("TODO: it should be an update")
        
    print_file_content(arg_file)
        
    _g_logger.debug("TODO: Ending work on %s", arg_file)
    return f"{arg_file} is done!"

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def module_work(arg_files: List[str], arg_update: bool = False) -> List[str]:
    ''' This is all the work the module is doing '''

    _g_logger.info("Welcome to TODO: Template!")
    res: List[str] = []
    for file in arg_files:
        res.append(file_work(file, arg_update))
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def module_main(arg_argv: Union[Dict[str, Any], None] = None) -> List[str]:
    ''' This function can be used from an interactive prompt such as Ipython or Jupyter '''

    if arg_argv is None:
        arg_argv = {}
    debug_mode: bool = arg_argv.get("debug_mode", False)

    _g_logger.debug("TODO: Sanity check on the keys in the arg_argv")
    _g_logger.debug("arg_argv looks like:")
    _g_logger.debug(_harding_utils.dict_to_json_string_pretty(arg_argv))

    l_files = _harding_utils.adv_glob(arg_argv.get('files', ""), arg_argv.get('check_subfolders', False))

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
    l_args = parser.parse_args().__dict__
    if "-" == l_args["files"][0]:
        l_args["files"] = [l_line.strip() for l_line in sys.stdin.readlines()]
    l_main_res: List[str] = module_main(l_args)
    for r in l_main_res:
        _g_logger.info(r)
