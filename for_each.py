#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run a OS command on many files. Can also show progress in external file.
"""

__version__ = 230313002152
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

use_natsort = True
try: # It will function without this sorting
    import natsort
except ImportError:
    use_natsort = False
    print("WARNING: Module natsort not installed, this module is not required but strongly recommended. pip install natsort")

import os
import time
import subprocess
import harding_utils as hu

def do_exec(command: str, arg_file: str, arg_index: int, number_of_files: int, started: float, print_progress_to_file: bool = None):
    if print_progress_to_file:
        percent_done = arg_index / number_of_files
        time_elapsed = time.time() - started
        estimated_total_time = time_elapsed / percent_done
        with open(print_progress_to_file, "w", encoding='utf8', newline='\n') as fdesc:
            fdesc.write(hu.timestamped_line(f"File {arg_index} / {number_of_files} ({percent_done * 100:.3f}%) estimated {(estimated_total_time - time_elapsed + 1)/60:0.0f}m left. Have been running for {time_elapsed:0.0f} seconds. File: \"{arg_file}\""))

    command = command.replace("%file", arg_file)
    os.system(command)

if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description=f"python {sys.argv[0]} \"string to be system() by Python\" file_1 [file_2 ... file_n] Example: python {sys.argv[0]} \"echo I will work on the file: \\\"%file\\\"\" *.py")
    parser.add_argument("-s", "--subfolders", action="store_true", dest="check_subfolders", help="Look in subfolders. Default: False", default=False)
    parser.add_argument("-f", "--file", action="store_true", dest="file_list", help="The file given contains filenames to work on. Default: False", default=False)
    parser.add_argument("-p", "--progress", dest="progress_file", help="Write current progress to this file before every file. This will cause many disk writes.", default=None)
    parser.add_argument("-b", "--basename", action="store_true", dest="only_basename", help="Use only the basename of the file. Default: False", default=False)
    parser.add_argument("command", help="The OS command to run. Use the string %%file for the filename replacement")
    parser.add_argument("file", nargs="+", help="The file(s) to work on. Use - for stdin")
    args = parser.parse_args()

    files = []
    if "-" == args.file[0]:
        files.append("-")
    else:
        files = hu.adv_glob(args.file, args.check_subfolders)
        
    start_time = time.time()

    if use_natsort and not args.file_list:
        files = natsort.natsorted(files)
    index = 0
    for file in files:
        index += 1
        if args.only_basename:
            file = os.path.basename(file)
        if args.file_list or "-" == file:
            if "-" == file: # stdin
                lines = sys.stdin.readlines()
            else:
                with open(file, 'r', encoding='utf8', newline='\n') as f:
                    lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                do_exec(args.command.strip(), line, index, len(files), start_time, args.progress_file)
        else:
            do_exec(args.command.strip(), file, index, len(files), start_time, args.progress_file)
    #os.system("pause")
    