"""
This module contains many helper functions to make some parts of your life easier.

In general I try to have the first word in the function connected to what the function is working on for easier tab completion.
"""

__version__ = "2026-09-05 00:33:07"
__author__ = "Harding"
__copyright__ = "Copyright 2026"
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
import pathlib
import json
import glob
import re
import decimal
import random
import contextlib
from typing import Union, Dict, List, Tuple, Set, TypeVar, TextIO, Any, Optional, Callable, Iterable, Generator
from types import ModuleType
from pydantic import validate_call

_G_USE_NATSORT = True
try: # It will function without this sorting
    import natsort
except ImportError:
    _G_USE_NATSORT = False
    print("WARNING: Module natsort not installed, this module is not required but strongly recommended. pip install natsort")

try:
    import peek as _peek
    _G_PEEK_AVAILABLE: bool = True
except ImportError:  # peek is an optional dependency, debug() falls through to a no-op below #
    _G_PEEK_AVAILABLE = False
    print("WARNING: Module peek-python not installed, this module is not required but strongly recommended. pip install peek-python")

__user_agent__: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
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
    else:
        arg_paths_list = arg_paths

    # arg_paths_list = arg_paths # TODO: Investigate
    for i in arg_paths_list:
        # file_filters becomes "*.*" if you give them without any filter
        if i.startswith('http'):
            # debug("URL: " + str(i), not arg_debug)
            _list_of_urls.append(i)
        elif os.path.isdir(i):
            # debug("Folder: " + str(i), not arg_debug)
            if not os.path.abspath(i) in file_filters:
                file_filters[os.path.abspath(i)] = set()
            file_filters[os.path.abspath(i)].add("*")
        elif os.path.dirname(os.path.abspath(i)) and os.path.basename(os.path.abspath(i)):
            # debug(f"Split to k = '{os.path.dirname(os.path.abspath(i))}'   v = '{os.path.basename(os.path.abspath(i))}'", not arg_debug)
            if not os.path.dirname(os.path.abspath(i)) in file_filters:
                file_filters[os.path.dirname(os.path.abspath(i))] = set()
            file_filters[os.path.dirname(os.path.abspath(i))].add(os.path.basename(os.path.abspath(i)))

    # Remove invalid paths (file_filters that don't exists) ignore URLs
    file_filters_2 = {}
    for k, v in file_filters.items():
        if os.path.isdir(k):
            # debug(f"k: {k}, v: {v}", not arg_debug)
            file_filters_2[k] = v
        elif k.startswith('http'):
            continue
        elif not arg_supress_errors:
            warning_print("Could not find folder \"" + k + "\"")
    file_filters = file_filters_2

    # debug("File filters = " + str(file_filters), not arg_debug)

    # Filters done, now create a file list
    return_list = []
    for k, v in file_filters.items():
        return_list.extend(list_of_files(k, v, arg_recursive, arg_supress_errors, arg_debug))

    return_list = list(set(return_list))
    return_list.sort()
    return_list.extend(_list_of_urls)
    return return_list

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
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
    # debug("list_of_files() arg_folder = " + arg_folder + ", argfilters = " + str(filters) + "", not arg_debug)
    # Add all files matching the filter. OBS! No folders whatsoever
    for i in filters:
        full_path = os.path.join(arg_folder, i).replace('[', '?').replace(']', '?')
        # debug(full_path, not arg_debug)
        the_glob_list = glob.glob(full_path)

        # debug("list_of_files() Globbing " + os.path.join(arg_folder, i) + " = " + str(the_glob_list), not arg_debug)
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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def ensure_dir(arg_full_path: str):
    l_dirs = os.path.dirname(arg_full_path)
    if not os.path.exists(l_dirs):
        os.makedirs(l_dirs)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def filename_extension(arg_filename: str) -> str:
    ''' Returns the extention: "image.jpg" --> "jpg" '''
    l_end_at = arg_filename.find('?')

    l_filename = arg_filename if l_end_at == -1 else arg_filename[0:l_end_at]
    return os.path.splitext(l_filename)[1][1:]

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def temp_filename(arg_extension: str = "tmp") -> str:
    ''' Returns a temp filename '''
    l_random_string: str = "".join([random.choice("abcdefghjkmnpqrstuvxyz") for _ in range(5)]) # If we have bad luck and multiple scripts download at the same time
    return f"0000_{now_nice_format(arg_filename_safe=True)}_{l_random_string}_download.{arg_extension}"

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def sanitize_url(arg_url: str, arg_fail_if_not_good: bool = False) -> Optional[str]:
    """ Given a string from a user, return something that is safe to give to os.system() as URL """
    from urllib.parse import quote
    res = quote(arg_url, safe="%/:=&?~#+!$,;'@()*[]")
    if arg_fail_if_not_good and res != arg_url:
        error_print(f'URL is not OK! "{arg_url}" != "{res}"')
        return None
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def download_file(arg_url: str, #pylint: disable=too-many-arguments
                  arg_proxy_string_to_curl: str = "",
                  arg_origin: str = "",
                  arg_referer: str = "",
                  arg_local_filename: Union[str, None] = None,
                  arg_check_remote_filesize: bool = False,
                  arg_max_num_bytes: int = 0,
                  arg_rate_limit: str = "100M",
                  arg_dry_run: bool = False
                  ) -> str:
    """ Download a file with CURL and look like a normal web browser 
    Will look like:
    curl --speed-time 60 --speed-limit 500 --retry 20 -e "" -H "Origin: " -H "Sec-Fetch-Site: cross-site" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Dest: empty" -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"   -L   --limit-rate 100M -H "Accept-Language: en-US,en;q=0.9" -o "saved_as" --continue-at - <URL>
    
    """

    if not arg_local_filename:
        arg_local_filename = temp_filename()

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
    curl_command += f' --limit-rate {arg_rate_limit}' # https://everything.curl.dev/usingcurl/transfers/rate-limiting.html    The rate limit value can be given with a letter suffix using one of K, M and G for kilobytes, megabytes and gigabytes.
    curl_command += ' -H "Accept-Language: en-US,en;q=0.9"'
    curl_command += f' -o "{arg_local_filename}"'
    curl_command += ' --continue-at -' # https://curl.se/docs/manpage.html#-C
    curl_command += f' "{arg_url}"'
    timestamped_print("\n\n" + curl_command + "\n\n", arg_force_flush=True)
    if arg_dry_run:
        return arg_local_filename
    if 0 == os.system(curl_command):
        return arg_local_filename
    error_print(f'Curl failed to download "{arg_url}"')
    return "ERROR: CURL FAILED!" # TODO: return None?

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def now_nice_format(arg_filename_safe: bool = False, arg_utc: bool = False) -> str:
    """ Helper function for timestamped_line() """

    dt = datetime.datetime.now(datetime.UTC) if arg_utc else datetime.datetime.now()
    res = time.strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.timetuple(dt))
    if arg_filename_safe:
        return smart_filesystem_safe_path(res)
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def timestamped_line(arg_str: str = "") -> str:
    return f"[{now_nice_format()}] {arg_str}"

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def timestamped_print(arg_str: str = "", arg_file = sys.stdout, arg_force_flush: bool = False):
    print(timestamped_line(arg_str), file=arg_file, flush=arg_force_flush) # TODO: Rewrite this to use a real logger

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def _file_and_line_number(arg_num_function_away: int = 2) -> _inspect.Traceback:
    ''' Internal function. Used in log_print() '''
    callerframerecord = _inspect.stack()[arg_num_function_away]      # 0 represents this line
    frame = callerframerecord[0]                                     # 1 represents line at caller and so on
    info = _inspect.getframeinfo(frame)                              # info.filename, info.function, info.lineno
    return info

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def log_print(arg_string: str, #pylint: disable=too-many-arguments
              arg_actually_log: bool = True,
              arg_type: str = "DEBUG",
              arg_file = sys.stdout,
              arg_force_flush: bool = False,
              arg_num_function_away: int = 6
              ) -> None:
    ''' Used for outputing code trace while development TODO: replace this with a real logger code? '''
    if not arg_actually_log: return
    info = _file_and_line_number(arg_num_function_away) # TODO: This is very slow, rewrite this to use a real logger code?
    function_name = info.function
    if function_name == "<module>":
        function_name = os.path.basename(info.filename)
    else:
        function_name = f"{os.path.splitext(os.path.basename(info.filename))[0]}.{function_name}"
    log_line = f"{arg_type}: {function_name}:{info.lineno} --> {arg_string}"

    timestamped_print(arg_str=log_line, arg_file=arg_file, arg_force_flush=arg_force_flush)




G_DEFAULT_PREFIX: str = 'DEBUG: '
class _NullDebug:
    """
    Fallback used when peek is not installed, so callers don't need peek as a
    hard dependency. Matches the subset of the peek API this project uses. #
    """
    def __call__(self, *arg_exp: object, **arg_kwargs: object) -> object:
        if len(arg_exp) == 1:
            return arg_exp[0]
        return arg_exp

    def timer(self, arg_func_or_none: object = None, **arg_kwargs: object) -> object:
        if callable(arg_func_or_none): # used as a bare decorator: @debug.timer #
            return arg_func_or_none
        return self._timer_context() # used as @debug.timer(...) or with debug.timer(...): #

    @contextlib.contextmanager
    def _timer_context(self) -> Generator[None, None, None]:
        yield

if _G_PEEK_AVAILABLE:
    # debug is a preconfigured peek instance, not a wrapper function around peek().
    # peek always inspects its own direct caller frame to resolve the source
    # expression being printed (e.g. "l_val=42"), and it has no public hook to skip
    # an extra wrapper frame (unlike icecream's ic._format(frame, expr), which let
    # the old implementation pass the caller's frame explicitly). Wrapping peek()
    # in a debug(arg_exp) function would make every message resolve to "arg_exp=..."
    # instead of the real variable name, so debug is exposed as a forked peek
    # instance and called directly at each call site instead. #
    debug = _peek.peek.fork(
        prefix=G_DEFAULT_PREFIX,
        show_line_number=True,
        output=lambda arg_line: timestamped_print(arg_line, arg_file=sys.stderr),
    )
else:
    debug = _NullDebug()

# Usage:
#
# debug(l_val)
#   -> prints "[HH:MM:SS] DEBUG: #<line> in <func>() ==> l_val=<value>"
#   -> returns l_val unchanged, so it can be inserted inline: l_val = debug(compute())
#
# debug(l_val, enabled=False)
#   -> suppresses this single call's output (per-call override of arg_supress_output)
#
# debug(l_val, output=lambda arg_line: timestamped_print(arg_line, arg_out_handle=sys.stdout))
#   -> redirects this single call's output (per-call override of arg_out_handle)
#
# with debug.timer(show_line_number=True):
#     do_something_slow()
#   -> times the wrapped block and prints "enter" / "exit in <seconds> seconds"
#
# @debug.timer
# def some_func(...): ...
#   -> times every call to some_func, printing entry/exit and the return value

# Old code:

# _ExpType = TypeVar('_ExpType')
# @validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
# def debug(arg_exp: _ExpType, arg_supress_output: bool = False, arg_out_handle = sys.stderr) -> _ExpType:
    # ''' Modded version of pydbg. TODO: Maybe replace this with iceream? https://github.com/gruns/icecream    pip install icecream '''
    # if arg_supress_output:
        # return arg_exp

    # for frame in _inspect.stack():
        # if not frame.code_context:
            # break
        # line = frame.code_context[0]
        # start = line.find('debug(') + 1

        # if start:
            # exp_str = find_matching_brackets(line[start - 1:], arg_opening_brackets='(')
            # if exp_str:
                # exp_str = exp_str[6:-1] # Strip  the 'debug(' and the trailing ')'

            # # Remove the arguments to this function (if there are any)
            # all_parts = exp_str.split(',')
            # if 1 == len(all_parts):
                # exp_res = all_parts[0]
            # else:
                # if all_parts:
                    # exp_res = ""
                    # for part in all_parts:
                        # exp_res += part + ','
                        # if find_matching_brackets(exp_res[:-1], arg_opening_brackets='('):
                            # exp_res = exp_res[:-1]
                            # break

            # exp_res = exp_res.strip()

            # # import ast
            # # a = ast.parse(exp_res)
            # # b = ast.dump(a)
            # # print(b, file=arg_out_handle)

            # timestamped_print(
                # f"DEBUG: {frame.filename}:{frame.lineno}: {exp_res} --> {arg_exp!r}",
                # arg_file=arg_out_handle,
            # )
            # break

    # return arg_exp

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def console_color(arg_string: str, arg_color: str = "OKGREEN") -> str:
    ''' Returns a new string with console marker at the start and at the end '''
    
    # TODO: These are in colorize.py?
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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def debug_print(arg_string: str, arg_num_function_away: int = 3):
    log_print(arg_type="DEBUG", arg_string=console_color(arg_string, arg_color="WHITE"), arg_num_function_away=arg_num_function_away+6)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def info_print(arg_string: str, arg_num_function_away: int = 3):
    log_print(arg_type="INFO", arg_string=console_color(arg_string, arg_color="WHITE"), arg_num_function_away=arg_num_function_away+6)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def warning_print(arg_string: str, arg_num_function_away: int = 3):
    log_print(arg_type="WARNING", arg_string=console_color(arg_string, arg_color="WARNING"), arg_num_function_away=arg_num_function_away+6)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def error_print(arg_string: str, arg_num_function_away: int = 3):
    log_print(arg_type="ERROR", arg_string=console_color(arg_string, arg_color="FAIL"), arg_num_function_away=arg_num_function_away+6)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def success_print(arg_string: str, arg_num_function_away: int = 3):
    log_print(arg_type="SUCCESS", arg_string=console_color(arg_string, arg_color="HEADER"), arg_num_function_away=arg_num_function_away+6)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_get_key_from_value(arg_dict: dict, arg_value):
    for k, v in arg_dict.items():
        if v == arg_value:
            return k
    return None

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_sort(arg_dict: dict, arg_sort_by_value: bool = False, arg_desc: bool = False) -> dict:
    ''' Returns a new sorted dictionary sorted on key (use arg_sort_by_value to sort on value) '''
    res = {}

    l_sort_function = natsort.natsorted if _G_USE_NATSORT else sorted
    if arg_sort_by_value:
        res = dict(l_sort_function(arg_dict.items(), key=lambda item: item[1])) # Sort by value ( lower -> higher )
    else:
        l_list = l_sort_function(arg_dict.items())

        for _t in l_list:
            res[_t[0]] = _t[1]

    if arg_desc:
        res = {k: res[k] for k in reversed(res)} # Just reverse the dict

    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_move_to_start(arg_dict: dict, arg_key) -> dict:
    ''' Returns a new dict with the given key as the first key '''
    res = {}
    res[arg_key] = arg_dict.pop(arg_key)
    for k, v in arg_dict.items():
        res[k] = v
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_to_json_string_pretty(arg_dict: Union[dict, list], arg_as_html: bool = False) -> str:
    res = json.dumps(arg_dict, ensure_ascii=False, indent=4, default=str)
    if arg_as_html:
        res = res.replace("\n", "<br/>\n")
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_dump_to_json_file(arg_dict: Union[dict, list], arg_filename: str) -> bool:
    data = dict_to_json_string_pretty(arg_dict)
    with io.open(arg_filename, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    return True

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_load_json_file(arg_filename_or_url: str) -> Union[Dict, None]:
    ''' Takes a filename or URL and parse it as a dict '''

    file_content = text_read_whole_file(arg_filename_or_url)
    if not file_content:
        return None
    return json.loads(file_content)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_list_to_massive_dict(arg_list: List[Any], arg_key) -> Union[Dict, None]:
    ''' Converts a list of dicts --> one massive dict '''
    res = {}
    for item in arg_list:
        if arg_key not in item:
            error_print(f'Could not find "{arg_key}" as key in arg_dict')
            return None

        res[str(item[arg_key])] = item # There is a "bug" in Python that JSON keys is always string but Python can have ints as keys: https://stackoverflow.com/a/1451857
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_sub(arg_original: dict, arg_updater: dict) -> dict:
    ''' Returns a new dict with the keys that are in arg_updater removed from arg_original '''
    res = {}
    list_of_items_left = list(set(arg_original) - set(arg_updater))
    for key in list_of_items_left:
        res[key] = arg_original[key]

    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def dict_intersect(arg_left: dict, arg_right: dict) -> dict:
    return {key: arg_left[key] for key in arg_left if key in arg_right}

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def smart_filesystem_safe_path(arg_file_path: Union[str, pathlib.Path],
                               arg_allow_swedish_chars: bool = False,
                               arg_fix_season_and_episodes: bool = True,
                               arg_replacement_char: str = '.') -> str:
    ''' Make a long and weird string into something that the OS likes more to handle '''
    res = str(arg_file_path)
    res = res.replace('/', os.path.sep)
    if len(res) < 2:
        warning_print(f"Filename is very short: {res}")

    l_dir = ''
    if len(res) > 3 and  res[1] == ':' and res[2] == '\\': # Full path: C:\dir\file.txt
            res = res[0].upper() + res[1:] # I like when the drive letter is uppercase
            l_dir = os.path.dirname(res)
            res = os.path.basename(res)

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
    # res = res.replace("_", arg_replacement_char) # Keep underscore?
    if os.path.sep != '/':
        res = res.replace("/", arg_replacement_char) # This will be strange on Linux paths
    res = res.replace("?", arg_replacement_char)
    # res = res.replace("-", arg_replacement_char)
    res = res.replace("#", arg_replacement_char)
    res = res.replace("*", arg_replacement_char)
    res = res.replace(" ", arg_replacement_char)
    res = res.replace("｜", "") # special char that yt-dlp generate
    res = res.replace("’", "") # special char that yt-dlp generate
    res = res.replace("|", arg_replacement_char) # normal pipe sign
    res = res.replace("：", "") # special char that yt-dlp generate
    res = res.replace("？", "") # special char that yt-dlp generate
    res = res.replace("⧸", "") # special char that yt-dlp generate
    res = res.replace("＂", "") # special char that yt-dlp generate
    res = res.replace("—", "") # special char that yt-dlp generate
    res = res.replace('"', "")
    res = res.replace("'", "")
    res = res.replace("[", arg_replacement_char)
    res = res.replace("]", arg_replacement_char)
    res = res.replace("{", arg_replacement_char)
    res = res.replace("}", arg_replacement_char)
    res = res.replace("\t", "")
    res = res.replace(".–", arg_replacement_char)
    res = res.replace("–.", arg_replacement_char)

    if arg_fix_season_and_episodes:
        res = re.sub(r's[aä]song.(\d\d?).avsnitt.(\d\d?)', 'S0\\1E0\\2', res, flags=re.IGNORECASE) # Swedish naming: Säsong-1-avsnitt-1 --> S01E01
        res = re.sub(fr'([{arg_replacement_char}])S0(\d\d)E(\d\d?\d?)', '\\1S\\2E\\3', res, flags=re.IGNORECASE) # Fix Season numbers 'S011' --> 'S11'
        res = re.sub(fr'([{arg_replacement_char}])S(\d\d)E0(\d\d)', '\\1S\\2E\\3', res, flags=re.IGNORECASE) # Fix episode numbers 'E012' --> 'E12'

    res = os.path.join(l_dir, res)
    while res != res.replace('__', arg_replacement_char):
        res = res.replace('__', arg_replacement_char)
    while res != res.replace('  ', arg_replacement_char):
        res = res.replace('  ', arg_replacement_char)
    while res != res.replace('--', arg_replacement_char):
        res = res.replace('--', arg_replacement_char)
    while res != res.replace('..', arg_replacement_char):
        res = res.replace('..', arg_replacement_char)

    res = res.replace("con.", "con_") # CON is a reserved word
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def regexp_findall_quick_fix(arg_needle: str,
                             arg_haystack: str,
                             arg_default_return_if_not_found: Union[List[str], str, None] = None
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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def to_float(arg_in: Union[str, List[str], int, List[int]]) -> float:
    ''' Convert to float in a smart way. '''
    res: float = 0
    if isinstance(arg_in, list):
        for i in arg_in:
            res += to_float(i)
        return res
    arg_in = str(arg_in)
    arg_in = arg_in.replace(" ", "") # Swedish thousand separator is ' ' (space)
    arg_in = arg_in.replace(",", ".") # Swedish  decimal separator is , not . 
    res = float(arg_in)
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def find_matching_brackets(arg_haystack: str, arg_opening_brackets: str = '{', arg_start_with_counter: int = 0):
    closing_brackets_dict = {'[': ']', '{': '}', '(': ')', '<': '>'}
    closing_bracket = closing_brackets_dict[arg_opening_brackets]

    for i in range(0, len(arg_haystack)):
        if arg_haystack[i] == arg_opening_brackets:
            arg_start_with_counter += 1
        elif arg_haystack[i] == closing_bracket:
            arg_start_with_counter -= 1
            if 0 == arg_start_with_counter:
                return arg_haystack[0:i+1]
    # timestamped_print("ERROR! find_matching_brackets() failed to find anything")
    return ""

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def get_part_of_json(arg_haystack: str, arg_start_marker_regexp: str, arg_opening_brackets: str = '{', arg_start_with_counter: int = 0) -> str:
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
    return ""

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def concat_files(arg_folder: str, arg_list_of_files: Union[List[str], str], arg_dest_file: str):
    if isinstance(arg_list_of_files, str):
        arg_list_of_files = list_from_str(arg_list_of_files)

    with open(arg_dest_file, "wb") as f:
        for file in arg_list_of_files:
            with open(os.path.join(arg_folder, file), "rb") as f2:
                f.write(f2.read())
    return True

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def text_write_whole_file(arg_filename: str, arg_text: str) -> bool:
    ''' Opens a text file (as UTF-8 with newline='\\n') and write the argument text to that file and then close the file  '''
    with io.open(arg_filename, mode="w", encoding="utf-8", newline="\n") as fp:
        fp.write(arg_text)
    return True

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def text_read_whole_file(arg_filename_or_url: Union[str, pathlib.Path]) -> Optional[str]:
    arg_filename_or_url = str(arg_filename_or_url) # This will handle pathlib.Path
    if arg_filename_or_url.lower().startswith("http"):
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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def math_nthroot(x: Union[int, float, decimal.Decimal], n: Union[int, float, decimal.Decimal]) -> decimal.Decimal:
    ''' Returns the n:th root of x. Example: x=729, n=3 --> 9 '''
    return decimal.Decimal(pow(decimal.Decimal(x), decimal.Decimal(1)/decimal.Decimal(n)))

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def list_from_str(arg_str: Union[str, List, Set, Tuple, None],
                  arg_re_splitter: str = ' |,|;|:|[+]|[-]|[|]|[\n]|[\r]'
                  ) -> List[str]:
    ''' Take a str and try to convert into a list of str in a smart way '''

    if arg_str is None:
        return []
    if isinstance(arg_str, list):
        res = arg_str
    elif isinstance(arg_str, (set, tuple)):
        res = list(arg_str)
    elif isinstance(arg_str, str):
        res = re.split(arg_re_splitter, arg_str)

    return [x for x in res if x]

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def table_from_html(arg_url: str) -> List[List[str]]:
    from bs4 import BeautifulSoup # Imported here since it's an external lib
    # TODO: Replace with justhtml 

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

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def html_unicode_to_entities(arg_text: str) -> str:
    '''Converts unicode to HTML entities.  For example '&' becomes '&amp;' TODO: This seems broken? Deprecate it'''
    import namedentities # type: ignore
    return namedentities.hex_entities(arg_text)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def file_delete(arg_filename: Union[str, pathlib.Path]) -> bool:
    ''' If the file exists, then delete it. If it does NOT exist, just return True

        Returns True if at the end of this function there is no file name arg_filename.
        Will return True even if there never was a file named that.
    '''
    arg_filename = str(arg_filename) # This will handle pathlib.Path
    if os.path.exists(arg_filename):
        os.remove(arg_filename)
    return not os.path.exists(arg_filename)

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
def zapper(arg_string: str, arg_character_to_zap: str = ' ') -> str:
    ''' Removed multiple chars in a row and only saves 1 '''
    res = arg_string
    while (res.replace(arg_character_to_zap + arg_character_to_zap, arg_character_to_zap) != res):
        res = res.replace(arg_character_to_zap + arg_character_to_zap, arg_character_to_zap)
    return res

@validate_call(config={"arbitrary_types_allowed": True, "strict": True, "validate_return": True})
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
