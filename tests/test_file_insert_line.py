import pytest
from conftest import create_interfaces_file
from ifedit import *


def create_test_file(tmp_path, content):
    return create_interfaces_file(tmp_path, "testfile.txt", content)


def read_all(file_path):
    with open(file_path, "r") as file:
        return file.readlines()


def test_insert_line_mid_file(tmp_path):
    setup_file = create_test_file(tmp_path, "Line 1\nLine 2\nLine 3\n")
    file_insert_line(setup_file, len("Line 1\n"), "Inserted Line\n")
    assert read_all(setup_file) == [
        "Line 1\n",
        "Inserted Line\n",
        "Line 2\n",
        "Line 3\n",
    ]


def test_insert_line_start_file(tmp_path):
    setup_file = create_test_file(tmp_path, "Line 1\nLine 2\nLine 3\n")
    file_insert_line(setup_file, 0, "Start Line\n")
    assert read_all(setup_file) == [
        "Start Line\n",
        "Line 1\n",
        "Line 2\n",
        "Line 3\n",
    ]


def test_insert_line_end_file(tmp_path):
    setup_file = create_test_file(tmp_path, "Line 1\nLine 2\nLine 3\n")
    initial_content = read_all(setup_file)
    end_offset = sum(len(line) for line in initial_content)
    file_insert_line(setup_file, end_offset, "End Line\n")
    assert read_all(setup_file) == initial_content + ["End Line\n"]


def test_insert_line_large_file(tmp_path):
    large_file = create_test_file(tmp_path, "Line\n" * 1000)
    middle_offset = len("Line\n" * 500)
    file_insert_line(large_file, middle_offset, "Middle Line\n")
    content = read_all(large_file)
    assert content[500] == "Middle Line\n"
    assert len(content) == 1001
