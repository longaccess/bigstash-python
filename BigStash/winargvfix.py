import os
import sys
from ctypes import (windll, POINTER, byref, c_int,
                    create_unicode_buffer, c_wchar_p)


def fix_env_on_windows():
    def getEnvironmentVariable(name):
        name = unicode(name)  # make sure string argument is unicode
        n = windll.kernel32.GetEnvironmentVariableW(name, None, 0)
        if n == 0:
            return None
        buf = create_unicode_buffer(u'\0'*n)
        windll.kernel32.GetEnvironmentVariableW(name, buf, n)
        return buf.value
    for k in os.environ.keys():
        os.environ[k] = getEnvironmentVariable(k).encode('utf-8')


def fix_argv_on_windows():
    # This works around <http://bugs.python.org/issue2128>.
    GetCommandLineW = windll.kernel32.GetCommandLineW
    GetCommandLineW.restype = c_wchar_p
    CommandLineToArgvW = windll.shell32.CommandLineToArgvW
    CommandLineToArgvW.restype = POINTER(c_wchar_p)

    argc = c_int(0)
    argv_unicode = CommandLineToArgvW(GetCommandLineW(), byref(argc))

    argv = [argv_unicode[i].encode('utf-8') for i in range(0, argc.value)]

    if not hasattr(sys, 'frozen'):
        # If this is an executable produced by py2exe or bbfreeze, then it will
        # have been invoked directly. Otherwise, unicode_argv[0] is the Python
        # interpreter, so skip that.
        argv = argv[1:]

        # Also skip option arguments to the Python interpreter.
        while len(argv) > 0:
            arg = argv[0]
            if not arg.startswith("-") or arg == "-":
                break
            argv = argv[1:]
            if arg == '-m':
                # sys.argv[0] should really be the absolute path of the module
                # source, but never mind
                break
            if arg == '-c':
                argv[0] = '-c'
                break
    return argv
