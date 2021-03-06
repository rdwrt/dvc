from __future__ import print_function

import os
import sys
import argparse
from multiprocessing import cpu_count

from dvc.command.init import CmdInit
from dvc.command.remove import CmdRemove
from dvc.command.run import CmdRun
from dvc.command.repro import CmdRepro
from dvc.command.data_sync import CmdDataPush, CmdDataPull, CmdDataFetch
from dvc.command.status import CmdDataStatus
from dvc.command.gc import CmdGC
from dvc.command.add import CmdAdd
from dvc.command.config import CmdConfig
from dvc.command.checkout import CmdCheckout
from dvc.stage import Stage
from dvc import VERSION


def parse_args(argv=None):
    # Common args
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
                        '-q',
                        '--quiet',
                        action='store_true',
                        default=False,
                        help='Be quiet.')
    parent_parser.add_argument(
                        '-v',
                        '--verbose',
                        action='store_true',
                        default=False,
                        help='Be verbose.')

    # Main parser
    desc = 'Data Version Control'
    parser = argparse.ArgumentParser(
                        prog='dvc',
                        description=desc,
                        parents=[parent_parser],
                        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-V',
                        '--version',
                        action='version',
                        version='%(prog)s ' + VERSION,
                        help='Show program\'s version')

    # Sub commands
    subparsers = parser.add_subparsers(
                        dest='cmd',
                        help='Use dvc CMD --help for command-specific help')

    # NOTE: Workaround for bug in Python 3
    if sys.version_info[0] == 3:
        subparsers.required = True
        subparsers.dest = 'cmd'

    # Init
    init_parser = subparsers.add_parser(
                        'init',
                        parents=[parent_parser],
                        help='Initialize dvc over a directory (should already be a git dir)')
    init_parser.set_defaults(func=CmdInit)

    # Add
    import_parser = subparsers.add_parser(
                        'add',
                        parents=[parent_parser],
                        help='Add files/directories to dvc')
    import_parser.add_argument(
                        'targets',
                        nargs='+',
                        help='Input files/directories')
    import_parser.set_defaults(func=CmdAdd)

    # Checkout
    checkout_parser = subparsers.add_parser(
                        'checkout',
                        parents=[parent_parser],
                        help='Checkout data files from cache')
    checkout_parser.set_defaults(func=CmdCheckout)

    # Run
    run_parser = subparsers.add_parser(
                        'run',
                        parents=[parent_parser],
                        help='Generate a stage file from a given command and execute the command')
    run_parser.add_argument('-d',
                        '--deps',
                        action='append',
                        default=[],
                        help='Declare dependencies for reproducible cmd.')
    run_parser.add_argument('-o',
                        '--outs',
                        action='append',
                        default=[],
                        help='Declare output data file or data directory.')
    run_parser.add_argument('-O',
                        '--outs-no-cache',
                        action='append',
                        default=[],
                        help='Declare output regular file or directory (sync to Git, not DVC cache).')
    run_parser.add_argument('-f',
                        '--file',
                        help='Specify name of the state file')
    run_parser.add_argument('-c',
                        '--cwd',
                        default=os.path.curdir,
                        help='Directory to run your command and place state file in')
    run_parser.add_argument(
                        '--no-exec',
                        action='store_true',
                        default=False,
                        help="Only create stage file without actually running it")
    run_parser.add_argument(
                        'command',
                        nargs=argparse.REMAINDER,
                        help='Command or command file to execute')
    run_parser.set_defaults(func=CmdRun)

    # Parent parser used in pull/push/status
    parent_cache_parser = argparse.ArgumentParser(
                        add_help=False,
                        parents=[parent_parser])
    parent_cache_parser.add_argument('-j',
                        '--jobs',
                        type=int,
                        default=8*cpu_count(),
                        help='Number of jobs to run simultaneously.')
    parent_cache_parser.add_argument(
                        'targets',
                        nargs='*',
                        default=None,
                        help='DVC files.')

    # Pull
    pull_parser = subparsers.add_parser(
                        'pull',
                        parents=[parent_cache_parser],
                        help='Pull data files from the cloud')
    pull_parser.set_defaults(func=CmdDataPull)

    # Push
    push_parser = subparsers.add_parser(
                        'push',
                        parents=[parent_cache_parser],
                        help='Push data files to the cloud')
    push_parser.set_defaults(func=CmdDataPush)

    # Fetch
    fetch_parser = subparsers.add_parser(
                        'fetch',
                        parents=[parent_cache_parser],
                        help='Fetch data files from the cloud')
    fetch_parser.set_defaults(func=CmdDataFetch)

    # Status
    status_parser = subparsers.add_parser(
                        'status',
                        parents=[parent_cache_parser],
                        help='Show the project status')
    status_parser.add_argument('-c',
                        '--cloud',
                        action='store_true',
                        default=False,
                        help='Show status of a local cache compared to a cloud')
    status_parser.set_defaults(func=CmdDataStatus)

    # Repro
    repro_parser = subparsers.add_parser(
                        'repro',
                        parents=[parent_parser],
                        help='Reproduce DVC file. Default file name - \'Dvcfile\'')
    repro_parser.add_argument(
                        'targets',
                        nargs='*',
                        default=[Stage.STAGE_FILE],
                        help='DVC file to reproduce.')
    repro_parser.add_argument('-f',
                        '--force',
                        action='store_true',
                        default=False,
                        help='Reproduce even if dependencies were not changed.')
    repro_parser.add_argument('-s',
                        '--single-item',
                        action='store_true',
                        default=False,
                        help='Reproduce only single data item without recursive dependencies check.')
    repro_parser.set_defaults(func=CmdRepro)

    # Remove
    remove_parser = subparsers.add_parser(
                        'remove',
                        parents=[parent_parser],
                        help='Remove outputs of DVC file.')
    remove_parser.add_argument('targets',
                        nargs='+',
                        help='DVC files.')
    remove_parser.set_defaults(func=CmdRemove)

    # Garbage collector
    gc_parser = subparsers.add_parser(
                        'gc',
                        parents=[parent_parser],
                        help='Collect garbage')
    gc_parser.set_defaults(func=CmdGC)

    # Config
    config_parser = subparsers.add_parser(
                        'config',
                        parents=[parent_parser],
                        help='Get or set config options')
    config_parser.add_argument('-u',
                        '--unset',
                        default=False,
                        action='store_true',
                        help='Unset option')
    config_parser.add_argument('name',
                        help='Option name')
    config_parser.add_argument('value',
                        nargs='?',
                        default=None,
                        help='Option value')
    config_parser.set_defaults(func=CmdConfig)

    return parser.parse_args(argv)
