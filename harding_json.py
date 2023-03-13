#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Takes a JSON file and parse it nicely. Can also update from the internet.
"""

__version__ = 230124161636
__author__ = "Harding"
__description__ = "Takes a JSON file and parse it nicely. Can also update from the internet."
__copyright__ = "Copyright 2022"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

json_source = "json_source"
json_date = "json_date"
json_data = "json_data"

import harding_utils as hu

def unwrapped_json(arg_file:str) -> dict:
    ''' If our JSON is wrapped with our metadata, then return the original dict '''
    
    _wrapped = wrapped_json(arg_file)
    return _wrapped.get('json_data', None)

def wrapped_json(arg_file:str, arg_save_as:str = None) -> dict:
    updated_at = ""
    if isinstance(arg_file, dict):
        json_content = arg_file
    else:
        if arg_file.startswith("http"):
            if not arg_save_as:
                _t = hu.smart_filesystem_safe_path(arg_file)
                _t += ".json"
                _t = _t.replace(".json.json", ".json")
            else:
                _t = arg_save_as
            
            _t = hu.download_file(arg_url=arg_file, arg_local_filename=_t)
            updated_at = hu.now_nice_format()
        else:
            _t = arg_file

        json_content = hu.dict_load_json_file(_t)
    
    # Here we have the JSON data in our dict
    if json_data not in json_content:
        updated_at = hu.now_nice_format()
        json_content = {json_source: arg_file, json_date: updated_at, json_data: json_content}
    
    return json_content

def file_work(arg_file:str, arg_update_json:bool = False):
    """ This is all the work done on each file """
    
    json_content = wrapped_json(arg_file)
    if arg_update_json and not arg_file.startswith('http'):
        if json_source not in json_content:
            hu.error_print(f"No field named \"{json_source}\" in the JSON, cannot update!")
            return None
        json_content = wrapped_json(json_content[json_source], arg_save_as = arg_file)
    
    print(hu.dict_to_json_string_pretty(json_content[json_data]))
    if json_source in json_content:
        print(f"Downloaded from {json_content[json_source]}")
    if json_date in json_content:
        print(f"Last downloaded at {json_content[json_date]}")

    return json_content[json_data]

def module_work(arg_files:list, arg_update_json:bool = False) -> int:
    ''' This is all the work the module is doing '''
    for file in arg_files:
        file_work(file, arg_update_json)
    return 0

def module_main(arg_argv:dict = None) -> int:
    ''' This function can be used from an interactive prompt such as Ipython or Jupyter '''

    if not arg_argv:
        arg_argv = {}
    debug_mode = arg_argv.get("debug_mode", False)

    # TODO: Make sure that the keys that you are expecting exists
    print(hu.dict_to_json_string_pretty(arg_argv))

    files = []
    if "-" == arg_argv.get('file', [""])[0]:
        files.append("-")
    else:
        files = hu.adv_glob(arg_argv.get('file', ""), arg_argv.get('check_subfolders', False))
    
    if not files:
        hu.error_print("files[] is empty!")
        return -1

    return module_work(files, arg_argv.get('update_json', False))

if __name__ == "__main__":
    ''' Main function is run when the script is called from the console. Only parse the arguments into a dict and send to module_main() '''
    import argparse

    version = f"v{__version__} by {__author__} {__email__}"
    parser = argparse.ArgumentParser(
        description=f"{__description__} {version}")
    parser.add_argument("-s", "--subfolders", action="store_true",
                        dest="check_subfolders", help="Look in subfolders", default=False)
    parser.add_argument("-u", "--update", action="store_true",
                        dest="update_json", help="Update the JSON file", default=False)
    parser.add_argument("file", nargs="+")
    args = parser.parse_args()

    module_main(args.__dict__)

