# (c) 2020 Frabit Project maintained and limited by Blylei < blylei.info@gmail.com >
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This file is part of Frabit
#
"""
This module is responsible for all the things related to Frabit configuration, such as parsing configuration file.
"""

import collections
import datetime
import inspect
import logging.handlers
import os
import re
import sys
from glob import iglob

from frabit import output

try:
    from ConfigParser import ConfigParser, NoOptionError
except ImportError:
    from configparser import ConfigParser, NoOptionError


# create a namedtuple object called PathConflict with 'label' and 'server'
PathConflict = collections.namedtuple('PathConflict', 'label server')

_logger = logging.getLogger(__name__)

FORBIDDEN_SERVER_NAMES = ['all']

DEFAULT_USER = 'frabit'
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s [%(process)s] %(name)s %(levelname)s: %(message)s"

_TRUE_RE = re.compile(r"""^(true|t|yes|1|on)$""", re.IGNORECASE)
_FALSE_RE = re.compile(r"""^(false|f|no|0|off)$""", re.IGNORECASE)
_TIME_INTERVAL_RE = re.compile(r"""
      ^\s*
      (\d+)\s+(day|month|week)s?  # N (day|month|week) with optional 's'
      \s*$
      """, re.IGNORECASE | re.VERBOSE)


# Possible copy methods for backups (must be all lowercase)
BACKUP_METHOD_VALUES = ['rsync', 'mysql']


class CsvOption(set):
    """
    Base class for CSV options.

    Given a comma delimited string, this class is a list containing the
    submitted options.
    Internally, it uses a set in order to avoid option replication.
    Allowed values for the CSV option are contained in the 'value_list'
    attribute.
    The 'conflicts' attribute specifies for any value, the list of
    values that are prohibited (and thus generate a conflict).
    If a conflict is found, raises a ValueError exception.
    """
    value_list = []
    conflicts = {}

    def __init__(self, value, key, source):
        # Invoke parent class init and initialize an empty set
        super(CsvOption, self).__init__()

        # Parse not None values
        if value is not None:
            self.parse(value, key, source)

        # Validates the object structure before returning the new instance
        self.validate(key, source)

    def parse(self, value, key, source):
        """
        Parses a list of values and correctly assign the set of values
        (removing duplication) and checking for conflicts.
        """
        if not value:
            return
        values_list = value.split(',')
        for val in sorted(values_list):
            val = val.strip().lower()
            if val in self.value_list:
                # check for conflicting values. if a conflict is
                # found the option is not valid then, raise exception.
                if val in self.conflicts and self.conflicts[val] in self:
                    raise ValueError("Invalid configuration value '%s' for "
                                     "key %s in %s: cannot contain both "
                                     "'%s' and '%s'."
                                     "Configuration directive ignored." %
                                     (val, key, source, val,
                                      self.conflicts[val]))
                else:
                    # otherwise use parsed value
                    self.add(val)
            else:
                # not allowed value, reject the configuration
                raise ValueError("Invalid configuration value '%s' for "
                                 "key %s in %s: Unknown option" %
                                 (val, key, source))

    def validate(self, key, source):
        """
        Override this method for special validation needs
        """

    def to_json(self):
        """
        Output representation of the obj for JSON serialization

        The result is a string which can be parsed by the same class
        """
        return ",".join(self)


class BackupOptions(CsvOption):
    """
    Extends CsvOption class providing all the details for the backup_options
    field
    """
    # constants containing labels for allowed values
    EXCLUSIVE_BACKUP = 'exclusive_backup'
    CONCURRENT_BACKUP = 'concurrent_backup'
    EXTERNAL_CONFIGURATION = 'external_configuration'

    # list holding all the allowed values for the BackupOption class
    value_list = [EXCLUSIVE_BACKUP, CONCURRENT_BACKUP, EXTERNAL_CONFIGURATION]
    # map holding all the possible conflicts between the allowed values
    conflicts = {EXCLUSIVE_BACKUP: CONCURRENT_BACKUP, CONCURRENT_BACKUP: EXCLUSIVE_BACKUP}


class RecoveryOptions(CsvOption):
    """
    Extends CsvOption class providing all the details for the recovery_options
    field
    """
    # constants containing labels for allowed values
    GET_WAL = 'get-wal'

    # list holding all the allowed values for the RecoveryOptions class
    value_list = [GET_WAL]


def parse_boolean(value):
    """
    Parse a string to a boolean value

    :param str value: string representing a boolean
    :raises ValueError: if the string is an invalid boolean representation
    """
    if _TRUE_RE.match(value):
        return True
    if _FALSE_RE.match(value):
        return False
    raise ValueError("Invalid boolean representation (use 'true' or 'false')")


def parse_time_interval(value):
    """
    Parse a string, transforming it in a time interval.
    Accepted format: N (day|month|week)s

    :param str value: the string to evaluate
    """
    # if empty string or none return none
    if value is None or value == '':
        return None
    result = _TIME_INTERVAL_RE.match(value)
    # if the string doesn't match, the option is invalid
    if not result:
        raise ValueError("Invalid value for a time interval {}".format(value))
    # if the int conversion
    value = int(result.groups()[0])
    unit = result.groups()[1][0].lower()

    # Calculates the time delta
    if unit == 'd':
        time_delta = datetime.timedelta(days=value)
    elif unit == 'w':
        time_delta = datetime.timedelta(weeks=value)
    elif unit == 'm':
        time_delta = datetime.timedelta(days=(31 * value))
    else:
        # This should never happen
        raise ValueError("Invalid unit time {}".format(unit))

    return time_delta


def parse_backup_method(value):
    """
    Parse a string to a valid backup_method value.

    Valid values are contained in BACKUP_METHOD_VALUES list

    :param str value: backup_method value
    :raises ValueError: if the value is invalid
    """
    if value is None:
        return None
    if value.lower() in BACKUP_METHOD_VALUES:
        return value.lower()
    raise ValueError("Invalid value (must be one in: '{}')".format("', '".join(BACKUP_METHOD_VALUES)))


class ServerConfig:
    """
    This class represents the configuration for a specific Server instance.
    """

    KEYS = [
        'active',
        'archiver',
        'archiver_batch_size',
        'backup_directory',
        'backup_method',
        'backup_options',
        'bandwidth_limit',
        'basebackup_retry_sleep',
        'basebackup_retry_times',
        'basebackups_directory',
        'check_timeout',
        'compression',
        'conninfo',
        'custom_compression_filter',
        'custom_decompression_filter',
        'description',
        'disabled',
        'errors_directory',
        'incoming_wals_directory',
        'last_backup_maximum_age',
        'max_incoming_wals_queue',
        'minimum_redundancy',
        'network_compression',
        'parallel_jobs',
        'path_prefix',
        'post_archive_retry_script',
        'post_archive_script',
        'post_backup_retry_script',
        'post_backup_script',
        'post_delete_script',
        'post_delete_retry_script',
        'post_recovery_retry_script',
        'post_recovery_script',
        'post_wal_delete_script',
        'post_wal_delete_retry_script',
        'pre_archive_retry_script',
        'pre_archive_script',
        'pre_backup_retry_script',
        'pre_backup_script',
        'pre_delete_script',
        'pre_delete_retry_script',
        'pre_recovery_retry_script',
        'pre_recovery_script',
        'pre_wal_delete_script',
        'pre_wal_delete_retry_script',
        'primary_ssh_command',
        'recovery_options',
        'retention_policy',
        'retention_policy_mode',
        'ssh_command',
        'wal_retention_policy',
        'wals_directory'
    ]

    FRABIT_KEYS = [
        'archiver',
        'archiver_batch_size',
        'backup_method',
        'backup_options',
        'bandwidth_limit',
        'basebackup_retry_sleep',
        'basebackup_retry_times',
        'check_timeout',
        'compression',
        'configuration_files_directory',
        'custom_compression_filter',
        'custom_decompression_filter',
        'immediate_checkpoint',
        'last_backup_maximum_age',
        'max_incoming_wals_queue',
        'minimum_redundancy',
        'network_compression',
        'parallel_jobs',
        'path_prefix',
        'post_archive_retry_script',
        'post_archive_script',
        'post_backup_retry_script',
        'post_backup_script',
        'post_delete_script',
        'post_delete_retry_script',
        'post_recovery_retry_script',
        'post_recovery_script',
        'post_wal_delete_script',
        'post_wal_delete_retry_script',
        'pre_archive_retry_script',
        'pre_archive_script',
        'pre_backup_retry_script',
        'pre_backup_script',
        'pre_delete_script',
        'pre_delete_retry_script',
        'pre_recovery_retry_script',
        'pre_recovery_script',
        'pre_wal_delete_script',
        'pre_wal_delete_retry_script',
        'primary_ssh_command',
        'recovery_options',
        'retention_policy',
        'retention_policy_mode',
        'wal_retention_policy'
    ]

    DEFAULTS = {
        'active': 'true',
        'archiver': 'off',
        'archiver_batch_size': '0',
        'backup_directory': '%(frabit_home)s/%(name)s',
        'backup_method': 'rsync',
        'backup_options': '',
        'basebackup_retry_sleep': '30',
        'basebackup_retry_times': '0',
        'basebackups_directory': '%(backup_directory)s/base',
        'check_timeout': '30',
        'disabled': 'false',
        'errors_directory': '%(backup_directory)s/errors',
        'immediate_checkpoint': 'false',
        'incoming_wals_directory': '%(backup_directory)s/incoming',
        'minimum_redundancy': '0',
        'network_compression': 'false',
        'parallel_jobs': '1',
        'recovery_options': '',
        'retention_policy_mode': 'auto',
        'streaming_archiver': 'off',
        'streaming_archiver_batch_size': '0',
        'streaming_archiver_name': 'frabit_receive_wal',
        'streaming_backup_name': 'frabit_streaming_backup',
        'streaming_conninfo': '%(conninfo)s',
        'streaming_wals_directory': '%(backup_directory)s/streaming',
        'wal_retention_policy': 'main',
        'wals_directory': '%(backup_directory)s/wals'
    }

    FIXED = [
        'disabled',
    ]

    PARSERS = {
        'active': parse_boolean,
        'archiver': parse_boolean,
        'archiver_batch_size': int,
        'backup_method': parse_backup_method,
        'backup_options': BackupOptions,
        'basebackup_retry_sleep': int,
        'basebackup_retry_times': int,
        'check_timeout': int,
        'disabled': parse_boolean,
        'immediate_checkpoint': parse_boolean,
        'last_backup_maximum_age': parse_time_interval,
        'max_incoming_wals_queue': int,
        'network_compression': parse_boolean,
        'parallel_jobs': int,
        'recovery_options': RecoveryOptions,
        'streaming_archiver': parse_boolean,
        'streaming_archiver_batch_size': int
    }

    def invoke_parser(self, key, source, value, new_value):
        """
        Function used for parsing configuration values.
        If needed, it uses special parsers from the PARSERS map,
        and handles parsing exceptions.

        Uses two values (value and new_value) to manage
        configuration hierarchy (server config overwrites global config).

        :param str key: the name of the configuration option
        :param str source: the section that contains the configuration option
        :param value: the old value of the option if present.
        :param str new_value: the new value that needs to be parsed
        :return: the parsed value of a configuration option
        """
        # If the new value is None, returns the old value
        if new_value is None:
            return value
        # If we have a parser for the current key, use it to obtain the actual value. If an exception is thrown,
        # print a warning and ignore the value.
        # noinspection PyBroadException
        if key in self.PARSERS:
            parser = self.PARSERS[key]
            try:
                # If the parser is a subclass of the CsvOption class
                # we need a different invocation, which passes not only
                # the value to the parser, but also the key name
                # and the section that contains the configuration
                if inspect.isclass(parser) and issubclass(parser, CsvOption):
                    value = parser(new_value, key, source)
                else:
                    value = parser(new_value)
            except Exception as e:
                output.warning("Ignoring invalid configuration value '{new_value}' for key {key} "
                               "in {source}: {e}".format(new_value=new_value, key=key, source=source, e=e))
        else:
            value = new_value
        return value

    def __init__(self, config, name):
        self.msg_list = []
        self.config = config
        self.name = name
        self.frabit_home = config.frabit_home
        self.frabit_lock_directory = config.frabit_lock_directory
        config.validate_server_config(self.name)
        for key in ServerConfig.KEYS:
            value = None
            # Skip parameters that cannot be configured by users
            if key not in ServerConfig.FIXED:
                # Get the setting from the [name] section of config file
                # A literal None value is converted to an empty string
                new_value = config.get(name, key, self.__dict__, none_value='')
                source = '{} section'.format(name)
                value = self.invoke_parser(key, source, value, new_value)
                # If the setting isn't present in [name] section of config file
                # check if it has to be inherited from the [frabit] section
                if value is None and key in ServerConfig.BARMAN_KEYS:
                    new_value = config.get('frabit',
                                           key,
                                           self.__dict__,
                                           none_value='')
                    source = '[frabit] section'
                    value = self.invoke_parser(key, source, value, new_value)
            # If the setting isn't present in [name] section of config file
            # and is not inherited from global section use its default
            # (if present)
            if value is None and key in ServerConfig.DEFAULTS:
                new_value = ServerConfig.DEFAULTS[key] % self.__dict__
                source = 'DEFAULTS'
                value = self.invoke_parser(key, source, value, new_value)
            # An empty string is a None value (bypassing inheritance
            # from global configuration)
            if value is not None and value == '' or value == 'None':
                value = None
            setattr(self, key, value)

    def to_json(self):
        """
        Return an equivalent dictionary that can be encoded in json
        """
        json_dict = dict(vars(self))
        # remove the reference to main Config object
        del json_dict['config']
        return json_dict


class Config:
    """This class represents the frabit configuration.

    Default configuration files are /etc/frabit/frabit.conf
    """
    CONFIG_FILES = ['/etc/frabit/frabit.conf']

    _QUOTE_RE = re.compile(r"""^(["'])(.*)\1$""")

    def __init__(self, filename=None):
        #  In Python 3 ConfigParser has changed to be strict by default.
        self._config = ConfigParser(strict=False)
        # 如果提供自定义配置文件，优先使用
        if filename:
            if hasattr(filename, 'read'):
                self._config.read_file(filename)
            else:
                # check for the existence of the user defined file
                if not os.path.exists(filename):
                    sys.exit("Configuration file '{}' does not exist".format(filename))
                self._config.read(os.path.expanduser(filename))
        # 没有指定配置文件的话，使用默认的配置文件（强烈建议使用默认配置文件）
        else:
            # Check for the presence of configuration files inside default directories
            for path in self.CONFIG_FILES:
                full_path = os.path.expanduser(path)
                if os.path.exists(full_path) and full_path in self._config.read(full_path):
                    filename = full_path
                    break
            else:
                sys.exit("Could not find any configuration file at default locations.\n"
                         "Check Frabit's documentation for more help.")
        self.config_file = filename
        self._servers = None
        self.servers_msg_list = []
        self._parse_global_config()

    def get(self, section, option, defaults=None, none_value=None):
        """
        Method to get the value from a given section from Frabit configuration
        """
        if not self._config.has_section(section):
            return None
        try:
            value = self._config.get(section, option, raw=False, vars=defaults)
            if value.lower() == 'none':
                value = none_value
            if value is not None:
                value = self._QUOTE_RE.sub(lambda m: m.group(2), value)
            return value
        except NoOptionError:
            return None

    def _parse_global_config(self):
        """
        This method parses the global [frabit] section
        """
        self.frabit_home = self.get('frabit', 'frabit_home')
        self.frabit_lock_directory = self.get('frabit', 'frabit_lock_directory') or self.frabit_home
        self.user = self.get('frabit', 'frabit_user') or DEFAULT_USER
        self.log_file = self.get('frabit', 'log_file')
        self.log_format = self.get('frabit', 'log_format') or DEFAULT_LOG_FORMAT
        self.log_level = self.get('frabit', 'log_level') or DEFAULT_LOG_LEVEL
        # save the raw frabit section to be compared later in _is_global_config_changed() method
        self._global_config = set(self._config.items('frabit'))

    def _is_global_config_changed(self):
        """Return true if something has changed in global configuration"""
        return self._global_config != set(self._config.items('frabit'))

    def load_configuration_files_directory(self):
        """
        Read the "configuration_files_directory" option and load all the configuration files with the .conf suffix
        that lie in that folder
        """

        config_files_directory = self.get('frabit', 'configuration_files_directory')

        if not config_files_directory:
            return

        if not os.path.isdir(os.path.expanduser(config_files_directory)):
            _logger.warn('Ignoring the "configuration_files_directory" option as "{}" is not a directory'.format(
                config_files_directory))
            return

        for cfile in sorted(iglob(os.path.join(os.path.expanduser(config_files_directory), '*.conf'))):
            filename = os.path.basename(cfile)
            if os.path.isfile(cfile):
                # Load a file
                _logger.debug('Including configuration file: {}'.format(filename))
                self._config.read(cfile)
                if self._is_global_config_changed():
                    msg = "The configuration file {} contains a not empty [frabit] section".format(filename)
                    _logger.fatal(msg)
                    raise SystemExit("FATAL: {}".format(msg))
            else:
                # Add an info that a file has been discarded
                _logger.warn('Discarding configuration file: {} (not a file)'.format(filename))

    def _populate_servers(self):
        """
        Populate server list from config file

        Also check for paths errors in config. If two or more paths overlap in a single server,that server is disabled.
        If two or more directory paths overlap between different servers an error is raised.
        """

        # Populate servers
        if self._servers is not None:
            return
        self._servers = {}
        # Cycle all the available configurations sections
        for section in self._config.sections():
            if section == 'frabit':
                # skip global settings
                continue
            # Exit if the section has a reserved name
            if section in FORBIDDEN_SERVER_NAMES:
                msg = "The reserved word '{}' is not allowed as server name,Please rename it.".format(section)
                _logger.fatal(msg)
                raise SystemExit("FATAL: {}".format(msg))
            # Create a ServerConfig object
            self._servers[section] = ServerConfig(self, section)

        # Check for conflicting paths in Frabit configuration
        self._check_conflicting_paths()

    def _check_conflicting_paths(self):
        """
        Look for conflicting paths intra-server and inter-server
        """

        # All paths in configuration
        servers_paths = {}
        # Global errors list
        self.servers_msg_list = []

        # Cycle all the available configurations sections
        for section in sorted(self._config.sections()):
            if section == 'frabit':
                # skip global settings
                continue

            # Paths map
            section_conf = self._servers[section]
            config_paths = {
                'backup_directory': section_conf.backup_directory,
                'basebackups_directory': section_conf.basebackups_directory,
                'errors_directory': section_conf.errors_directory,
                'incoming_wals_directory': section_conf.incoming_wals_directory,
                'streaming_wals_directory': section_conf.streaming_wals_directory,
                'wals_directory': section_conf.wals_directory
            }

            # Check for path errors
            for label, path in sorted(config_paths.items()):
                # If the path does not conflict with the others, add it to the paths map
                real_path = os.path.realpath(path)
                if real_path not in servers_paths:
                    servers_paths[real_path] = PathConflict(label, section)
                else:
                    if section == servers_paths[real_path].server:
                        # Internal path error.
                        # Insert the error message into the server.msg_list
                        if real_path == path:
                            self._servers[section].msg_list.append("Conflicting path: {label}={path} conflicts with "
                            "'{real_lable}' for server '{real_path}'".format(label=label,  path=path,
                                                                             real_lable=servers_paths[real_path].label,
                                                                             real_server=servers_paths[real_path].server
                                                                             )
                                                                   )
                        else:
                            # Symbolic link
                            self._servers[section].msg_list.append(
                                "Conflicting path: {label}={path} (symlink to: {real_path}) "
                                "conflicts with '{real_label}' for server '{real_server}'".format(
                                    label=label, path=path, real_path=real_path,
                                    real_label=servers_paths[real_path].label,
                                    real_server=servers_paths[real_path].server)
                            )
                        # Disable the server
                        self._servers[section].disabled = True
                    else:
                        # Global path error.
                        # Insert the error message into the global msg_list
                        if real_path == path:
                            self.servers_msg_list.append(
                                "Conflicting path: {label}={path} for server '{section}' conflicts with "
                                "'{real_label}' for server '{real_server}'".format(
                                    label=label, path=path, section=section,
                                    real_label=servers_paths[real_path].label,
                                    real_server=servers_paths[real_path].server)
                            )
                        else:
                            # Symbolic link
                            self.servers_msg_list.append(
                                "Conflicting path: {label}={path} (symlink to: {real_path}) for server '{section}' "
                                "conflicts with '{real_label}' for server '{real_server}'".format(
                                    label=label, path=path, real_path=real_path, section=section,
                                    real_label=servers_paths[real_path].label,
                                    real_server=servers_paths[real_path].server)
                            )

    def server_names(self):
        """This method returns a list of server names"""
        self._populate_servers()
        return self._servers.keys()

    def servers(self):
        """This method returns a list of server parameters"""
        self._populate_servers()
        return self._servers.values()

    def get_server(self, name):
        """
        Get the configuration of the specified server

        :param str name: the server name
        """
        self._populate_servers()
        return self._servers.get(name, None)

    def validate_global_config(self):
        """
        Validate global configuration parameters
        """
        # Check for the existence of unexpected parameters in the global section of the configuration file
        keys = ['frabit_home',
                'frabit_lock_directory',
                'frabit_user',
                'log_file',
                'log_level',
                'configuration_files_directory']
        keys.extend(ServerConfig.KEYS)
        self._validate_with_keys(self._global_config, keys, 'frabit')

    def validate_server_config(self, server):
        """
        Validate configuration parameters for a specified server

        :param str server: the server name
        """
        # Check for the existence of unexpected parameters in the
        # server section of the configuration file
        self._validate_with_keys(self._config.items(server), ServerConfig.KEYS, server)

    @staticmethod
    def _validate_with_keys(config_items, allowed_keys, section):
        """
        Check every config parameter against a list of allowed keys

        :param config_items: list of tuples containing provided parameters along with their values
        :param allowed_keys: list of allowed keys
        :param section: source section (for error reporting)
        """
        for parameter in config_items:
            # if the parameter name is not in the list of allowed values, then output a warning
            name = parameter[0]
            if name not in allowed_keys:
                output.warning('Invalid configuration option "{name}" in [{section}] section.'.format(name=name,
                                                                                                      section=section
                                                                                                      ))


# easy raw config diagnostic with python -m
# noinspection PyProtectedMember
def _main():
    print("Active configuration settings:")
    r = Config()
    r.load_configuration_files_directory()
    for section in r._config.sections():
        print("Section: {}".format(section))
        for option in r._config.options(section):
            print("\t{option} = {value}".format(option=option, value=r.get(section, option)))


if __name__ == "__main__":
    _main()
