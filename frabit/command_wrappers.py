# (c) 2020 Frabit Project maintained and limited by Blylei < blylei.info@gmail.com >
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This file is part of Frabit
#
from __future__ import print_function

import errno
import inspect
import logging
import os
import re
import select
import signal
import subprocess
import sys
import time

from distutils.version import LooseVersion as Version

import frabit.utils
from frabit.exceptions import CommandFailedException, CommandMaxRetryExceeded

_logger = logging.getLogger(__name__)


class StreamLineProcessor:
    """
    Class deputed to reading lines from a file object, using a buffered read.

    NOTE: This class never call os.read() twice in a row. And is designed to
    work with the select.select() method.
    """

    def __init__(self, fobject, handler):
        """
        :param file fobject: The file that is being read
        :param callable handler: The function (taking only one unicode string
         argument) which will be called for every line
        """
        self._file = fobject
        self._handler = handler
        self._buf = ''

    def fileno(self):
        """
        Method used by select.select() to get the underlying file descriptor.

        :rtype: the underlying file descriptor
        """
        return self._file.fileno()

    def process(self):
        """
        Read the ready data from the stream and for each line found invoke the
        handler.

        :return bool: True when End Of File has been reached
        """
        data = os.read(self._file.fileno(), 4096)
        # If nothing has been read, we reached the EOF
        if not data:
            self._file.close()
            # Handle the last line (always incomplete, maybe empty)
            self._handler(self._buf)
            return True
        self._buf += data.decode('utf-8', 'replace')
        # If no '\n' is present, we just read a part of a very long line.
        # Nothing to do at the moment.
        if '\n' not in self._buf:
            return False
        tmp = self._buf.split('\n')
        # Leave the remainder in self._buf
        self._buf = tmp[-1]
        # Call the handler for each complete line.
        lines = tmp[:-1]
        for line in lines:
            self._handler(line)
        return False


class Command:
    """
    Wrapper for a system command
    """

    def __init__(self, cmd, args=None, env_append=None, path=None, shell=False, check=False, allowed_retval=(0,),
                 close_fds=True, out_handler=None, err_handler=None, retry_times=0, retry_sleep=0,
                 retry_handler=None):
        """
        If the `args` argument is specified the arguments will be always added
        to the ones eventually passed with the actual invocation.

        If the `env_append` argument is present its content will be appended to
        the environment of every invocation.

        The subprocess output and error stream will be processed through
        the output and error handler, respectively defined through the
        `out_handler` and `err_handler` arguments. If not provided every line
        will be sent to the log respectively at INFO and WARNING level.

        The `out_handler` and the `err_handler` functions will be invoked with
        one single argument, which is a string containing the line that is
        being processed.

        If the `close_fds` argument is True, all file descriptors
        except 0, 1 and 2 will be closed before the child process is executed.

        If the `check` argument is True, the exit code will be checked
        against the `allowed_retval` list, raising a CommandFailedException if
        not in the list.

        If `retry_times` is greater than 0, when the execution of a command
        terminates with an error, it will be retried for
        a maximum of `retry_times` times, waiting for `retry_sleep` seconds
        between every attempt.

        Every time a command is retried the `retry_handler` is executed
        before running the command again. The retry_handler must be a callable
        that accepts the following fields:

         * the Command object
         * the arguments list
         * the keyword arguments dictionary
         * the number of the failed attempt
         * the exception containing the error

        An example of such a function is:

            > def retry_handler(command, args, kwargs, attempt, exc):
            >     print("Failed command!")

        Some of the keyword arguments can be specified both in the class
        constructor and during the method call. If specified in both places,
        the method arguments will take the precedence over
        the constructor arguments.

        :param str cmd: The command to exexute
        :param list[str]|None args: List of additional arguments to append
        :param dict[str.str]|None env_append: additional environment variables
        :param str path: PATH to be used while searching for `cmd`
        :param bool shell: If true, use the shell instead of an "execve" call
        :param bool check: Raise a CommandFailedException if the exit code
            is not present in `allowed_retval`
        :param list[int] allowed_retval: List of exit codes considered as a
            successful termination.
        :param bool close_fds: If set, close all the extra file descriptors
        :param callable out_handler: handler for lines sent on stdout
        :param callable err_handler: handler for lines sent on stderr
        :param int retry_times: number of allowed retry attempts
        :param int retry_sleep: wait seconds between every retry
        :param callable retry_handler: handler invoked during a command retry
        """
        self.pipe = None
        self.cmd = cmd
        self.args = args if args is not None else []
        self.shell = shell
        self.close_fds = close_fds
        self.check = check
        self.allowed_retval = allowed_retval
        self.retry_times = retry_times
        self.retry_sleep = retry_sleep
        self.retry_handler = retry_handler
        self.path = path
        self.ret = None
        self.out = None
        self.err = None
        # If env_append has been provided use it or replace with an empty dict
        env_append = env_append or {}
        # If path has been provided, replace it in the environment
        if path:
            env_append['PATH'] = path
        # Find the absolute path to the command to execute
        if not self.shell:
            full_path = frabit.utils.which(self.cmd, self.path)
            if not full_path:
                raise CommandFailedException('{} not in PATH'.format(self.cmd))
            self.cmd = full_path
        # If env_append contains anything, build an env dict to be used during
        # subprocess call, otherwise set it to None and let the subprocesses
        # inherit the parent environment
        if env_append:
            self.env = os.environ.copy()
            self.env.update(env_append)
        else:
            self.env = None
        # If an output handler has been provided use it, otherwise log the
        # stdout as INFO
        if out_handler:
            self.out_handler = out_handler
        else:
            self.out_handler = self.make_logging_handler(logging.INFO)
        # If an error handler has been provided use it, otherwise log the
        # stderr as WARNING
        if err_handler:
            self.err_handler = err_handler
        else:
            self.err_handler = self.make_logging_handler(logging.WARNING)

    @staticmethod
    def _restore_sigpipe():
        """restore default signal handler (http://bugs.python.org/issue1652)"""
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # pragma: no cover

    def __call__(self, *args, **kwargs):
        """
        Run the command and return the exit code.

        The output and error strings are not returned, but they can be accessed
        as attributes of the Command object, as well as the exit code.

        If `stdin` argument is specified, its content will be passed to the
        executed command through the standard input descriptor.

        If the `close_fds` argument is True, all file descriptors
        except 0, 1 and 2 will be closed before the child process is executed.

        If the `check` argument is True, the exit code will be checked
        against the `allowed_retval` list, raising a CommandFailedException if
        not in the list.

        Every keyword argument can be specified both in the class constructor
        and during the method call. If specified in both places,
        the method arguments will take the precedence over
        the constructor arguments.

        :rtype: int
        :raise: CommandFailedException
        :raise: CommandMaxRetryExceeded
        """
        self.get_output(*args, **kwargs)
        return self.ret

    def get_output(self, *args, **kwargs):
        """
        Run the command and return the output and the error as a tuple.

        The return code is not returned, but it can be accessed as an attribute
        of the Command object, as well as the output and the error strings.

        If `stdin` argument is specified, its content will be passed to the
        executed command through the standard input descriptor.

        If the `close_fds` argument is True, all file descriptors
        except 0, 1 and 2 will be closed before the child process is executed.

        If the `check` argument is True, the exit code will be checked
        against the `allowed_retval` list, raising a CommandFailedException if
        not in the list.

        Every keyword argument can be specified both in the class constructor
        and during the method call. If specified in both places,
        the method arguments will take the precedence over
        the constructor arguments.

        :rtype: tuple[str, str]
        :raise: CommandFailedException
        :raise: CommandMaxRetryExceeded
        """
        attempt = 0
        while True:
            try:
                return self._get_output_once(*args, **kwargs)
            except CommandFailedException as exc:
                # Try again if retry number is lower than the retry limit
                if attempt < self.retry_times:
                    # If a retry_handler is defined, invoke it passing the
                    # Command instance and the exception
                    if self.retry_handler:
                        self.retry_handler(self, args, kwargs, attempt, exc)
                    # Sleep for configured time, then try again
                    time.sleep(self.retry_sleep)
                    attempt += 1
                else:
                    if attempt == 0:
                        # No retry requested by the user
                        # Raise the original exception
                        raise
                    else:
                        # If the max number of attempts is reached and
                        # there is still an error, exit raising
                        # a CommandMaxRetryExceeded exception and wrap the
                        # original one
                        raise CommandMaxRetryExceeded(*exc.args)

    def _get_output_once(self, *args, **kwargs):
        """
        Run the command and return the output and the error as a tuple.

        The return code is not returned, but it can be accessed as an attribute
        of the Command object, as well as the output and the error strings.

        If `stdin` argument is specified, its content will be passed to the
        executed command through the standard input descriptor.

        If the `close_fds` argument is True, all file descriptors
        except 0, 1 and 2 will be closed before the child process is executed.

        If the `check` argument is True, the exit code will be checked
        against the `allowed_retval` list, raising a CommandFailedException if
        not in the list.

        Every keyword argument can be specified both in the class constructor
        and during the method call. If specified in both places,
        the method arguments will take the precedence over
        the constructor arguments.

        :rtype: tuple[str, str]
        :raises: CommandFailedException
        """
        out = []
        err = []
        # If check is true, it must be handled here
        check = kwargs.pop('check', self.check)
        allowed_retval = kwargs.pop('allowed_retval', self.allowed_retval)
        self.execute(out_handler=out.append, err_handler=err.append,
                     check=False, *args, **kwargs)
        self.out = '\n'.join(out)
        self.err = '\n'.join(err)

        _logger.debug("Command stdout: {}".format(self.out))
        _logger.debug("Command stderr: {}".format(self.err))

        # Raise if check and the return code is not in the allowed list
        if check:
            self.check_return_value(allowed_retval)
        return self.out, self.err

    def check_return_value(self, allowed_retval):
        """
        Check the current return code and raise CommandFailedException when
        it's not in the allowed_retval list

        :param list[int] allowed_retval: list of return values considered
            success
        :raises: CommandFailedException
        """
        if self.ret not in allowed_retval:
            raise CommandFailedException(dict(
                ret=self.ret, out=self.out, err=self.err))

    def execute(self, *args, **kwargs):
        """
        Execute the command and pass the output to the configured handlers

        If `stdin` argument is specified, its content will be passed to the
        executed command through the standard input descriptor.

        The subprocess output and error stream will be processed through
        the output and error handler, respectively defined through the
        `out_handler` and `err_handler` arguments. If not provided every line
        will be sent to the log respectively at INFO and WARNING level.

        If the `close_fds` argument is True, all file descriptors
        except 0, 1 and 2 will be closed before the child process is executed.

        If the `check` argument is True, the exit code will be checked
        against the `allowed_retval` list, raising a CommandFailedException if
        not in the list.

        Every keyword argument can be specified both in the class constructor
        and during the method call. If specified in both places,
        the method arguments will take the precedence over
        the constructor arguments.

        :rtype: int
        :raise: CommandFailedException
        """
        # Check keyword arguments
        stdin = kwargs.pop('stdin', None)
        check = kwargs.pop('check', self.check)
        allowed_retval = kwargs.pop('allowed_retval', self.allowed_retval)
        close_fds = kwargs.pop('close_fds', self.close_fds)
        out_handler = kwargs.pop('out_handler', self.out_handler)
        err_handler = kwargs.pop('err_handler', self.err_handler)
        if len(kwargs):
            raise TypeError('{}() got an unexpected keyword argument {}'.format(inspect.stack()[1][3], kwargs.popitem()[0]))

        # Reset status
        self.ret = None
        self.out = None
        self.err = None

        # Create the subprocess and save it in the current object to be usable
        # by signal handlers
        pipe = self._build_pipe(args, close_fds)
        self.pipe = pipe

        # Send the provided input and close the stdin descriptor
        if stdin:
            pipe.stdin.write(stdin)
        pipe.stdin.close()
        # Prepare the list of processors
        processors = [
            StreamLineProcessor(pipe.stdout, out_handler),
            StreamLineProcessor(pipe.stderr, err_handler)]

        # Read the streams until the subprocess exits
        self.pipe_processor_loop(processors)

        # Reap the zombie and read the exit code
        pipe.wait()
        self.ret = pipe.returncode

        # Remove the closed pipe from the object
        self.pipe = None
        _logger.debug("Command return code: {}".format(self.ret))

        # Raise if check and the return code is not in the allowed list
        if check:
            self.check_return_value(allowed_retval)
        return self.ret

    def _build_pipe(self, args, close_fds):
        """
        Build the Pipe object used by the Command

        The resulting command will be composed by:
           self.cmd + self.args + args

        :param args: extra arguments for the subprocess
        :param close_fds: if True all file descriptors except 0, 1 and 2
            will be closed before the child process is executed.
        :rtype: subprocess.Popen
        """
        # Append the argument provided to this method of the base argument list
        args = self.args + list(args)
        # If shell is True, properly quote the command
        if self.shell:
            cmd = full_command_quote(self.cmd, args)
        else:
            cmd = [self.cmd] + args

        # Log the command we are about to execute
        _logger.debug("Command: %r", cmd)
        return subprocess.Popen(cmd, shell=self.shell, env=self.env,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                preexec_fn=self._restore_sigpipe,
                                close_fds=close_fds)

    @staticmethod
    def pipe_processor_loop(processors):
        """
        Process the output received through the pipe until all the provided
        StreamLineProcessor reach the EOF.

        :param list[StreamLineProcessor] processors: a list of
            StreamLineProcessor
        """
        # Loop until all the streams reaches the EOF
        while processors:
            try:
                ready = select.select(processors, [], [])[0]
            except select.error as e:
                # If the select call has been interrupted by a signal
                # just retry
                if e.args[0] == errno.EINTR:
                    continue
                raise

            # For each ready StreamLineProcessor invoke the process() method
            for stream in ready:
                eof = stream.process()
                # Got EOF on this stream
                if eof:
                    # Remove the stream from the list of valid processors
                    processors.remove(stream)

    @classmethod
    def make_logging_handler(cls, level, prefix=None):
        """
        Build a handler function that logs every line it receives.

        The resulting function logs its input at the specified level
        with an optional prefix.

        :param level: The log level to use
        :param prefix: An optional prefix to prepend to the line
        :return: handler function
        """
        class_logger = logging.getLogger(cls.__name__)

        def handler(line):
            if line:
                if prefix:
                    class_logger.log(level, "{prefix}{line}".format(prefix=prefix, line=line))
                else:
                    class_logger.log(level, "{}".format(line))
        return handler

    @staticmethod
    def make_output_handler(prefix=None):
        """
        Build a handler function which prints every line it receives.

        The resulting function prints (and log it at INFO level) its input
        with an optional prefix.

        :param prefix: An optional prefix to prepend to the line
        :return: handler function
        """

        # Import the output module inside the function to avoid circular
        # dependency
        from frabit import output

        def handler(line):
            if line:
                if prefix:
                    output.info("{prefix}{line}".format(prefix=prefix, line=line))
                else:
                    output.info("{}".format(line))

        return handler

    def enable_signal_forwarding(self, signal_id):
        """
        Enable signal forwarding to the subprocess for a specified signal_id

        :param signal_id: The signal id to be forwarded
        """
        # Get the current signal handler
        old_handler = signal.getsignal(signal_id)

        def _handler(sig, frame):
            """
            This signal handler forward the signal to the subprocess then
            execute the original handler.
            """
            # Forward the signal to the subprocess
            if self.pipe:
                self.pipe.send_signal(signal_id)
            # If the old handler is callable
            if callable(old_handler):
                old_handler(sig, frame)
            # If we have got a SIGTERM, we must exit
            elif old_handler == signal.SIG_DFL and signal_id == signal.SIGTERM:
                sys.exit(128 + signal_id)

        # Set the signal handler
        signal.signal(signal_id, _handler)


class Ssh(Command):
    """
    This class is a wrapper for the ssh system command,
    which is used vastly by frabit
    """

    def __init__(self, rsync='rsync', args=None, ssh=None, ssh_options=None, bwlimit=None, exclude=None,
                 exclude_and_protect=None, include=None, network_compression=None, path=None, **kwargs):
        """
        :param str rsync: rsync executable name
        :param list[str]|None args: List of additional argument to always append
        :param str ssh: the ssh executable to be used when building the `-e` argument
        :param list[str] ssh_options: the ssh options to be used when building the `-e` argument
        :param str bwlimit: optional bandwidth limit
        :param list[str] exclude: list of file to be excluded from the copy
        :param list[str] exclude_and_protect: list of file to be excluded from the copy, preserving the destination
        if exists
        :param list[str] include: list of files to be included in the copy even if excluded.
        :param bool network_compression: enable the network compression
        :param str path: PATH to be used while searching for `cmd`
        :param bool check: Raise a CommandFailedException if the exit code is not present in `allowed_retval`
        :param list[int] allowed_retval: List of exit codes considered as a successful termination.
        """
        options = []
        if ssh:
            options += ['-e', full_command_quote(ssh, ssh_options)]
        if network_compression:
            options += ['-z']
        # Include patterns must be before the exclude ones, because the exclude
        # patterns actually short-circuit the directory traversal stage
        # when rsync finds the files to send.
        if include:
            for pattern in include:
                options += ["--include={}".format(pattern)]
        if exclude:
            for pattern in exclude:
                options += ["--exclude={}".format(pattern)]
        if exclude_and_protect:
            for pattern in exclude_and_protect:
                options += ["--exclude=%s" % (pattern,),
                            "--filter=P_%s" % (pattern,)]
        if args:
            options += self._args_for_suse(args)
        if bwlimit is not None and bwlimit > 0:
            options += ["--bwlimit={}".format(bwlimit)]

        # By default check is on and the allowed exit code are 0 and 24
        if 'check' not in kwargs:
            kwargs['check'] = True
        if 'allowed_retval' not in kwargs:
            kwargs['allowed_retval'] = (0, 24)
        Command.__init__(self, rsync, args=options, path=path, **kwargs)

    def _args_for_suse(self, args):
        """
        Mangle args for SUSE compatibility

        See https://bugzilla.opensuse.org/show_bug.cgi?id=898513
        """
        # Prepend any argument starting with ':' with a space
        # Workaround for SUSE rsync issue
        return [' ' + a if a.startswith(':') else a for a in args]

    def get_output(self, *args, **kwargs):
        """
        Run the command and return the output and the error (if present)
        """
        # Prepares args for SUSE
        args = self._args_for_suse(args)
        # Invoke the base class method
        return super(Ssh, self).get_output(*args, **kwargs)


class Xtrabackup(Command):
    """A wrapper for Percona XtraBackup aka PXB"""
    def __init__(self):
        pass

    def test(self):
        pass


class Mysqldump(Command):
    """A wrapper for Mysqldump"""

    def __init__(self):
        pass

    def test(self):
        pass


class Mysqlbinlog(Command):
    """A wrapper for Mysqldump"""

    def __init__(self):
        pass

    def test(self):
        pass


class FrabitSubProcess:
    """
    Wrapper class for frabit sub instances
    """

    def __init__(self, command=sys.argv[0], subcommand=None, config=None, args=None, keep_descriptors=False):
        """
        Build a specific wrapper for all the frabit sub-commands, providing an unified interface.

        :param str command: path to frabit
        :param str subcommand: the frabit sub-command
        :param str config: path to the frabit configuration file.
        :param list[str] args: a list containing the sub-command args like the target server name
        :param bool keep_descriptors: whether to keep the subprocess stdin,  stdout, stderr descriptors attached.
         Defaults to False
        """
        # The config argument is needed when the user explicitly
        # passes a configuration file, as the child process
        # must know the configuration file to use.
        #
        # The configuration file must always be propagated,
        # even in case of the default one.
        if not config:
            raise CommandFailedException(
                "No configuration file passed to frabit subprocess")
        # Build the sub-command:
        # * be sure to run it with the right python interpreter
        # * pass the current configuration file with -c
        # * set it quiet with -q
        self.command = [sys.executable, command, '-c', config, '-q', subcommand]
        self.keep_descriptors = keep_descriptors
        # Handle args for the sub-command (like the server name)
        if args:
            self.command += args

    def execute(self):
        """
        Execute the command and pass the output to the configured handlers
        """
        _logger.debug("FrabitSubProcess: {}".format(self.command))
        # Redirect all descriptors to /dev/null
        devnull = open(os.devnull, 'a+')

        additional_arguments = {}
        if not self.keep_descriptors:
            additional_arguments = {'stdout': devnull, 'stderr': devnull}

        proc = subprocess.Popen(self.command, preexec_fn=os.setsid, close_fds=True, stdin=devnull,
                                **additional_arguments)
        _logger.debug("FrabitSubProcess: subprocess started. pid: {}".format(proc.pid))


def shell_quote(arg):
    """
    Quote a string argument to be safely included in a shell command line.

    :param str arg: The script argument
    :return: The argument quoted
    """

    # This is an excerpt of the Bash zh page, and the same applies for
    # every Posix compliant shell:
    #
    #     A  non-quoted backslash (\) is the escape character.  It preserves
    #     the literal value of the next character that follows, with the
    #     exception of <newline>.  If a \<newline> pair appears, and the
    #     backslash is not itself quoted, the \<newline> is treated as a
    #     line continuation (that is, it is removed  from  the  input
    #     stream  and  effectively ignored).
    #
    #     Enclosing characters in single quotes preserves the literal value
    #     of each character within the quotes.  A single quote may not occur
    #     between single quotes, even when pre-ceded by a backslash.
    #
    # This means that, as long as the original string doesn't contain any
    # apostrophe character, it can be safely included between single quotes.
    #
    # If a single quote is contained in the string, we must terminate the
    # string with a quote, insert an apostrophe character escaping it with
    # a backslash, and then start another string using a quote character.

    assert arg is not None
    return "'{}'".format(arg.replace("'", "'\\''"))


def full_command_quote(command, args=None):
    """
    Produce a command with quoted arguments

    :param str command: the command to be executed
    :param list[str] args: the command arguments
    :rtype: str
    """
    if args is not None and len(args) > 0:
        args = ' '.join([shell_quote(arg) for arg in args])
        return "{cmd} {args}".format(cmd=command, args=args)
    else:
        return command