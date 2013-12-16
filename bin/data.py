#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from codecs import open
from itertools import imap
from operator import itemgetter
import os
import shutil
import sys
from time import time

from utils import create_dir
from utils import is_osx
from utils import move_file


BACKUP_THRESHOLD = 24 * 60 * 60


def load(config):
    xdg_aj_home = os.path.join(
            os.path.expanduser('~'),
            '.local',
            'share',
            'autojump')

    if is_osx() and os.path.exists(xdg_aj_home):
        migrate_osx_xdg_data(config)

    if os.path.exists(config['data_path']):
        try:
            with open(config['data_path'], 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except (IOError, EOFError):
            return load_backup(config)

        # example: u'10.0\t/home/user\n' -> ['10.0', u'/home/user']
        parse = lambda x: x.strip().split('\t')

        # example: ['10.0', u'/home/user'] -> (u'/home/user', 10.0)
        convert = lambda x: (x[1], float(x[0]))

        return dict(imap(convert, imap(parse, lines)))
    return {}


def load_backup(config):
    if os.path.exists(config['backup_path']):
        move_file(config['backup_path'], config['data_path'])
        return load(config)
    return {}


def migrate_osx_xdg_data(config):
    """
    Older versions incorrectly used Linux XDG_DATA_HOME paths on OS X. This
    migrates autojump files from ~/.local/share/autojump to ~/Library/autojump
    """
    assert is_osx(), "Expecting OSX."

    xdg_data_home = os.path.join(os.path.expanduser('~'), '.local', 'share')
    xdg_aj_home = os.path.join(xdg_data_home, 'autojump')
    data_path = os.path.join(xdg_aj_home, 'autojump.txt'),
    backup_path = os.path.join(xdg_aj_home, 'autojump.txt.bak'),

    if os.path.exists(data_path):
        move_file(data_path, config['data_path'])
    if os.path.exists(backup_path):
        move_file(backup_path, config['backup_path'])

    # cleanup
    shutil.rmtree(xdg_aj_home)
    if len(os.listdir(xdg_data_home)) == 0:
        shutil.rmtree(xdg_data_home)


def save(config, data):
    """Save data and create backup, creating a new data file if necessary."""
    create_dir(os.path.dirname(config['data_path']))

    # atomically save by writing to temporary file and moving to destination
    try:
        # write to temp file
        with open(config['tmp_path'], 'w', encoding='utf-8', errors='replace') as f:
            for path, weight in sorted(
                    data.iteritems(),
                    key=itemgetter(1),
                    reverse=True):
                f.write((unicode("%s\t%s\n" % (weight, path)).encode('utf-8')))

            f.flush()
            os.fsync(f)
    except IOError as ex:
        print("Error saving autojump data (disk full?)" % ex, file=sys.stderr)
        sys.exit(1)

    # create backup file if it doesn't exist or is older than BACKUP_THRESHOLD
    if not os.path.exists(config['backup_path']) or \
            (time() - os.path.getmtime(config['backup_path']) > BACKUP_THRESHOLD):
        move_file(config['data_path'], config['backup_path'])

    # move temp_file -> autojump.txt
    move_file(temp_file.name, config['data_path'])
