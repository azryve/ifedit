import sys
import subprocess

from textwrap import dedent

import ifedit
from conftest import create_interfaces_file


def test_list(tmp_path):
    interfaces_d = tmp_path / "interfaces.d"
    interfaces_d.mkdir()
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            f"iface eth0 inet static\nsource {interfaces_d}/*.intf\n",
        )
    )
    create_interfaces_file(interfaces_d, "01.intf", "iface eth1 inet dhcp\n")
    create_interfaces_file(interfaces_d, "02.intf", "iface eth2 inet dhcp\n")

    output = subprocess.check_output(
        [sys.executable, ifedit.__file__, "list", "-f", main_conf]
    )
    assert output.decode() == dedent(
        """\
        eth0
        eth1
        eth2
        """
    )


def test_list_dups(tmp_path):
    interfaces_d = tmp_path / "interfaces.d"
    interfaces_d.mkdir()
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            f"iface eth0 inet static\nsource {interfaces_d}/*.intf\niface eth0 inet6 static",
        )
    )
    create_interfaces_file(interfaces_d, "01.intf", "iface eth1 inet dhcp\n")
    create_interfaces_file(interfaces_d, "02.intf", "iface eth2 inet dhcp\n")

    output = subprocess.check_output(
        [sys.executable, ifedit.__file__, "list", "-f", main_conf]
    )
    assert output.decode() == dedent(
        """\
        eth0
        eth1
        eth2
        """
    )
