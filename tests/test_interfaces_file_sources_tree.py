from ifedit import interfaces_file_sources_tree
from conftest import create_interfaces_file


def test_single_source_file(tmp_path):
    main_conf = str(
        create_interfaces_file(
            tmp_path, "interfaces", "iface eth0 inet static\nsource *.intf\n"
        )
    )
    result = interfaces_file_sources_tree(str(main_conf))
    assert result
    assert main_conf in result
    assert len(result[main_conf]) == 0


def test_no_source_files(tmp_path):
    main_conf = str(
        create_interfaces_file(tmp_path, "interfaces", "iface eth0 inet static\n")
    )
    result = interfaces_file_sources_tree(str(main_conf))
    assert result == {main_conf: {}}


def test_multiple_source_directives(tmp_path):
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

    result = interfaces_file_sources_tree(str(main_conf))
    assert result
    assert main_conf in result
    assert len(result[main_conf]) == 2
    assert intf1 in result[main_conf]
    assert intf2 in result[main_conf]


def test_source_directory(tmp_path):
    interfaces_d = tmp_path / "interfaces.d"
    interfaces_d.mkdir()
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            f"iface eth0 inet static\nsource-directory {interfaces_d}\n",
        )
    )
    intf1 = str(
        create_interfaces_file(interfaces_d, "01.intf", "iface eth1 inet dhcp\n")
    )
    intf2 = str(
        create_interfaces_file(interfaces_d, "02.intf", "iface eth2 inet dhcp\n")
    )

    result = interfaces_file_sources_tree(str(main_conf))
    assert result
    assert main_conf in result
    assert len(result[main_conf]) == 2
    assert intf1 in result[main_conf]
    assert intf2 in result[main_conf]
