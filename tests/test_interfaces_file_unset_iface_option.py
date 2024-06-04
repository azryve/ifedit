from textwrap import dedent
from conftest import create_test_file
from ifedit import *


def test_eth0_unset_mtu(tmp_path):
    main_conf = str(
        create_test_file(
            tmp_path,
            dedent("""\
            source *.intf

            auto eth0
            iface eth0
                mtu 1000
                address 10.1.1.1
            """),
        )
    )
    interfaces_file_unset_iface_option(main_conf, IfaceOptionRequest("eth0", "mtu"))
    assert open(main_conf).read() == dedent("""\
        source *.intf

        auto eth0
        iface eth0
            address 10.1.1.1
    """)


def test_eth0_unset_mtu_multiple(tmp_path):
    main_conf = str(
        create_test_file(
            tmp_path,
            dedent("""\
            source *.intf

            auto eth0
            iface eth0
                mtu 1000
            iface eth0
                mtu 1000
                address 10.1.1.1
            """),
        )
    )
    interfaces_file_unset_iface_option(main_conf, IfaceOptionRequest("eth0", "mtu"))
    assert open(main_conf).read() == dedent("""\
        source *.intf

        auto eth0
        iface eth0
        iface eth0
            address 10.1.1.1
    """)


def test_eth0_unset_skip(tmp_path):
    main_content = dedent("""\
        source *.intf

        auto eth0
        iface eth0
            mtu 1000
        iface eth0
            mtu 1000
            address 10.1.1.1
    """)
    main_conf = str(
        create_test_file(
            tmp_path,
            main_content,
        )
    )
    first_mtu = main_content.index("    mtu ")
    second_mtu = main_content.index("    mtu ", first_mtu)
    interfaces_file_unset_iface_option(
        main_conf,
        IfaceOptionRequest("eth0", "mtu"),
        second_mtu,
    )
    assert open(main_conf).read() == dedent("""\
        source *.intf

        auto eth0
        iface eth0
            mtu 1000
        iface eth0
            address 10.1.1.1
    """)
