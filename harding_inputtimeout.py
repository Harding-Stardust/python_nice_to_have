#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is a modified version of inputimeout (https://pypi.org/project/inputimeout)
With the following mods:
docstrings
type hints
default values
each keypress adds the timeout so we won't interupt the user when he/she is typing
"""

__version__ = 230312150647
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["inputimeout: https://pypi.org/project/inputimeout"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

import sys

DEFAULT_TIMEOUT_IN_SECONDS: float = 30.0
DEFAULT_RETURN_VALUE: str = 'Timeout occured'
DEFAULT_ERROR_MESSAGE: str = " No user input, defaulted to "
INTERVAL: float = 0.05

CR = '\r'
LF = '\n'
CTRL_Z = '\x1A'
CRLF = CR + LF

def _posix_inputimeout(arg_prompt: str = '', arg_timeout: float = DEFAULT_TIMEOUT_IN_SECONDS, arg_default_return_value: str = DEFAULT_RETURN_VALUE) -> str:
    ''' POSIX implementation using select() '''
    print(arg_prompt, file=sys.stdout, flush=True, end='')
    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ)
    events = sel.select(arg_timeout)

    if events:
        key, _ = events[0]
        return key.fileobj.readline().rstrip(LF)

    termios.tcflush(sys.stdin, termios.TCIFLUSH)
    print(DEFAULT_ERROR_MESSAGE + f"'{arg_default_return_value}'", file=sys.stdout, flush=True)
    return arg_default_return_value

def _win_inputimeout(arg_prompt: str ='', arg_timeout:float = DEFAULT_TIMEOUT_IN_SECONDS, arg_default_return_value: str = DEFAULT_RETURN_VALUE) -> str:
    ''' Windows implementation using getwche() '''
    print(arg_prompt, file=sys.stdout, flush=True, end='')
    begin: float = time.monotonic()
    end: float = begin + arg_timeout
    line: str = ''

    while time.monotonic() < end:
        if msvcrt.kbhit():
            c = msvcrt.getwche()
            end = time.monotonic() + arg_timeout # Each key press adds to the timeout so we won't interupt the user if he/she is typing. OBS! This will make the POSIX and Windows version work differently!
            if c in (CR, LF, CTRL_Z):
                print(CRLF, file=sys.stdout, flush=True)
                return line
            if c == '\003': # Ctrl + C
                raise KeyboardInterrupt
            if c == '\b': # Backspace
                line = line[:-1]
                cover = ' ' * len(arg_prompt + line + ' ')
                print(''.join([CR, cover, CR, arg_prompt, line]), file=sys.stdout, flush=True, end='')
            else:
                line += c
                # return line # TODO: test with only 1 keypress as choice.com
        time.sleep(INTERVAL)

    print(DEFAULT_ERROR_MESSAGE + f"'{arg_default_return_value}'", file=sys.stdout, flush=True)
    return arg_default_return_value

if "__main__" == __name__:
    import os
    my_module_name: str = os.path.basename(__file__)[:-3]
    print("This module is not usable from the console, use it like this:")
    print()
    print(f"import {my_module_name}")
    print(f"username = {my_module_name}.inputimeout(arg_prompt='You have 10 seconds to enter your name >> ', arg_timeout=10.0, arg_default_return_value='You seems to have forgotten your name')")
    print("print(f'Your name is: {username}')")
    
try:
    import msvcrt
except ImportError:
    import selectors
    import termios
    inputimeout = _posix_inputimeout
else:
    import time
    inputimeout = _win_inputimeout
    
