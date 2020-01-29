import os, sys
import csv
import hashlib
import errno

from numbers import Number
from typing import Tuple

import six

def import_class(cl):
    d = cl.rfind(".")
    classname = cl[d+1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [classname])
    return getattr(m, classname)()

def flip(size: Tuple[Number, Number]) -> Tuple[Number, Number]:
    return (size[1], size[0])

def is_notebook():
    try:
        from IPython import get_ipython
        if get_ipython() is None:
            raise ImportError("console")
        if 'IPKernelApp' not in get_ipython().config:  # pragma: no cover
            raise ImportError("console")
        if 'VSCODE_PID' in os.environ:  # pragma: no cover
            raise ImportError("vscode")
    except ImportError:
        return False
    else:
        return True

if is_notebook():
    try:
        from ipywidgets import IntProgress
        from tqdm._tqdm_notebook import tqdm_notebook as tqdm
    except ImportError:
        from tqdm import tqdm
else:
    from tqdm import tqdm

class Progress(tqdm):

    def update_absolute(self, current, total = None):
        if total is not None:
            self.total = total
        self.update(current - self.n)  # will also set self.n = b * bsize
        
    def update_relative(self, n, total = None):
        if total is not None:
            self.total = total
        self.update(n)  # will also set self.n = b * bsize

def extract_files(archive, destination, callback = None):
    from zipfile import ZipFile
    
    with ZipFile(file=archive) as zip_file:
        # Loop over each file
        total=len(zip_file.namelist())
        for file in zip_file.namelist():

            # Extract each file to another directory
            # If you want to extract to current working directory, don't specify path
            zip_file.extract(member=file, path=destination)
            if callback:
                callback(1, total)

def read_properties(filename, delimiter='='):
    ''' Reads a given properties file with each line of the format key=value.
        Returns a dictionary containing the pairs.
            filename -- the name of the file to be read
    '''
    if not os.path.exists(filename):
        return {}
    open_kwargs = {'mode': 'r', 'newline': ''} if six.PY3 else {'mode': 'rb'}
    with open(filename, **open_kwargs) as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter, escapechar='\\',
                            quoting=csv.QUOTE_NONE)
        return {row[0]: row[1] for row in reader}

def write_properties(filename, dictionary, delimiter='='):
    ''' Writes the provided dictionary in key sorted order to a properties
        file with each line in the format: key<delimiter>value
            filename -- the name of the file to be written
            dictionary -- a dictionary containing the key/value pairs.
    '''
    open_kwargs = {'mode': 'w', 'newline': ''} if six.PY3 else {'mode': 'wb'}
    with open(filename, **open_kwargs) as csvfile:
        writer = csv.writer(csvfile, delimiter=delimiter, escapechar='\\',
                            quoting=csv.QUOTE_NONE)
        writer.writerows(sorted(dictionary.items()))

def file_hash(filename):

    # BUF_SIZE is totally arbitrary, change for your app!
    bufsize = 65536  # lets read stuff in 64kb chunks!

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    with open(filename, 'rb') as f:
        while True:
            data = f.read(bufsize)
            if not data:
                break
            md5.update(data)
            sha1.update(data)

    return md5.hexdigest(), sha1.hexdigest()


def mkpath(path):
    try:
        os.makedirs(path)
    except OSError as exc: 
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def which(program):

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def normalize(path, root=None):
    if os.path.isabs(path):
        return path
    if not root:
        root = os.getcwd()
    return os.path.normpath(os.path.join(root, path))

