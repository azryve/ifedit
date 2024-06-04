def create_interfaces_file(tmp_path, filename, content):
    path = tmp_path / filename
    path.write_text(content)
    return path


def create_test_file(tmp_path, content):
    return create_interfaces_file(tmp_path, "testfile.txt", content)


def read_all(file_path):
    with open(file_path, "r") as file:
        return file.readlines()
