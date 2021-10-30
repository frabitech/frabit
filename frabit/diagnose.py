# (c) 2020 Frabit Project maintained and limited by Blylei < blylei.info@gmail.com >
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This file is part of Frabit
#

"""
This module represents the frabit diagnostic tool.
"""

import datetime
import json
import logging

import frabit
from frabit import filesystem, output
from frabit.backup import BackupInfo
from frabit.exceptions import CommandFailedException, FsOperationFailed
from frabit.utils import FrabitEncoder

_logger = logging.getLogger(__name__)


def exec_diagnose(servers, errors_list):
    """
    Diagnostic command: gathers information from backup server
    and from all the configured servers.

    Gathered information should be used for support and problems detection

    :param dict(str,frabit.server.Server) servers: list of configured servers
    :param list errors_list: list of global errors
    """
    # global section. info about frabit server
    diagnosis = {'global': {}, 'servers': {}}
    # frabit global config
    diagnosis['global']['config'] = dict(frabit.__config__._global_config)
    diagnosis['global']['config']['errors_list'] = errors_list
    try:
        command = filesystem.UnixLocalCommand()
        # basic system info
        diagnosis['global']['system_info'] = command.get_system_info()
    except CommandFailedException as e:
        diagnosis['global']['system_info'] = {'error': repr(e)}
    diagnosis['global']['system_info']['frabit_ver'] = frabit.__version__
    diagnosis['global']['system_info']['timestamp'] = datetime.datetime.now()
    # per server section
    for name in sorted(servers):
        server = servers[name]
        if server is None:
            output.error("Unknown server '{}'".format(name))
            continue
        # server configuration
        diagnosis['servers'][name] = {}
        diagnosis['servers'][name]['config'] = vars(server.config)
        del diagnosis['servers'][name]['config']['config']
        # server system info
        if server.config.ssh_command:
            try:
                command = filesystem.UnixRemoteCommand( ssh_command=server.config.ssh_command, path=server.path)
                diagnosis['servers'][name]['system_info'] = (command.get_system_info())
            except FsOperationFailed:
                pass
        # frabit status information for the server
        diagnosis['servers'][name]['status'] = server.get_remote_status()
        # backup list
        backups = server.get_available_backups(BackupInfo.STATUS_ALL)
        diagnosis['servers'][name]['backups'] = backups
        # wal status
        diagnosis['servers'][name]['wals'] = {
            'last_archived_wal_per_timeline':
                server.backup_manager.get_latest_archived_wals_info(),
        }
        # Release any PostgreSQL resource
        server.close()
    output.info(json.dumps(diagnosis, cls=FrabitEncoder, indent=4,
                           sort_keys=True))