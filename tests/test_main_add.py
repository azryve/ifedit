import sys
import subprocess

import pytest

import ifedit
from conftest import create_interfaces_file


def test_add_option(tmp_path):
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
        create_interfaces_file(interfaces_d, "01.intf", "iface eth1 inet dhcp\n")
    )
    intf2 = str(
        create_interfaces_file(interfaces_d, "02.intf", "iface eth2 inet dhcp\n")
    )

    subprocess.check_call(
        [
            sys.executable,
            ifedit.__file__,
            "add",
            "eth1",
            "post-up",
            "true",
            "-f",
            main_conf,
        ]
    )
    subprocess.check_call(
        [
            sys.executable,
            ifedit.__file__,
            "add",
            "eth1",
            "post-up",
            "false",
            "-f",
            main_conf,
        ]
    )
    assert (
        open(main_conf).read()
        == f"iface eth0 inet static\nsource {interfaces_d}/*.intf\n"
    )
    assert (
        open(intf1).read()
        == "iface eth1 inet dhcp\n    post-up true\n    post-up false\n"
    )
    assert open(intf2).read() == "iface eth2 inet dhcp\n"


def test_add_option_iface_not_found(tmp_path):
    interfaces_d = tmp_path / "interfaces.d"
    interfaces_d.mkdir()
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            f"iface eth0 inet static\nsource {interfaces_d}/*.intf\n",
        )
    )
    with pytest.raises(subprocess.CalledProcessError) as exc:
        subprocess.check_call(
            [
                sys.executable,
                ifedit.__file__,
                "add",
                "eth1",
                "mtu",
                "1500",
                "-f",
                main_conf,
            ]
        )
    assert exc.value.returncode == 1
