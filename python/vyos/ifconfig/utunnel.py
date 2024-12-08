# Copyright 2019-2021 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.
import glob
import os
from pathlib import Path
import yaml

from vyos.ifconfig import Interface
from vyos.ifconfig import Operational

utunnel_config_directory = '/config/utunnels/'


def get_utunnel_config(tunnel_type):
    config_file = os.path.join(utunnel_config_directory, '{}.yaml'.format(tunnel_type))

    config = {}
    if os.path.exists(config_file):
        config = yaml.safe_load(open(config_file))

    defaults = {
        'scripts': {
            'start': '',
            'stop': '',
            'update': '',
            'status': '',
        },
    }
    defaults.update(config)

    return defaults


def get_custom_tunnel_types() -> list[str]:
    pattern = os.path.join(utunnel_config_directory, '*.yaml')

    types = []
    for file_path in glob.glob(pattern):
        basename = Path(file_path).stem
        types.append(basename)

    return sorted(types)


class CustomTunnelOperational(Operational):

    def get_tunnel_type(self):
        from vyos.config import Config

        c = Config()
        return c.return_effective_value(['interfaces', 'utunnel', self.config['ifname'], 'tunnel-type'])

    def start(self):
        config = get_utunnel_config(self.get_tunnel_type())
        if config['scripts']['start']:
            self._cmd(config['scripts']['start'].replace('{device}', self.ifname))

    def stop(self):
        config = get_utunnel_config(self.get_tunnel_type())
        if config['scripts']['stop']:
            self._cmd(config['scripts']['stop'].replace('{device}', self.ifname))

    def restart(self):
        self.stop()
        self.start()

    def update(self):
        config = get_utunnel_config(self.get_tunnel_type())
        if config['scripts']['update']:
            self._cmd(config['scripts']['update'].replace('{device}', self.ifname))

    def show_status(self):
        config = get_utunnel_config(self.get_tunnel_type())
        if config['scripts']['status']:
            print(self._cmd(config['scripts']['status'].replace('{device}', self.ifname)))


@Interface.register
class CustomTunnelIf(Interface):
    """
    A dummy interface for custom tunnels
    """

    OperationalClass = CustomTunnelOperational

    iftype = 'utunnel'
    definition = {
        **Interface.definition,
        **{
            'section': 'utunnel',
            'prefixes': ['utun', ],
            'eternal': 'utun[0-9]+$',
        },
    }

    def _create(self):
        # don't create this interface as it is managed outside
        pass

    def _delete(self):
        # don't create this interface as it is managed outside
        pass

    def get_mac(self):
        """ Get a synthetic MAC address. """
        return self.get_mac_synthetic()

    def update(self, config):
        # don't perform any update
        pass
