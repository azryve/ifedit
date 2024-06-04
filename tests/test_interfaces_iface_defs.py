import pytest
from ifedit import *
from textwrap import dedent
from conftest import create_interfaces_file


def test_single_eth0(tmp_path):
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            dedent("""\
                source *.intf

                auto eth0
                iface eth0
            """),
        )
    )
    result = list(interfaces_declarations(main_conf))
    assert result == [
        IfaceDeclaration(
            name="eth0",
            section="",
            options=[],
            file=main_conf,
            lineno=3,
            offset=25,
        )
    ]


def test_single_eth0_eth1(tmp_path):
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            dedent("""\
                source *.intf

                auto eth0
                iface eth0 inet dhcp

                auto eth1
                iface eth1 inet dhcp
            """),
        )
    )
    result = list(interfaces_declarations(main_conf))
    assert result == [
        IfaceDeclaration(
            name="eth0",
            section="inet dhcp",
            options=[],
            file=main_conf,
            lineno=3,
            offset=25,
        ),
        IfaceDeclaration(
            name="eth1",
            section="inet dhcp",
            options=[],
            file=main_conf,
            lineno=6,
            offset=57,
        ),
    ]


def test_single_eth0_no_auto(tmp_path):
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            dedent("""\
                source *.intf

                # we do not care about auto
                iface eth0 inet dhcp
            """),
        )
    )
    result = list(interfaces_declarations(main_conf))
    assert result == [
        IfaceDeclaration(
            name="eth0",
            section="inet dhcp",
            file=main_conf,
            options=[],
            lineno=3,
            offset=43,
        ),
    ]


def test_muti_eth0(tmp_path):
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            dedent("""\
                source *.intf

                iface eth0 inet dhcp
                
                auto eth0
                iface eth0 inet6 static 
            """),
        )
    )
    result = list(interfaces_declarations(main_conf))
    assert result == [
        IfaceDeclaration(
            name="eth0",
            section="inet dhcp",
            options=[],
            file=main_conf,
            lineno=2,
            offset=15,
        ),
        IfaceDeclaration(
            name="eth0",
            section="inet6 static",
            options=[],
            file=main_conf,
            lineno=5,
            offset=47,
        ),
    ]


def test_single_eth0_utf8(tmp_path):
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            dedent("""\
                source *.intf

                # テストコメント
                auto eth0
                iface eth0
            """),
        )
    )
    result = list(interfaces_declarations(main_conf))
    assert result == [
        IfaceDeclaration(
            name="eth0",
            section="",
            options=[],
            file=main_conf,
            lineno=4,
            offset=49,
        )
    ]


def test_single_eth0_with_address(tmp_path):
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            """\
source *.intf

auto eth0
iface eth0 inet static
    address 10.0.0.100/24
    gateway 10.0.0.1
""",
        )
    )
    result = list(interfaces_declarations(main_conf))
    assert result == [
        IfaceDeclaration(
            name="eth0",
            section="inet static",
            options=[
                IfaceDeclarationOptions(
                    name="address",
                    value="10.0.0.100/24",
                    offset=48,
                    lineno=4,
                ),
                IfaceDeclarationOptions(
                    name="gateway",
                    value="10.0.0.1",
                    offset=74,
                    lineno=5,
                ),
            ],
            file=main_conf,
            lineno=3,
            offset=25,
        )
    ]


def test_single_eth0_empty_lines(tmp_path):
    conf_content = """\
source *.intf

auto eth0
iface eth0 inet static
                        
    address 10.0.0.100/24
    

    gateway 10.0.0.1
"""
    main_conf = str(
        create_interfaces_file(
            tmp_path,
            "interfaces",
            conf_content,
        )
    )
    result = list(interfaces_declarations(main_conf))
    assert result == [
        IfaceDeclaration(
            name="eth0",
            section="inet static",
            options=[
                IfaceDeclarationOptions(
                    name="address",
                    value="10.0.0.100/24",
                    offset=73,
                    lineno=5,
                ),
                IfaceDeclarationOptions(
                    name="gateway",
                    value="10.0.0.1",
                    offset=105,
                    lineno=8,
                ),
            ],
            file=main_conf,
            lineno=3,
            offset=25,
        )
    ]
