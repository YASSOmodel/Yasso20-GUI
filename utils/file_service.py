import glob
import sys
import os

from pyface.api import FileDialog, OK as Pyface_OK

from traitsui.message import error


def open_file():
    """
    Replaces the old traitsui.file_dialog.open_file calls with the more robust PyFace.
    """

    wildcard = '*.txt'
    dialog = FileDialog(title='Select the file to open', action='open', wildcard=wildcard)
    if dialog.open() == Pyface_OK:
        return dialog.path
    return ''


def save_file():
    wildcard = '*.txt'
    dialog = FileDialog(title='Select the file to save as...', action='save as', wildcard=wildcard)
    if dialog.open() == Pyface_OK:
        return dialog.path
    return ''


def get_parameter_files():
    """
    Extracts the available parameter files from the param sub folder
    """

    fn = os.path.split(sys.executable)
    if fn[1].lower().startswith('python'):
        exedir = os.path.abspath(os.path.split(sys.argv[0])[0])
    else:
        exedir = fn[0]
    join = os.path.join
    pdir = join(exedir, 'param')
    if os.path.exists(pdir):
        p_files = glob.glob(join(pdir, '*.dat'))
        pset = []
        for f in p_files:
            p = os.path.basename(f).split('.')[0]
            pset.append(p)

        return sorted(pset)
    else:
        print(f"Not finding the parameter directory {pdir}")
        errmsg = """
            The model parameter directory param is missing.
            It must be in the same directory as the program 
            executable
        """
        error(errmsg, title='Error starting the program', buttons=['OK'])
        sys.exit(-1)
