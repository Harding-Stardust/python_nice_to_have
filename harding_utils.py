#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains many helper functions to make some parts of your life easier.

In general I try to have the first word in the function connected to what the function is working on for easier tab completion.
"""

__version__ = 230217121512
__author__ = "Harding"
__copyright__ = "Copyright 2023"
__credits__ = ["Many random ppl on the Internet"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

import sys
import os
import io
import datetime
import time
import inspect as _inspect
import json
import glob
import re
import decimal
from typing import Union, Dict, List, Tuple, Set, TypeVar, Any
from types import ModuleType

use_natsort = True
try: # It will function without this sorting
    import natsort
except ImportError:
    use_natsort = False
    print("WARNING: Module natsort not installed, this module is not required but strongly recommended. pip install natsort")

__user_agent__ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'

def adv_glob(arg_paths: Union[List[str], str], arg_recursive: bool = False, arg_supress_errors: bool = False, arg_debug: bool = False) -> List[str]:
    ''' Returns a list of files (with full path) that matches a list of filters.
        Example arg_paths: c:\\a.txt c:\\a\\folder1 folder* folder1 folder2\\ folder1\\* fodler5 non-existant_file.txt folder2 *.log

        # TODO: Rewrite this function with https://docs.python.org/3/library/pathlib.html#pathlib.Path
        # TODO: If I give "file1.mp4 *.mp4" This should expand the *.mp4 (which include file1.mp4) but only handle that file once.
        # This is for doing something on many files but prio the first one
    '''

    _list_of_urls = []
    file_filters: Dict[str, Set] = {}
    arg_paths_list: list
    if isinstance(arg_paths, str):
        arg_paths_list = [arg_paths]
    elif isinstance(arg_paths, list):
        arg_paths_list = arg_paths
    else:
        raise ValueError(f"argument arg_paths is: {type(arg_paths)} and I can only handle str or list")

    # arg_paths_list = arg_paths # TODO: Investigate
    for i in arg_paths_list:
        # file_filters becomes "*.*" if you give them without any filter
        if i.startswith('http'):
            debug("URL: " + str(i), not arg_debug)
            _list_of_urls.append(i)
        elif os.path.isdir(i):
            debug("Folder: " + str(i), not arg_debug)
            if not os.path.abspath(i) in file_filters:
                file_filters[os.path.abspath(i)] = set()
            file_filters[os.path.abspath(i)].add("*")
        elif os.path.dirname(os.path.abspath(i)) and os.path.basename(os.path.abspath(i)):
            debug(f"Split to k = '{os.path.dirname(os.path.abspath(i))}'   v = '{os.path.basename(os.path.abspath(i))}'", not arg_debug)
            if not os.path.dirname(os.path.abspath(i)) in file_filters:
                file_filters[os.path.dirname(os.path.abspath(i))] = set()
            file_filters[os.path.dirname(os.path.abspath(i))].add(os.path.basename(os.path.abspath(i)))

    # Remove invalid paths (file_filters that don't exists) ignore URLs
    file_filters_2 = {}
    for k, v in file_filters.items():
        if os.path.isdir(k):
            debug(f"k: {k}, v: {v}", not arg_debug)
            file_filters_2[k] = v
        elif k.startswith('http'):
            continue
        elif not arg_supress_errors:
            warning_print("Could not find folder \"" + k + "\"")
    file_filters = file_filters_2

    debug("File filters = " + str(file_filters), not arg_debug)

    # Filters done, now create a file list
    return_list = []
    for k, v in file_filters.items():
        return_list.extend(list_of_files(k, v, arg_recursive, arg_supress_errors, arg_debug))

    return_list = list(set(return_list))
    return_list.sort()
    return_list.extend(_list_of_urls)
    return return_list

def list_of_files(arg_folder: str,
                  arg_filters: Union[None, str, List, Set, Tuple] = "*",
                  arg_recursive: bool = False,
                  arg_supress_errors: bool = False,
                  arg_debug: bool = False) -> List[str]:
    """ Helper funtion to adv_glob """
    res: List[str] = []
    filters = list_from_str(arg_filters)
    if not filters:
        return res
    debug("list_of_files() arg_folder = " + arg_folder + ", argfilters = " + str(filters) + "", not arg_debug)
    # Add all files matching the filter. OBS! No folders whatsoever
    for i in filters:
        full_path = os.path.join(arg_folder, i).replace('[', '?').replace(']', '?')
        debug(full_path, not arg_debug)
        the_glob_list = glob.glob(full_path)

        debug("list_of_files() Globbing " + os.path.join(arg_folder, i) + " = " + str(the_glob_list), not arg_debug)
        for j in the_glob_list:
            if os.path.isfile(j):
                res.append(j)

    # If we should be recursive then do this for all folders
    if arg_recursive:
        sub_folders = []
        try:
            sub_folders = os.listdir(arg_folder)
        except:
            warning_print("Could not open \"" + arg_folder + "\" for file listing")
        for i in sub_folders:
            if os.path.isdir(os.path.join(arg_folder, i)):
                res.extend(list_of_files(os.path.join(arg_folder, i), arg_filters, arg_recursive, arg_supress_errors, arg_debug))
    return res

def ensure_dir(arg_full_path: str):
    _dirs = os.path.dirname(arg_full_path)
    if not os.path.exists(_dirs):
        os.makedirs(_dirs)

def download_file(arg_url: str, #pylint: disable=too-many-arguments
                  arg_proxy_string_to_curl: str = "",
                  arg_origin: str = "",
                  arg_referer: str = "",
                  arg_local_filename: Union[str, None] = None,
                  arg_check_remote_filesize: bool = False,
                  arg_max_num_bytes: int = 0,
                  arg_rate_limit: str = "100M"
                  ) -> str:
    """ Download a file with CURL and look like a normal web browser """

    if not arg_local_filename:
        arg_local_filename = os.path.join(f"0000_{now_nice_format(arg_filename_safe=True)}_download.tmp")

    if arg_proxy_string_to_curl and not arg_proxy_string_to_curl.startswith("-x "):
        arg_proxy_string_to_curl = "-x " + arg_proxy_string_to_curl
    head = ""
    _range = ""
    if arg_check_remote_filesize:
        head = "--head "
    elif arg_max_num_bytes > 0:
        _range = f"--range 0-{arg_max_num_bytes}"

    # show_verbose = "-s" # -s --> silent, no screen output, set this to "-v" for verbose and "-vvv" for VERY verbose
    show_verbose = ""

    curl_command = 'curl'
    curl_command += ' --speed-time 60' # https://curl.se/docs/manpage.html#-y If a transfer runs slower than speed-limit bytes per second during a speed-time period, the transfer is aborted. If speed-time is used, the default speed-limit will be 1 unless set with -Y, --speed-limit.
    curl_command += ' --speed-limit 500' # https://curl.se/docs/manpage.html#-Y If a transfer is slower than this given speed (in bytes per second) for speed-time seconds it gets aborted. speed-time is set with --speed-time and is 30 if not set.
    curl_command += ' --retry 20' # https://curl.se/docs/manpage.html#--retry If a transient error is returned when curl tries to perform a transfer, it will retry this number of times before giving up. Setting the number to 0 makes curl do no retries (which is the default).
    curl_command += f' -e "{arg_referer}"'
    curl_command += f' -H "Origin: {arg_origin}"'
    curl_command += ' -H "Sec-Fetch-Site: cross-site"'
    curl_command += ' -H "Sec-Fetch-Mode: cors"'
    curl_command += ' -H "Sec-Fetch-Dest: empty"'
    curl_command += f' -A "{__user_agent__}"'
    curl_command += f' {arg_proxy_string_to_curl}' # https://curl.se/docs/manpage.html#-x The proxy string can be specified with a protocol:// prefix. No protocol specified or http:// will be treated as HTTP proxy. Use socks4://, socks4a://, socks5:// or socks5h:// to request a specific SOCKS version to be used. If the port number is not specified in the proxy string, it is assumed to be 1080.
    curl_command += f' {show_verbose}'
    curl_command += ' -L' # -L is --location --> if we get a HTTP 3XX Location response, we follow that. https://curl.se/docs/manpage.html#-L
    curl_command += f' {head}'
    curl_command += f' {_range}'
    curl_command += f' --limit-rate {arg_rate_limit}' # https://everything.curl.dev/usingcurl/transfers/rate-limiting    The rate limit value can be given with a letter suffix using one of K, M and G for kilobytes, megabytes and gigabytes.
    curl_command += ' -H "Accept-Language: en-US,en;q=0.9"'
    curl_command += f' -o "{arg_local_filename}"'
    curl_command += ' --continue-at -' # https://curl.se/docs/manpage.html#-C
    curl_command += f' "{arg_url}"'
    timestamped_print("\n\n" + curl_command + "\n\n", arg_force_flush=True)
    if 0 == os.system(curl_command):
        return arg_local_filename
    error_print(f'Curl failed to download "{arg_url}"')
    return "ERROR: CURL FAILED!" # TODO: return None?

def now_nice_format(arg_filename_safe: bool = False, arg_utc: bool = False) -> str:
    """ Helper function for timestamped_line() """

    dt = datetime.datetime.utcnow() if arg_utc else datetime.datetime.now()
    res = time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.timetuple(dt))
    if arg_filename_safe:
        return smart_filesystem_safe_path(res)
    return res

def timestamped_line(arg_str: str = "") -> str:
    return f"[{now_nice_format()}] {arg_str}"

def timestamped_print(arg_str: str = "", arg_file = sys.stdout, arg_force_flush: bool = False):
    print(timestamped_line(arg_str), file=arg_file, flush=arg_force_flush)

def _file_and_line_number(arg_num_function_away: int = 2) -> _inspect.Traceback:
    ''' Internal function. Used in log_print() '''
    callerframerecord = _inspect.stack()[arg_num_function_away]      # 0 represents this line
    frame = callerframerecord[0]                                     # 1 represents line at caller and so on
    info = _inspect.getframeinfo(frame)                              # info.filename, info.function, info.lineno
    return info

def log_print(arg_string: str, #pylint: disable=too-many-arguments
              arg_actually_log: bool = True,
              arg_type: str = "DEBUG",
              arg_file = sys.stdout,
              arg_force_flush: bool = False,
              arg_num_function_away: int = 2
              ) -> None:
    ''' Used for outputing code trace while development '''
    if arg_actually_log:
        info = _file_and_line_number(arg_num_function_away)
        function_name = info.function
        if function_name == "<module>":
            function_name = os.path.basename(info.filename)
        else:
            function_name = f"{os.path.splitext(os.path.basename(info.filename))[0]}.{function_name}"
        log_line = f"{arg_type}: {function_name}:{info.lineno} --> {arg_string}"

        timestamped_print(arg_str=log_line, arg_file=arg_file, arg_force_flush=arg_force_flush)

_ExpType = TypeVar('_ExpType')
def debug(exp: _ExpType, arg_supress_output: bool = False, arg_out_handle = sys.stderr) -> _ExpType:
    ''' Modded version of pydbg '''
    if arg_supress_output:
        return exp

    for frame in _inspect.stack():
        if not frame.code_context:
            break
        line = frame.code_context[0]
        start = line.find('debug(') + 1

        if start:
            exp_str = find_matching_brackets(line[start - 1:], arg_opening_brackets = '(')
            if exp_str:
                exp_str = exp_str[6:-1] # Strip  the 'debug(' and the trailing ')'

            # Remove the arguments to this function (if there are any)
            all_parts = exp_str.split(',')
            if 1 == len(all_parts):
                exp_res = all_parts[0]
            else:
                if all_parts:
                    exp_res = ""
                    for part in all_parts:
                        exp_res += part + ','
                        if find_matching_brackets(exp_res[:-1], arg_opening_brackets='('):
                            exp_res = exp_res[:-1]
                            break

            exp_res = exp_res.strip()

            # import ast
            # a = ast.parse(exp_res)
            # b = ast.dump(a)
            # print(b, file=arg_out_handle)

            timestamped_print(
                f" {frame.filename}:{frame.lineno}: {exp_res} --> {exp!r}",
                arg_file=arg_out_handle,
            )
            break

    return exp

def console_color(arg_string: str, arg_color: str = "OKGREEN") -> str:
    ''' Returns a new string with console marker at the start and at the end '''
    l_console_color = {}
    l_console_color["HEADER"] = '\033[95m'
    l_console_color["OKBLUE"] = '\033[94m'
    l_console_color["OKGREEN"] = '\033[92m'
    l_console_color["WARNING"] = '\033[93m'
    l_console_color["FAIL"] = '\033[91m'
    l_console_color["BOLD"] = '\033[1m'
    l_console_color["UNDERLINE"] = '\033[m'
    l_console_color["RED"] = '\033[31m'
    l_console_color["YELLOW"] = '\033[33m'
    l_console_color["CYAN"] = '\033[36m'
    l_console_color["MAGENTA"] = '\033[35m'
    l_console_color["WHITE"] = '\033[37m'
    l_console_color["ENDC"] = '\033[0m' # Use this to go back to normal color

    if arg_color not in l_console_color:
        warning_print(f"No such color: {arg_color}")
        return arg_string

    return f'{l_console_color[arg_color]}{arg_string}{l_console_color["ENDC"]}'

def warning_print(arg_string: str):
    log_print(arg_type="WARNING", arg_string=console_color(arg_string, arg_color="WARNING"), arg_num_function_away=3)

def error_print(arg_string: str):
    log_print(arg_type="ERROR", arg_string=console_color(arg_string, arg_color="FAIL"), arg_num_function_away=3)

def success_print(arg_string: str):
    timestamped_print(console_color(f"SUCCESS! {arg_string}", "HEADER"))

# Dictionaries are nice to handle data in Python, here I have some helper functions for them
def dict_count(arg_dict: dict, arg_key) -> dict:
    """ A dict where the value is another dict: count how many different values there are.
    ex: dict_count({"1001": {"name": "Spongebob", "age": 35}, "1002": {"name": "Patrick", "age": 35}, "1003": {"name": "Squidward", "age": 43}}, "age")
    """

    res: Dict[Any, int] = {}
    for v in arg_dict.values():
        for k2, v2 in v.items():
            if arg_key == k2:
                res[v2] = res.get(v2, 0) + 1
    return res

def dict_get_key_from_value(arg_dict: dict, arg_value):
    for k, v in arg_dict.items():
        if v == arg_value:
            return k
    return None

def dict_sort(arg_dict: dict, arg_sort_by_value: bool = False, arg_desc: bool = False) -> dict:
    ''' Returns a new sorted dictionary '''
    res = {}
    sort_function = sorted
    if use_natsort:
        sort_function = natsort.natsorted
    if arg_sort_by_value:
        res = dict(sort_function(arg_dict.items(), key=lambda item: item[1])) # Sort by value ( lower -> higher )
    else:
        _list = sort_function(arg_dict.items())
        for _t in _list:
            res[_t[0]] = _t[1]

    if arg_desc:
        res = {k: res[k] for k in reversed(res)} # Just reverse the dict

    return res

def dict_move_to_start(arg_dict: dict, arg_key) -> dict:
    ''' Returns a new dict with the given key as the first key '''
    res = {}
    res[arg_key] = arg_dict.pop(arg_key)
    for k, v in arg_dict.items():
        res[k] = v
    return res

def dict_to_json_string_pretty(arg_dict: Union[dict, list], arg_as_html: bool = False) -> str:
    res = json.dumps(arg_dict, ensure_ascii=False, indent=4, default=str)
    if arg_as_html:
        res = res.replace("\n", "<br/>\n")
    return res

def dict_dump_to_json_file(arg_dict: Union[dict, list], arg_filename: str) -> bool:
    if isinstance(arg_dict, str) and isinstance(arg_filename, dict): # Sometimes I mix up the order, if I do then just make the code fix it for me
        arg_dict, arg_filename = arg_filename, arg_dict

    if not (isinstance(arg_dict, (dict, list))) or not isinstance(arg_filename, str):
        raise ValueError(f'Invalid arguments. arg_dict is of type: {type(arg_dict)} and arg_filename is of type: {type(arg_filename)}')

    data = dict_to_json_string_pretty(arg_dict)
    with io.open(arg_filename, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    return True

def dict_load_json_file(arg_filename_or_url: str) -> Union[Dict, None]:
    ''' Takes a filename or URL and parse it as a dict '''

    file_content = text_read_whole_file(arg_filename_or_url)
    if not file_content:
        return None
    return json.loads(file_content)

def dict_list_to_massive_dict(arg_list: List[Any], arg_key) -> Union[Dict, None]:
    ''' Converts a list of dicts --> one massive dict '''
    res = {}
    for item in arg_list:
        if arg_key not in item:
            error_print(f"Could not find \"{arg_key}\" as key in arg_dict")
            return None

        res[str(item[arg_key])] = item # There is a "bug" in Python that JSON keys is always string but Python can have ints as keys: https://stackoverflow.com/a/1451857
    return res

def dict_add(arg_original: dict, arg_updated: dict, arg_let_original_values_be: bool = False) -> dict:
    ''' First dict is the original, the next arg is the new dict you want to add on top (overwriting keys that already exists)

    TODO: dict.update() can be used?
    '''
    res = arg_original.copy()
    for k, v in arg_updated.items():
        if arg_let_original_values_be and k in res:
            continue

        res[k] = v

    return res

def dict_compare(d1: dict, d2: dict) -> dict:
    ''' Determine what the difference beetween d1 and d2. Rule of thought, we are in state d1 and moved to state d2. What has happened? '''
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    shared_keys = d1_keys.intersection(d2_keys)
    added = d2_keys - d1_keys
    removed = d1_keys - d2_keys
    modified = {o : (d1[o], d2[o]) for o in shared_keys if d1[o] != d2[o]}
    same = set(o for o in shared_keys if d1[o] == d2[o])
    return {'added': added, 'removed': removed, 'modified': modified, 'same': same}

def dict_sub(arg_original: dict, arg_updater: dict) -> dict:
    ''' Returns a new dict with the keys that are in arg_updater removed from arg_original '''
    res = {}
    list_of_items_left = list(set(arg_original) - set(arg_updater))
    for key in list_of_items_left:
        res[key] = arg_original[key]

    return res

def dict_intersect(arg_left: dict, arg_right: dict) -> dict:
    return {key: arg_left[key] for key in arg_left if key in arg_right}

# End of dict helpers

def smart_filesystem_safe_path(arg_file_path: Union[str],
                               arg_allow_swedish_chars: bool = False,
                               arg_fix_season_and_episodes: bool = True,
                               arg_replacement_char: str = '.') -> str:
    ''' Make a long and weird string into something that the OS likes more to handle '''
    res = str(arg_file_path)

    l_dir = ''
    if arg_file_path[1] == ':' and arg_file_path[2] == '\\': # Full path: C:\dir\file.txt
        arg_file_path = arg_file_path[0].upper() + arg_file_path[1:] # I like when the drive letter is uppercase
        l_dir = os.path.dirname(arg_file_path)
        res = os.path.basename(arg_file_path)

    if not arg_allow_swedish_chars:
        res = res.replace("å", "a")
        res = res.replace("ä", "a")
        res = res.replace("ö", "o")
        res = res.replace("Å", "A")
        res = res.replace("Ä", "A")
        res = res.replace("Ö", "O")

    res = res.replace("https://", "")
    res = res.replace("http://", "")
    res = res.replace("\\", arg_replacement_char)
    res = res.replace("%", arg_replacement_char)
    res = res.replace(":", arg_replacement_char)
    res = res.replace("_", arg_replacement_char)
    res = res.replace("/", arg_replacement_char)
    res = res.replace("?", arg_replacement_char)
    res = res.replace("-", arg_replacement_char)
    res = res.replace("#", arg_replacement_char)
    res = res.replace("*", arg_replacement_char)
    res = res.replace(" ", arg_replacement_char)
    res = res.replace("｜", "") # special char that yt-dlp generate
    res = res.replace("：", "") # special char that yt-dlp generate
    res = res.replace("？", "") # special char that yt-dlp generate
    res = res.replace('"', "")
    res = res.replace("'", "")
    res = res.replace("[", arg_replacement_char)
    res = res.replace("]", arg_replacement_char)
    res = res.replace("\t", "")
    res = res.replace(".–", arg_replacement_char)
    res = res.replace("–.", arg_replacement_char)

    if arg_fix_season_and_episodes:
        res = re.sub(r'sasong.(\d\d?).avsnitt.(\d\d?)', 'S0\\1E0\\2', res, flags=re.IGNORECASE) # Swedish naming: Säsong-1-avsnitt-1 --> S01E01
        res = re.sub(fr'([{arg_replacement_char}])S0(\d\d)E(\d\d?\d?)', '\\1S\\2E\\3', res, flags=re.IGNORECASE) # Fix Season numbers 'S011' --> 'S11'
        res = re.sub(fr'([{arg_replacement_char}])S(\d\d)E0(\d\d)', '\\1S\\2E\\3', res, flags=re.IGNORECASE) # Fix episode numbers 'E012' --> 'E12'

    res = os.path.join(l_dir, res)
    while res != res.replace('__', arg_replacement_char):
        res = res.replace('__', arg_replacement_char)
    while res != res.replace('  ', arg_replacement_char):
        res = res.replace('  ', arg_replacement_char)
    while res != res.replace('..', arg_replacement_char):
        res = res.replace('..', arg_replacement_char)
    return res

def regexp_findall_quick_fix(arg_needle: str,
                             arg_haystack: str,
                             arg_default_return_if_not_found: Union[List[str], None] = None
                             ) -> List[str]:
    ''' # TODO: Write docstring '''
    m = re.findall(arg_needle, arg_haystack)
    if m:
        return m

    if not arg_default_return_if_not_found:
        return ['<< Not found >>']

    if not isinstance(arg_default_return_if_not_found, list):
        arg_default_return_if_not_found = [arg_default_return_if_not_found]
    #  Return looks like this: [("first group of first full match", "second group of first full match"),
    #                           ("first group of second full match", "second group of second full match")]
    return arg_default_return_if_not_found

def get_size_as_B_KB_MB_GB(arg_size: Union[float, int], arg_force_unit: bool = False) -> str:
    del arg_force_unit # TODO: arg_force_unit is not implemented yet
    units = ["B", "KB", "MB", "GB", "TB"]
    temp = float(arg_size)
    for i in range(0, len(units) - 1):
        if temp >= 1024.0:
            temp /= 1024.0
        else:
            return f"{temp:0.2f} {units[i]}"

    return f"{temp:0.2f} {units[-1]}"

def find_matching_brackets(arg_haystack: str, arg_opening_brackets: str = '{', arg_start_with_counter: int = 0):
    closing_brackets_dict = {'[': ']', '{': '}', '(': ')', '<': '>'}
    closing_brackets = closing_brackets_dict[arg_opening_brackets]

    for i in range(0, len(arg_haystack)):
        if arg_haystack[i] == arg_opening_brackets:
            arg_start_with_counter += 1
        elif arg_haystack[i] == closing_brackets:
            arg_start_with_counter -= 1
            if 0 == arg_start_with_counter:
                return arg_haystack[0:i+1]
    # timestamped_print("ERROR! find_matching_brackets() failed to find anything")
    return ""

def get_part_of_json(arg_haystack, arg_start_marker_regexp, arg_opening_brackets = '{', arg_start_with_counter = 0):
    json_result = ""

    match = re.search(arg_start_marker_regexp, arg_haystack)
    if match:
        match_index = match.start()
        # Let's backup until we get the part before the match included in the arg_start_marker_regexp
        number_of_opening_brackets_left_to_find = arg_start_with_counter
        for i in range(match_index, 0, -1):
            if arg_haystack[i] == arg_opening_brackets:
                number_of_opening_brackets_left_to_find -= 1
                if 0 == number_of_opening_brackets_left_to_find:
                    json_result = find_matching_brackets(arg_haystack[i:], arg_opening_brackets)
    if len(json_result) > 0:
        return json_result

    error_print("get_part_of_json() failed to find anything")
    return False

def concat_files(arg_folder: str, arg_list_of_files: list, arg_dest_file: str):
    if isinstance(arg_list_of_files, str):
        arg_list_of_files = list_from_str(arg_list_of_files)

    with open(arg_dest_file, "wb") as f:
        for file in arg_list_of_files:
            with open(os.path.join(arg_folder, file), "rb") as f2:
                f.write(f2.read())
    return True

def text_write_whole_file(arg_filename: str, arg_text: str) -> bool:
    ''' Opens a text file (as UTF-8 with newline='\\n') and write the argument text to that file and then close the file  '''
    with io.open(arg_filename, mode="w", encoding="utf-8", newline="\n") as fp:
        fp.write(arg_text)
    return True

def text_read_whole_file(arg_filename_or_url: str) -> Union[str, None]:
    arg_filename_or_url = str(arg_filename_or_url) # This will handle pathlib.Path
    if "http" == arg_filename_or_url[0:4].lower():
        _tmp = download_file(arg_filename_or_url)
        res = text_read_whole_file(_tmp)
        os.remove(_tmp)
        return res

    if "-" == arg_filename_or_url:
        return sys.stdin.read()

    if not os.path.exists(arg_filename_or_url):
        return None
    with io.open(file=arg_filename_or_url, mode="r", encoding="utf-8", newline="\n") as fp:
        r = fp.read()
    return r

def math_nthroot(x: Union[int, float, decimal.Decimal], n: Union[int, float, decimal.Decimal]) -> decimal.Decimal:
    ''' Returns the n:th root of x. Example: x=729, n=3 --> 9 '''
    return decimal.Decimal(pow(decimal.Decimal(x), decimal.Decimal(1)/decimal.Decimal(n)))

def list_from_str(arg_str: Union[str, List, Set, Tuple, None],
                  arg_re_splitter: str = ' |,|;|:|[+]|[-]|[|]|[\n]|[\r]'
                  ) -> Union[List[str], None]:
    ''' Take a str and try to convert into a list of str in a smart way.
    Returns None if something breaks. '''

    if arg_str is None:
        return []
    if isinstance(arg_str, list):
        res = arg_str
    elif isinstance(arg_str, (set, tuple)):
        res = list(arg_str)
    elif isinstance(arg_str, str):
        res = re.split(arg_re_splitter, arg_str)
    else:
        print(f"ERROR! arg_str is of type: {type(arg_str)} which I cannot handle!")
        return None

    res = [x for x in res if x]
    return res

def table_from_html(arg_url: str) -> List[List[str]]:
    from bs4 import BeautifulSoup # Imported here since it's an external lib

    res: List[List[str]] = []
    page = text_read_whole_file(arg_url)
    if not page:
        return res
    html_page = BeautifulSoup(page, "html.parser")
    rows = html_page.find_all("tr")
    for row in rows:
        row_list: List[str] = []

        values = row.find_all("td")
        for value in values:
            value_text = value.encode_contents().strip().decode("UTF-8")
            row_list.append(value_text)
        if len(row_list) > 0:
            res.append(row_list)
    return res

def html_unicode_to_entities(arg_text: str) -> str:
    '''Converts unicode to HTML entities.  For example '&' becomes '&amp;' '''
    import namedentities # type: ignore
    return namedentities.hex_entities(arg_text)

def file_delete(arg_filename: str) -> bool:
    ''' If the file exists, then delete it. If it does NOT exist, just return True

        Returns True if at the end of this function there is no file name arg_filename.
        Will return True even if there never was a file named that.
    '''
    arg_filename = str(arg_filename) # This will handle pathlib.Path
    if os.path.exists(arg_filename):
        os.remove(arg_filename)
    return not os.path.exists(arg_filename)

def reload(arg_module: Union[str, ModuleType, None] = None):
    ''' During development, this is nice to have '''

    import importlib

    l_module: str = arg_module if isinstance(arg_module, str) else getattr(arg_module, '__name__', __name__)
    return importlib.reload(sys.modules[l_module])



def main():
    timestamped_print("This module contains many good helper functions.")
    timestamped_print(f"Version {__version__} by {__author__}")

if "__main__" == __name__:
    main()
