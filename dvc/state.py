import os
import json
from checksumdir import dirhash

from dvc.system import System
from dvc.output import Output
from dvc.utils import file_md5
from dvc.exceptions import DvcException


class StateEntry(object):
    PARAM_MTIME = 'mtime'
    PARAM_MD5 = 'md5'

    def __init__(self, md5, mtime):
        self.mtime = mtime
        self.md5 = md5

    def update(self, md5, mtime):
        self.mtime = mtime
        self.md5 = md5

    @staticmethod
    def loadd(d):
        mtime = d[StateEntry.PARAM_MTIME]
        md5 = d[StateEntry.PARAM_MD5]
        return StateEntry(md5, mtime)

    def dumpd(self):
        return {
            self.PARAM_MD5: self.md5,
            self.PARAM_MTIME: self.mtime,
        }


class StateDuplicateError(DvcException):
    pass


class State(object):
    STATE_FILE = 'state'

    def __init__(self, root_dir, dvc_dir):
        self.root_dir = root_dir
        self.dvc_dir = dvc_dir
        self.state_file = os.path.join(dvc_dir, self.STATE_FILE)
        self._db = {}

    @staticmethod
    def init(root_dir, dvc_dir):
        return State(root_dir, dvc_dir)

    def compute_md5(self, path):
        if os.path.isdir(path):
            return dirhash(path, hashfunc='md5') + Output.MD5_DIR_SUFFIX
        else:
            return file_md5(path)[0]

    def changed(self, path, md5):
        return self.update(path) != md5

    def load(self):
        with open(self.state_file, 'r') as fd:
            self._db = json.load(fd)

    def dump(self):
        with open(self.state_file, 'w+') as fd:
            json.dump(self._db, fd)

    def update(self, path, dump=True):
        mtime = os.path.getmtime(path)
        inode = System.inode(path)

        md5 = self._get(inode, mtime)
        if md5:
            return md5

        md5 = self.compute_md5(path)
        state = StateEntry(md5, mtime)
        d = state.dumpd()
        self._db[inode] = d

        if dump:
            self.dump()

        return md5

    def _get(self, inode, mtime):
        d = self._db.get(inode, None)
        if not d:
            return None

        state = StateEntry.loadd(d)
        if mtime == state.mtime:
            return state.md5

        return None

    def get(self, path):
        mtime = os.path.getmtime(path)
        inode = System.inode(path)

        return self._get(inode, mtime)
