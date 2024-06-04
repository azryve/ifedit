import sys
import subprocess

import pytest

import ifedit
from conftest import create_interfaces_file


def test_unset_option(tmp_path):
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
        create_interfaces_file(interfaces_d, "02.intf", "iface eth2 inet dhcp\n")
    )

    subprocess.check_call(
        [sys.executable, ifedit.__file__, "unset", "eth1", "mtu", "-f", main_conf]
    )
    assert (
        open(main_conf).read()
        == f"iface eth0 inet static\nsource {interfaces_d}/*.intf\n"
    )
    assert open(intf1).read() == "iface eth1 inet dhcp\n"
    assert open(intf2).read() == "iface eth2 inet dhcp\n"


def test_unset_option_not_found(tmp_path):
    interfaces_d = tmp_path / "interfaces.d"
    interfaces_d.mkdir()
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            f"iface eth0 inet static\n",
        )
    )
    with pytest.raises(subprocess.CalledProcessError) as exc:
        subprocess.check_call(
            [sys.executable, ifedit.__file__, "unset", "eth0", "mtu", "-f", main_conf]
        )
    assert exc.value.returncode == 1
