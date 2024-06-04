from textwrap import dedent
from conftest import create_test_file
from ifedit import *


def test_eth0_add_mtu(tmp_path):
    main_conf = str(
        create_test_file(
            tmp_path,
            dedent("""\
            source *.intf

            auto eth0
            iface eth0
                address 10.1.1.1
            """),
        )
    )
    interfaces_file_add_iface_option(
        main_conf,
        IfaceOptionRequest("eth0", "mtu"),
        "1500",
    )
    assert open(main_conf).read() == dedent("""\
        source *.intf

        auto eth0
        iface eth0
            address 10.1.1.1
            mtu 1500
    """)


def test_eth0_add_mtu(tmp_path):
    main_conf = str(
        create_test_file(
            tmp_path,
            dedent("""\
            source *.intf

            auto eth0
            iface eth0
            """),
        )
    )
    interfaces_file_add_iface_option(
        main_conf,
        IfaceOptionRequest("eth0", "mtu"),
        "1500",
    )
    assert open(main_conf).read() == dedent("""\
        source *.intf

        auto eth0
        iface eth0
            mtu 1500
    """)


def test_eth0_add_multiple(tmp_path):
    main_conf = str(
        create_test_file(
            tmp_path,
            dedent("""\
            source *.intf

            auto eth0
            iface eth0
                address 10.1.1.1
            iface eth0
                gateway 10.1.1.254
            """),
        )
    )
    interfaces_file_add_iface_option(
        main_conf,
        IfaceOptionRequest("eth0", "mtu"),
        "1500",
    )
    assert open(main_conf).read() == dedent("""\
            source *.intf

            auto eth0
            iface eth0
                address 10.1.1.1
            iface eth0
                gateway 10.1.1.254
                mtu 1500
    """)


def test_eth0_add_duplicate(tmp_path):
    main_conf = str(
        create_test_file(
            tmp_path,
            dedent("""\
            source *.intf

            auto eth0
            iface eth0
                post-up true
                address 10.1.1.1
            """),
        )
    )
    interfaces_file_add_iface_option(
        main_conf,
        IfaceOptionRequest("eth0", "post-up"),
        "false",
    )
    assert open(main_conf).read() == dedent("""\
            source *.intf

            auto eth0
            iface eth0
                post-up true
                post-up false
                address 10.1.1.1
    """)
