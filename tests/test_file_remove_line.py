from conftest import create_interfaces_file, create_test_file, read_all
from ifedit import *


def test_file_remove_first_line(tmp_path):
    setup_file = create_test_file(tmp_path, "Line 1\nLine 2\nLine 3\n")
    file_remove_line(setup_file, 0)
    assert read_all(setup_file) == [
        "Line 2\n",
        "Line 3\n",
    ]


def test_file_remove_middle_line(tmp_path):
    setup_file = create_test_file(tmp_path, "Line 1\nLine 2\nLine 3\n")
    file_remove_line(setup_file, len("Line 2\n"))
    assert read_all(setup_file) == [
        "Line 1\n",
        "Line 3\n",
    ]


def test_file_remove_end_line(tmp_path):
    setup_file = create_test_file(tmp_path, "Line 1\nLine 2\nLine 3\n")
    file_remove_line(setup_file, len("Line 1\nLine 2\n"))
    assert read_all(setup_file) == [
        "Line 1\n",
        "Line 2\n",
    ]


def test_file_remove_not_full_line(tmp_path):
    setup_file = create_test_file(tmp_path, "Line 1\nLine 2\nLine 3\n")
    file_remove_line(setup_file, 5)
    assert read_all(setup_file) == [
        "Line Line 2\n",
        "Line 3\n",
    ]


def test_file_remove_empty_line(tmp_path):
    setup_file = create_test_file(tmp_path, "Line 1\n\nLine 2\nLine 3\n")
    file_remove_line(setup_file, len("Line 1\n"))
    assert read_all(setup_file) == [
        "Line 1\n",
        "Line 2\n",
        "Line 3\n",
    ]
