# (c) 2020 Frabit Project maintained and limited by Blylei < blylei.info@gmail.com >
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This file is part of Frabit
#
from mysql.connector.errors import DatabaseError, InterfaceError, PoolError


class FrabitException(Exception):
    """
    The base class of all other Frabit exceptions
    """


class ConfigurationException(FrabitException):
    """
    Base exception for all the Configuration errors
    """


class CommandException(FrabitException):
    """
    Base exception for all the errors related to
    the execution of a Command.
    """


class CompressionException(FrabitException):
    """
    Base exception for all the errors related to
    the execution of a compression action.
    """


class MysqlException(DatabaseError):
    """
    Exception for errors related to the database for MySQL.
    """


class MysqlDataError(MysqlException):
    """
    Exception for errors reporting problems with processed data related to MySQL.
    """


class MysqlIntegrityError(MysqlException):
    """
    Exception for errors regarding relational integrity related to MySQL.
    """


class MysqlInternalError(MysqlException):
    """
    Exception for errors internal database errors related to MySQL.
    """


class MysqlOperationalError(MysqlException):
    """
    Exception for errors related to the database's operation for MySQL.
    """


class MysqlNotSupportedError(MysqlException):
    """
    Exception for errors when an unsupported database feature was used for MySQL.
    """


class MysqlProgrammingError(MysqlException):
    """
    Exception for errors programming errors for MySQL.
    """


class MysqlConnectError(PoolError):
    """
    Exception for errors relating to connection pooling related to MySQL
    """


class MysqlInterfaceError(InterfaceError):
    """
    Exception for errors related to the interface related to MySQL
    """


class BackupException(FrabitException):
    """
    Base exception for all the errors related to the execution of a backup.
    """


class BackupInefficientPrivilege(BackupException):
    """
    Superuser or access to backup functions is required
    """


class BackupInfoBadInitialisation(BackupException):
    """
    Exception for a bad initialization error
    """


class HookScriptException(FrabitException):
    """
    Base exception for all the errors related to Hook Script execution.
    """


class LockFileException(FrabitException):
    """
    Base exception for lock related errors
    """


class SyncException(FrabitException):
    """
    Base Exception for synchronisation functions
    """


class SshCommandException(CommandException):
    """
    Error parsing ssh_command parameter
    """


class TimeoutError(CommandException):
    """
    Error parsing command execute timeout parameter
    """


class UnknownBackupIdException(BackupException):
    """
    The searched backup_id doesn't exists
    """


class SyncError(SyncException):
    """
    Synchronisation error
    """


class SyncNothingToDo(SyncException):
    """
    Nothing to do during sync operations
    """


class SyncToBeDeleted(SyncException):
    """
    An incomplete backup is to be deleted
    """


class CommandFailedException(CommandException):
    """
    Exception representing a failed command
    """


class CommandMaxRetryExceeded(CommandFailedException):
    """
    A command with retry_times > 0 has exceeded the number of available retry
    """


class RsyncListFilesFailure(CommandException):
    """
    Failure parsing the output of a "rsync --list-only" command
    """


class DataTransferFailure(CommandException):
    """
    Used to pass failure details from a data transfer Command
    """

    @classmethod
    def from_command_error(cls, cmd, e, msg):
        """
        This method build a DataTransferFailure exception and report the
        provided message to the user (both console and log file) along with
        the output of the failed command.

        :param str cmd: The command that failed the transfer
        :param CommandFailedException e: The exception we are handling
        :param str msg: a descriptive message on what we are trying to do
        :return DataTransferFailure: will contain the message provided in msg
        """
        try:
            details = msg
            details += "\n%s error:\n" % cmd
            details += e.args[0]['out']
            details += e.args[0]['err']
            return cls(details)
        except (TypeError, NameError):
            # If it is not a dictionary just convert it to a string
            from frabit.utils import force_str
            return cls(force_str(e.args))


class CompressionIncompatibility(CompressionException):
    """
    Exception for compression incompatibility
    """


class FsOperationFailed(CommandException):
    """
    Exception which represents a failed execution of a command on FS
    """


class LockFileBusy(LockFileException):
    """
    Raised when a lock file is not free
    """


class LockFilePermissionDenied(LockFileException):
    """
    Raised when a lock file is not accessible
    """


class LockFileParsingError(LockFileException):
    """
    Raised when the content of the lockfile is unexpected
    """


class ConninfoException(ConfigurationException):
    """
    Error for missing or failed parsing of the conninfo parameter (DSN)
    """


class BinlogHasPurged(MysqlException):
    """
    Error connecting to the MySQL server
    """
    def __str__(self):
        # Returns the first line
        if self.args and self.args[0]:
            from frabit.utils import force_str
            return force_str(self.args[0]).splitlines()[0].strip()
        else:
            return ''


class AbortedRetryHookScript(HookScriptException):
    """
    Exception for handling abort of retry hook scripts
    """
    def __init__(self, hook):
        """
        Initialise the exception with hook script info
        """
        self.hook = hook

    def __str__(self):
        """
        String representation
        """
        return ("Abort '%s_%s' retry hook script (%s, exit code: %d)" % (
                self.hook.phase, self.hook.name,
                self.hook.script, self.hook.exit_status))


class RecoveryException(FrabitException):
    """
    Exception for a recovery error
    """


class RecoveryTargetActionException(RecoveryException):
    """
    Exception for a wrong recovery target action
    """


class RecoveryStandbyModeException(RecoveryException):
    """
    Exception for a wrong recovery standby mode
    """


class RecoveryInvalidTargetException(RecoveryException):
    """
    Exception for a wrong recovery target
    """
