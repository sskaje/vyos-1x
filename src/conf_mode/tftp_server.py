#!/usr/bin/env python3
#
# Copyright (C) 2018 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import sys
import os
import stat
import pwd

import jinja2
import ipaddress
import netifaces

from vyos.config import Config
from vyos import ConfigError

config_file = r'/etc/default/tftpd-hpa'

# Please be careful if you edit the template.
config_tmpl = """
### Autogenerated by tftp_server.py ###

# See manual at https://linux.die.net/man/8/tftpd

TFTP_USERNAME="tftp"
TFTP_DIRECTORY="{{ directory }}"
{% if listen_ipv4 and listen_ipv6 -%}
TFTP_ADDRESS="{% for a in listen_ipv4 -%}{{ a }}:{{ port }}{{- " --address " if not loop.last -}}{% endfor -%} {% for a in listen_ipv6 %} --address [{{ a }}]:{{ port }}{% endfor -%}"
{% elif listen_ipv4 -%}
TFTP_ADDRESS="{% for a in listen_ipv4 -%}{{ a }}:{{ port }}{{- " --address " if not loop.last -}}{% endfor %} -4"
{% elif listen_ipv6 -%}
TFTP_ADDRESS="{% for a in listen_ipv6 -%}[{{ a }}]:{{ port }}{{- " --address " if not loop.last -}}{% endfor %} -6"
{%- endif %}

TFTP_OPTIONS="--secure {% if allow_upload %}--create --umask 002{% endif %}"
"""

default_config_data = {
    'directory': '',
    'allow_upload': False,
    'port': '69',
    'listen_ipv4': [],
    'listen_ipv6': []
}

# Verify if an IP address is assigned to any interface, IPv4 and IPv6
def addrok(ipaddr, ipversion):
    # For every available interface on this system
    for interface in netifaces.interfaces():
        # If it has any IPv4 or IPv6 address (depending on ipversion) configured
        if ipversion in netifaces.ifaddresses(interface).keys():
            # For every configured IP address
            for addr in netifaces.ifaddresses(interface)[ipversion]:
                # Check if it matches to the address requested
                if addr['addr'] == ipaddr:
                    return True

    return False

def get_config():
    tftpd = default_config_data
    conf = Config()
    if not conf.exists('service tftp-server'):
        return None
    else:
        conf.set_level('service tftp-server')

    if conf.exists('directory'):
        tftpd['directory'] = conf.return_value('directory')

    if conf.exists('allow-upload'):
        tftpd['allow_upload'] = True

    if conf.exists('port'):
        tftpd['port'] = conf.return_value('port')

    if conf.exists('listen-address'):
        for addr in conf.return_values('listen-address'):
            if (ipaddress.ip_address(addr).version == 4):
                tftpd['listen_ipv4'].append(addr)

            if (ipaddress.ip_address(addr).version == 6):
                tftpd['listen_ipv6'].append(addr)

    return tftpd

def verify(tftpd):
    # bail out early - looks like removal from running config
    if tftpd is None:
        return None

    # Configuring allowed clients without a server makes no sense
    if not tftpd['directory']:
        raise ConfigError('TFTP root directory must be configured!')

    if not (tftpd['listen_ipv4'] or tftpd['listen_ipv6']):
        raise ConfigError('TFTP server listen address must be configured!')

    for address in tftpd['listen_ipv4']:
        if not addrok(address, netifaces.AF_INET):
            raise ConfigError('TFTP server listen address "{0}" not configured on this system.'.format(address))

    for address in tftpd['listen_ipv6']:
        if not addrok(address, netifaces.AF_INET6):
            raise ConfigError('TFTP server listen address "{0}" not configured on this system.'.format(address))

    return None

def generate(tftpd):
    # bail out early - looks like removal from running config
    if tftpd is None:
        return None

    tmpl = jinja2.Template(config_tmpl)
    config_text = tmpl.render(tftpd)
    with open(config_file, 'w') as f:
        f.write(config_text)

    return None

def apply(tftpd):
    if tftpd is not None:

        tftp_root = tftpd['directory']
        if not os.path.exists(tftp_root):
            os.makedirs(tftp_root)
            os.chmod(tftp_root, stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)
            # get UNIX uid for user 'tftp'
            tftp_uid = pwd.getpwnam('tftp').pw_uid
            os.chown(tftp_root, tftp_uid, -1)

        os.system('sudo systemctl restart tftpd-hpa.service')
    else:
        # TFTP server support is removed in the commit
        os.system('sudo systemctl stop tftpd-hpa.service')
        os.unlink(config_file)

    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        sys.exit(1)
