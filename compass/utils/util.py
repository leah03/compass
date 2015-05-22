# Copyright 2014 Huawei Technologies Co. Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module to provider util functions in all compass code

   .. moduleauthor:: Xiaodong Wang <xiaodongwang@huawei.com>
"""

import crypt
import datetime
import logging
import os
import os.path
import re
import sys


def parse_datetime(date_time, exception_class=Exception):
    """Parse datetime str to get datetime object."""
    try:
        return datetime.datetime.strptime(
            date_time, '%Y-%m-%d %H:%M:%S'
        )
    except Exception as error:
        logging.exception(error)
        raise exception_class(
            'date time %s format is invalid' % date_time
        )


def parse_datetime_range(date_time_range, exception_class=Exception):
    """parse datetime range str to pair of datetime objects."""
    try:
        start, end = date_time_range.split(',')
    except Exception as error:
        logging.exception(error)
        raise exception_class(
            'there is no `,` in date time range %s' % date_time_range
        )
    if start:
        start_datetime = parse_datetime(start, exception_class)
    else:
        start_datetime = None
    if end:
        end_datetime = parse_datetime(end, exception_class)
    else:
        end_datetime = None
    return start_datetime, end_datetime


def parse_request_arg_dict(arg, exception_class=Exception):
    """parse string to dict."""
    arg_dict = {}
    arg_pairs = arg.split(';')
    for arg_pair in arg_pairs:
        try:
            arg_name, arg_value = arg_pair.split('=', 1)
        except Exception as error:
            logging.exception(error)
            raise exception_class(
                'there is no `=` in %s' % arg_pair
            )
        arg_dict[arg_name] = arg_value
    return arg_dict


def format_datetime(date_time):
    """Generate string from datetime object."""
    return date_time.strftime("%Y-%m-%d %H:%M:%S")


def merge_dict(lhs, rhs, override=True):
    """Merge nested right dict into left nested dict recursively.

    :param lhs: dict to be merged into.
    :type lhs: dict
    :param rhs: dict to merge from.
    :type rhs: dict
    :param override: the value in rhs overide the value in left if True.
    :type override: boolean
    """
    if not isinstance(lhs, dict) or not isinstance(rhs, dict):
        if override:
            return rhs
        else:
            return lhs

    for key, value in rhs.items():
        if key not in lhs:
            lhs[key] = rhs[key]
        else:
            lhs[key] = merge_dict(lhs[key], value, override)

    return lhs


def encrypt(value, crypt_method=None):
    """Get encrypted value."""
    if not crypt_method:
        if hasattr(crypt, 'METHOD_MD5'):
            crypt_method = crypt.METHOD_MD5
        else:
            # for python2.7, copy python2.6 METHOD_MD5 logic here.
            from random import choice
            import string

            _saltchars = string.ascii_letters + string.digits + './'

            def _mksalt():
                """generate salt."""
                salt = '$1$'
                salt += ''.join(choice(_saltchars) for _ in range(8))
                return salt

            crypt_method = _mksalt()

    return crypt.crypt(value, crypt_method)


def parse_time_interval(time_interval_str):
    if not time_interval_str:
        return 0

    time_interval_tuple = [
        time_interval_element
        for time_interval_element in time_interval_str.split(' ')
        if time_interval_element
    ]
    time_interval_dict = {}
    time_interval_unit_mapping = {
        'd': 'days',
        'w': 'weeks',
        'h': 'hours',
        'm': 'minutes',
        's': 'seconds'
    }
    for time_interval_element in time_interval_tuple:
        mat = re.match(r'^([+-]?\d+)(w|d|h|m|s).*', time_interval_element)
        if not mat:
            continue

        time_interval_value = int(mat.group(1))
        time_interval_unit = time_interval_unit_mapping[mat.group(2)]
        time_interval_dict[time_interval_unit] = (
            time_interval_dict.get(time_interval_unit, 0) + time_interval_value
        )

    time_interval = datetime.timedelta(**time_interval_dict)
    if sys.version_info[0:2] > (2, 6):
        return time_interval.total_seconds()
    else:
        return (
            time_interval.microseconds + (
                time_interval.seconds + time_interval.days * 24 * 3600
            ) * 1e6
        ) / 1e6


def load_configs(
    config_dir, config_name_suffix='.conf',
    env_globals={}, env_locals={}
):
    configs = []
    config_dir = str(config_dir)
    if not os.path.exists(config_dir):
        logging.debug('path %s does not exist', config_dir)
        return configs
    for component in os.listdir(config_dir):
        if not component.endswith(config_name_suffix):
            continue
        path = os.path.join(config_dir, component)
        logging.debug('load config from %s', path)
        config_globals = {}
        config_globals.update(env_globals)
        config_locals = {}
        config_locals.update(env_locals)
        try:
            execfile(path, config_globals, config_locals)
        except Exception as error:
            logging.exception(error)
            raise error
        configs.append(config_locals)
    return configs


def is_instance(instance, expected_types):
    """Check instance type is in one of expected types.

    :param instance: instance to check the type.
    :param expected_types: types to check if instance type is in them.
    :type expected_types: list of type

    :returns: True if instance type is in expect_types.
    """
    for expected_type in expected_types:
        if isinstance(instance, expected_type):
            return True

    return False


def pretty_print(*contents):
    """pretty print contents."""
    if len(contents) == 0:
        print ""
    else:
        print "\n".join(content for content in contents)


def get_switch_machines_from_file(filename):
    """get switch machines from file."""
    switches = []
    switch_machines = {}
    with open(filename) as switch_file:
        for line in switch_file:
            line = line.strip()
            if not line:
                # ignore empty line
                continue

            if line.startswith('#'):
                # ignore comments
                continue

            columns = [column for column in line.split(',')]
            if not columns:
                # ignore empty line
                continue

            if columns[0] == 'switch':
                (switch_ip, switch_vendor, switch_version,
                 switch_community, switch_state) = columns[1:]
                switches.append({
                    'ip': switch_ip,
                    'vendor': switch_vendor,
                    'credentials': {
                        'version': switch_version,
                        'community': switch_community,
                    },
                    'state': switch_state,
                })
            elif columns[0] == 'machine':
                switch_ip, switch_port, mac = columns[1:]
                switch_machines.setdefault(switch_ip, []).append({
                    'mac': mac,
                    'port': switch_port,
                })

    return (switches, switch_machines)


def execute_cli_by_ssh(cmd, host, username, password=None,
                       keyfile='/root/.ssh/id_rsa', nowait=False):
    """SSH to execute script on remote machine

    :param host: ip of the remote machine
    :param username: username to access the remote machine
    :param password: password to access the remote machine
    :param cmd: command to execute

    """
    if not cmd:
        logging.error("No command found!")
        raise Exception('No command found!')

    if nowait:
        cmd = "nohup %s >/dev/null 2>&1 &" % cmd

    stdin = None
    stdout = None
    stderr = None
    try:
        import paramiko
        from paramiko import ssh_exception

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if password:
            client.connect(host, username=username, password=password)
        else:
            client.load_system_host_keys()
            client.connect(
                host, username=username,
                key_filename=keyfile, look_for_keys=True
            )
        stdin, stdout, stderr = client.exec_command(cmd)
        result = stdout.readlines()
        logging.info("result of command '%s' is '%s'!" % (cmd, result))
        return result

    except ImportError:
        err_msg = "Cannot find Paramiko package!"
        logging.error(err_msg)
        raise ImportError(err_msg)

    except (ssh_exception.BadHostKeyException,
            ssh_exception.AuthenticationException,
            ssh_exception.SSHException):

        err_msg = 'SSH connection error or command execution failed!'
        logging.error(err_msg)
        raise Exception(err_msg)

    except Exception as exc:
        logging.error(
            'Failed to execute command "%s", exception is %s' % (cmd, exc)
        )
        raise Exception(exc)

    finally:
        for resource in [stdin, stdout, stderr]:
            if resource:
                resource.close()

        client.close()
