#!/usr/bin/env python3
#
# Copyright (C) 2023 VyOS maintainers and contributors
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

import argparse
import glob
import os
import sys
from pathlib import Path

directory = '/config/utunnels/'
pattern = os.path.join(directory, '*.yaml')

parser = argparse.ArgumentParser(description='list available custom tunnel types')


def get_custom_tunnel_types() -> list[str]:
    types = []
    for file_path in glob.glob(pattern):
        basename = Path(file_path).stem
        types.append(basename)

    return sorted(types)


if __name__ == '__main__':
    args = parser.parse_args()
    print("\n".join(get_custom_tunnel_types()))
    sys.exit(0)
