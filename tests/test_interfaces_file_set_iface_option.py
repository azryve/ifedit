from textwrap import dedent
from conftest import create_test_file
from ifedit import *


def test_eth0_set_option_value(tmp_path):
    main_conf = str(
        create_test_file(
            tmp_path,
            dedent("""\
            source *.intf

            auto eth0
            iface eth0
                address 10.1.1.1
                gateway 10.1.1.254
            """),
        )
    )
    interfaces_file_set_iface_option(
        main_conf,
        IfaceOptionRequest("eth0", "address"),
        "10.1.1.2",
    )
    assert open(main_conf).read() == dedent("""\
            source *.intf

            auto eth0
            iface eth0
                address 10.1.1.2
                gateway 10.1.1.254
    """)
