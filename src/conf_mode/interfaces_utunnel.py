#!/usr/bin/env python3
#
# Copyright (C) 2018-2024 yOS maintainers and contributors
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

from sys import exit

from vyos.config import Config
from vyos.configdict import get_interface_dict
from vyos.configdict import is_node_changed
from vyos.configverify import verify_address
from vyos.ifconfig import Interface
from vyos.ifconfig import CustomTunnelIf
from vyos.utils.dict import dict_search
from vyos.utils.network import get_interface_config
from vyos.utils.network import interface_exists
from vyos import ConfigError
from vyos import airbag
airbag.enable()


def get_config(config=None):
    """
    Retrive CLI config as dictionary. Dictionary can never be empty, as at least
    the interface name will be added or a deleted flag
    """
    if config:
        conf = config
    else:
        conf = Config()
    base = ['interfaces', 'utunnel']
    ifname, utunnel = get_interface_dict(conf, base)

    return utunnel


def verify(utunnel):
    if 'deleted' in utunnel:
        return None

    verify_address(utunnel)

    # todo: if tunnel_type has no related yaml definitions, throws a warning

    return None


def generate(utunnel):
    return None


def apply(utunnel):
    interface = utunnel['ifname']

    intf = CustomTunnelIf(**utunnel)

    if 'disable' in utunnel or 'deleted' in utunnel:
        # WireGuard only supports peer removal based on the configured public-key,
        # by deleting the entire interface this is the shortcut instead of parsing
        # out all peers and removing them one by one.
        #
        # Peer reconfiguration will always come with a short downtime while the
        # WireGuard interface is recreated (see below)

        # call stop script
        intf.operational.stop()
        return None

    # for custom tunnels, if manage-type is external, nothing need to be done.
    # tun.update(utunnel)
    # Users should manage external programs by systemd
    # intf.operational.start()

    return None


if __name__ == '__main__':
    try:
        c = get_config()
        generate(c)
        verify(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)
