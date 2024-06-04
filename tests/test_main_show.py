import sys
import subprocess

from textwrap import dedent

import ifedit
from conftest import create_interfaces_file


def test_show_options(tmp_path):
    interfaces_d = tmp_path / "interfaces.d"
    interfaces_d.mkdir()
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            f"iface eth0 inet static\nsource {interfaces_d}/*.intf\n",
        )
    )
    intf1 = str(
        create_interfaces_file(
            interfaces_d, "01.intf", "iface eth1 inet dhcp\n    mtu 1500\n"
        )
    )
    intf2 = str(
        create_interfaces_file(
            interfaces_d, "02.intf", "iface eth2 inet dhcp\npost-up false"
        )
    )

    output = subprocess.check_output(
        [sys.executable, ifedit.__file__, "show", "eth1", "eth2", "-f", main_conf]
    )
    assert output.decode() == dedent(
        """\
        iface eth1 inet dhcp
            mtu 1500
        iface eth2 inet dhcp
            post-up false
        """
    )
