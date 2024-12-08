#!/usr/bin/env python3
#
# Copyright (C) 2022-2023 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import typing

import vyos.opmode

from vyos.ifconfig import CustomTunnelIf
from vyos.configquery import ConfigTreeQuery


def _verify(func):
    """Decorator checks if WireGuard interface config exists"""
    from functools import wraps

    @wraps(func)
    def _wrapper(*args, **kwargs):
        config = ConfigTreeQuery()
        interface = kwargs.get('interface')
        if not config.exists(['interfaces', 'utunnel', interface]):
            unconf_message = f'Custom Tunnel interface {interface} is not configured'
            raise vyos.opmode.UnconfiguredSubsystem(unconf_message)
        return func(*args, **kwargs)

    return _wrapper


@_verify
def restart(raw: bool, interface: str):
    intf = CustomTunnelIf(interface)
    return intf.operational.restart()


@_verify
def show_status(raw: bool, interface: str):
    intf = CustomTunnelIf(interface)
    return intf.operational.show_status()


if __name__ == '__main__':
    try:
        res = vyos.opmode.run(sys.modules[__name__])
        if res:
            print(res)
    except (ValueError, vyos.opmode.Error) as e:
        print(e)
        sys.exit(1)
