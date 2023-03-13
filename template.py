#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TODO: What the module is doing
"""

__version__ = 230114032110
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # This is the level that is actually used
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(module)s:%(funcName)s:%(lineno)d - %(message)s'))
if logger.handlers:
    logger.removeHandler(logger.handlers[0]) # When you importlib.reload() a module, we need to clear out the old logger
logger.addHandler(console_handler)

import harding_utils as hu

def file_work(arg_file: str, arg_update: bool = False) -> str:
    ''' This is all the work done on each file '''

    logger.debug(f"TODO: Work here on {arg_file}")
    if arg_update:
        logger.debug("TODO: it should be an update")
    return (f"{arg_file} is done!")

def module_work(arg_files: list, arg_update: bool = False) -> list:
    ''' This is all the work the module is doing '''

    logger.info("Welcome to TODO: Template!")
    res = []
    for file in arg_files:
        res.append(file_work(file, arg_update))
    return res

def module_main(arg_argv: dict = None) -> list:
    ''' This function can be used from an interactive prompt such as Ipython or Jupyter '''

    if not arg_argv:
        arg_argv = {}
    debug_mode = arg_argv.get("debug_mode", False)

    logger.debug("TODO: Sanity check on the keys in the arg_argv")
    logger.debug(hu.dict_to_json_string_pretty(arg_argv))

    files = []
    if "-" == arg_argv.get('files', [""])[0]:
        files.append("-")
    else:
        files = hu.adv_glob(arg_argv.get('files', ""), arg_argv.get('check_subfolders', False))

    if not files:
        error_msg = "arg_files[] is empty!"
        logger.critical(error_msg)
        return [error_msg]

    if debug_mode:
        logger.debug("Entering debug mode")

    return module_work(arg_files=files, arg_update=arg_argv.get('update', False))

if __name__ == "__main__":
    import argparse

    version = f"v{__version__} by {__author__} {__email__}"
    parser = argparse.ArgumentParser(
        description=f"{__description__} {version}")
    parser.add_argument("-s", "--subfolders", action="store_true",
                        dest="check_subfolders", help="Look in subfolders", default=False)
    parser.add_argument("-u", "--update", action="store_true",
                        dest="update", help="Update the file", default=False)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    main_res = module_main(args.__dict__)
    for r in main_res:
        logger.info(r)
