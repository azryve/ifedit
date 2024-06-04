#!/usr/bin/env python3

import sys
import argparse
import glob
import dataclasses
import collections
from typing import Iterable, List, OrderedDict, Optional, Set


FileTreeT = OrderedDict[str, "FileTreeT"]


def interfaces_file_sources_tree(root_file: str) -> FileTreeT:
    """
    Reads root interfaces file and scans for 'source' directives.
    Returns a recursive ordered dictionary with the tree of includes.

    Example of /etc/network/interfaces:
        source /etc/network/interfaces.d/*.intf
        source /etc/network/interfaces.d/*-subifs.intf

    This would result in something like this:
    {
        "/etc/network/interfaces": {
            "/etc/network/interfaces.d/01.intf": {},
            "/etc/network/interfaces.d/02.intf": {},
            "/etc/network/interfaces.d/01-subifs.intf": {},
            "/etc/network/interfaces.d/02-subifs.intf": {},
        }
    }
    """

    def read_and_parse_source_lines(filename: str) -> dict:
        tree: FileTreeT = collections.OrderedDict()
        with open(filename, "r") as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if line.startswith("source "):
                    source_path_glob = line.split(maxsplit=1)[1]
                elif line.startswith("source-directory "):
                    source_path_glob = line.split(maxsplit=1)[1] + "/*"
                else:
                    continue
                # Using glob to resolve wildcard paths
                for inc_file in sorted(glob.glob(source_path_glob)):
                    # Recursively read each included file
                    tree[inc_file] = read_and_parse_source_lines(inc_file)
        return tree

    return collections.OrderedDict(
        [(root_file, read_and_parse_source_lines(root_file))]
    )


def walk_file_sources_tree(file_tree: FileTreeT) -> Iterable[str]:
    """
    Iterates over interfaces file tree.
    """
    for file_name in file_tree:
        yield file_name
        yield from walk_file_sources_tree(file_tree[file_name])


def walk_file_sources_tree_reversed(file_tree: FileTreeT) -> Iterable[str]:
    """
    Iterates over interfaces file tree.
    Goes in revere order of inclusion, starting with root file.
    """
    for file_name in reversed(file_tree):
        yield file_name
        yield from walk_file_sources_tree_reversed(file_tree[file_name])


@dataclasses.dataclass
class IfaceDeclarationOptions:
    """
    Points to specific option in 'iface <name> [section]' declaration block
    Args:
        name: name of option: address, gateway, post-up, etc.
        value: value of option
        file: file containing option
        offset: byte offset in file of start of line containing option
        lineno: line offset in file of file containing option (stats with 0)
    """

    name: str
    value: str
    offset: int
    lineno: int


@dataclasses.dataclass
class IfaceDeclaration:
    """
    Points to specific 'iface <name> [section]' declaration
    Args:
        name: name of interface
        section: may be empty
        file: file containing declaration
        offset: byte offset in file of where declaration contains
        lineno: line offset in file of where declaration contains (stats with 0)
    """

    name: str
    section: str
    options: List[IfaceDeclarationOptions]
    file: str
    offset: int
    lineno: int


def interfaces_declarations(file_path: str) -> Iterable[IfaceDeclaration]:
    """
    Reads interfaces file and returns iface block declarations

    Args:
        file (str): Path to the interfaces file.

    Yields:
        IfaceDeclaration: An instance for each 'iface <name>' declaration found.
    """
    with open(file_path, "rb") as fh:
        for lineno, line in enumerate(fh):
            if not line.startswith(b"iface "):
                continue

            section = b""
            _, name = line.split(maxsplit=1)
            if b" " in name:
                name, section = name.split(maxsplit=1)

            options = list(
                interfaces_options(
                    file_path,
                    lineno + 1,
                    fh.tell(),
                )
            )

            yield IfaceDeclaration(
                name=name.decode().strip(),
                section=section.decode().strip(),
                options=options,
                file=file_path,
                lineno=lineno,
                offset=fh.tell() - len(line),
            )


def interfaces_options(
    file_path: str, start_lineno: int, start_offset: int
) -> Iterable[IfaceDeclarationOptions]:
    """
    Reads interfaces file from current position
    and yields found IfaceDeclarationOptions
    until it encounters one of stop other keywords.

    Args:
        file (str): Path to the interfaces file.
        start_lineno (int): offset in file lines
        start_offset (int): offset in bytes of file

    Yields:
        IfaceDeclarationOptions: An instance for each option encountered
    """
    stop_keywords = (
        b"iface",
        b"mapping",
        b"auto",
        b"allow-",
        b"source",
        b"source-directory",
    )
    with open(file_path, "rb") as fh:
        fh.seek(start_offset)
        for lineno, line in enumerate(fh):
            if line.startswith(stop_keywords):
                break

            stripped = line.lstrip().rstrip(b"\n")
            name_value = stripped.split(b" ", maxsplit=1)
            if len(name_value) > 1:
                name, value = name_value
            else:
                name, value = name_value[0], b""

            # empty or whitespace-only string
            if name:
                yield IfaceDeclarationOptions(
                    name=name.decode(),
                    value=value.decode(),
                    offset=fh.tell() - len(line),
                    lineno=start_lineno + lineno,
                )


def file_insert_line(file: str, offset: int, line: str) -> None:
    """
    Inserts line at specified position in file.
    Assumes that file is utf8-encoded.

    Args:
        file (str): Path to the edited file.
        offset (int): byte offset in file
        line (int): inserted line.
    """
    chunk = line.encode()
    chunklen = max(len(chunk), 4096)
    with open(file, "r+b") as fh:
        # move to target position
        fh.seek(offset)
        # save current content
        # write inserted line
        next_chunk = fh.peek(chunklen)
        fh.write(chunk)

        # write chunks until the eof encontered
        chunk = next_chunk
        while len(chunk) == chunklen:
            next_chunk = fh.peek(chunklen)
            fh.write(chunk)
            chunk = next_chunk

        # write the tail end of the file
        fh.write(chunk)


def file_remove_line(file: str, offset: int) -> None:
    """
    Removes line from the file and inserts a new one.

    Args:
        file (str): Path to the edited file.
        offset (int): byte offset in file.
        maxlen (int): maximum len of replaced line (including newline symobol).
        line (int): inserted line.
    """
    chunklen = 4096
    with open(file, "rb") as rfh:
        with open(file, "r+b") as wfh:
            # move to target position
            rfh.seek(offset)
            wfh.seek(offset)
            # skip replaced string
            rfh.readline()
            # copy file until the end
            chunk = rfh.read(chunklen)
            while len(chunk) == chunklen:
                wfh.write(chunk)
                chunk = rfh.read(chunklen)
            wfh.write(chunk)
            wfh.truncate()


def file_read_line(file: str, offset: int) -> str:
    """
    Reads a line from specific offset in the file.

    Args:
        file (str): Path to the edited file.
        offset (int): byte offset in file.
    """
    with open(file, "rb") as fh:
        fh.seek(offset)
        return fh.readline().decode()


def line_indent(line: str) -> str:
    """
    Returns indentation of a given line.

    Args:
        line (str): line to extract indentation from.
    """
    stripped = line.lstrip()
    return line[: len(line) - len(stripped)]


@dataclasses.dataclass
class IfaceOptionRequest:
    """
    Changes to specific option set or deletion
    Args:
        iface: name of interface
        option: name of option
    """

    iface: str
    option: str


def interfaces_file_unset_iface_option(
    file_path: str,
    opt_req: IfaceOptionRequest,
    skip_offset: Optional[int] = None,
) -> List[IfaceDeclarationOptions]:
    """
    Removes previous option declarations for specific interface.

    Args:
        file_path (str): path to the edited file.
        opt_req: (IfaceOptionRequest) iface option to remove.
    Returns:
        list of options that has been removed
    """
    ret: List[IfaceDeclarationOptions] = []
    decls = list(interfaces_declarations(file_path))
    for ifdecl in reversed(decls):
        if ifdecl.name != opt_req.iface:
            continue
        for opt in ifdecl.options:
            if opt.name != opt_req.option:
                continue
            if skip_offset == opt.offset:
                continue
            file_remove_line(file_path, opt.offset)
            ret.append(opt)
    return ret


def interfaces_file_add_iface_option(
    file_path: str,
    opt_req: IfaceOptionRequest,
    value: str,
) -> Optional[int]:
    """
    Adds an option with specific value to iface declaration.
    If this value is already present then adds it as the line following just that.
    If not then adds the value.

    Args:
        file_path (str): path to the edited file.
        opt_req: (IfaceOptionRequest) iface option to add.
        value (str): value of the option.
    Returns:
        Byte offset of inserted option.
        If iface block not found returns None.
    """
    # set value only in the last definition
    # iterace in reverse to not mess up offsests
    decls = list(interfaces_declarations(file_path))
    current_opts = OrderedDict()
    target_decl = None
    for ifdecl in decls:
        if ifdecl.name != opt_req.iface:
            continue
        target_decl = ifdecl
        for opt in ifdecl.options:
            if opt.name in current_opts:
                del current_opts[opt.name]
            current_opts[opt.name] = opt

    # no iface declaration found
    if not target_decl:
        return None
    target_opt = None
    # option already present add right after it
    if opt_req.option in current_opts:
        target_opt = current_opts[opt_req.option]
    # append after any other option present
    elif current_opts:
        target_opt = list(current_opts.values())[-1]

    if target_opt:
        line = file_read_line(file_path, target_opt.offset)
        indent = line_indent(line)
        insert_offset = target_opt.offset + len(line.encode())
    else:
        indent = "    "  # default indentation
        line = file_read_line(file_path, target_decl.offset)
        insert_offset = target_decl.offset + len(line.encode())

    inserted_line = indent + opt_req.option + " " + value + "\n"
    file_insert_line(file_path, insert_offset, inserted_line)
    return insert_offset


def interfaces_file_set_iface_option(
    file_path: str,
    opt_req: IfaceOptionRequest,
    value: str,
) -> Optional[int]:
    """
    Sets option to a specified value.
    Removes all other instances of the same option.

    Args:
        file_path (str): path to the edited file.
        opt_req: (IfaceOptionRequest) iface option to set.
        value (str): value of the option.
    Returns:
        Byte offset of inserted option.
        If iface block not found returns None.
    """
    inserted_offset = interfaces_file_add_iface_option(file_path, opt_req, value)
    interfaces_file_unset_iface_option(
        file_path,
        opt_req,
        skip_offset=inserted_offset,
    )
    return inserted_offset


def set_mode_main(subparsers) -> None:
    """
    Scan all definitions of interface in root_file and included files.
    Removes all current values of the option and sets a new value in last position.
    """

    def func(args: argparse.Namespace) -> Optional[int]:
        root_file: str = args.root_file
        opt_req = IfaceOptionRequest(args.iface, args.option)
        value: str = args.value
        tree = interfaces_file_sources_tree(root_file)
        inserted = False
        for file_path in walk_file_sources_tree_reversed(tree):
            if not inserted:
                pos = interfaces_file_set_iface_option(
                    file_path,
                    opt_req,
                    value,
                )
                inserted |= pos is not None
            else:
                interfaces_file_unset_iface_option(
                    file_path,
                    opt_req,
                )
        if not inserted:
            return 1

    parser = subparsers.add_parser("set", help="set option for interface")
    parser.add_argument("iface", help="interface name to to edit")
    parser.add_argument("option", help="name of the option to edit")
    parser.add_argument("value", help="name of the option to edit")
    parser.set_defaults(func=func)
    add_common_flags(parser)


def unset_mode_main(subparsers) -> None:
    """
    Scan all definitions of interface in root_file and included files.
    Removes all current value for requested option.
    """

    def func(args: argparse.Namespace) -> Optional[int]:
        root_file: str = args.root_file
        opt_req = IfaceOptionRequest(args.iface, args.option)
        tree = interfaces_file_sources_tree(root_file)
        removed = []
        for file_path in walk_file_sources_tree_reversed(tree):
            removed.extend(
                interfaces_file_unset_iface_option(
                    file_path,
                    opt_req,
                )
            )
        if not removed:
            return 1

    parser = subparsers.add_parser("unset", help="removes option for interface")
    parser.add_argument("iface", help="interface name to to edit")
    parser.add_argument("option", help="name of the option to edit")
    parser.set_defaults(func=func)
    add_common_flags(parser)


def add_mode_main(subparsers) -> None:
    """
    Adds option to the interface.
    """

    def func(args: argparse.Namespace) -> Optional[int]:
        root_file: str = args.root_file
        opt_req = IfaceOptionRequest(args.iface, args.option)
        value: str = args.value
        tree = interfaces_file_sources_tree(root_file)
        for file_path in walk_file_sources_tree_reversed(tree):
            if interfaces_file_add_iface_option(file_path, opt_req, value):
                break
        else:
            return 1

    parser = subparsers.add_parser("add", help="adds option to the interface")
    parser.add_argument("iface", help="interface name to to edit")
    parser.add_argument("option", help="name of the option to edit")
    parser.add_argument("value", help="name of the option to edit")
    parser.set_defaults(func=func)
    add_common_flags(parser)


def show_mode_main(subparsers) -> None:
    """
    Shows options for the interface.
    """

    def func(args: argparse.Namespace) -> Optional[int]:
        root_file: str = args.root_file
        iface_names: Set[str] = set(args.iface)
        tree = interfaces_file_sources_tree(root_file)
        ifdecls: List[IfaceDeclaration] = []
        for file_path in walk_file_sources_tree(tree):
            for ifdecl in interfaces_declarations(file_path):
                if ifdecl.name in iface_names:
                    ifdecls.append(ifdecl)
        if not ifdecls:
            return 1
        for ifdecl in ifdecls:
            print("iface", ifdecl.name, ifdecl.section)
            for opt in ifdecl.options:
                print("    %s %s" % (opt.name, opt.value))

    parser = subparsers.add_parser("show", help="show all interfaces options")
    parser.add_argument("iface", nargs="+", help="interface names to to show options")
    parser.set_defaults(func=func)
    add_common_flags(parser)


def list_mode_main(subparsers) -> None:
    """
    Lists declared interfaces.
    """

    def func(args: argparse.Namespace) -> Optional[int]:
        root_file: str = args.root_file
        tree = interfaces_file_sources_tree(root_file)
        seen = set()
        for file_path in walk_file_sources_tree(tree):
            for ifdecl in interfaces_declarations(file_path):
                if ifdecl.name not in seen:
                    print(ifdecl.name)
                    seen.add(ifdecl.name)

    parser = subparsers.add_parser("list", help="lists declared interfaces")
    parser.set_defaults(func=func)
    add_common_flags(parser)


def add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-f",
        "--root-file",
        default="/etc/network/interfaces",
        help="main interfaces file",
    )


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    set_mode_main(subparsers)
    unset_mode_main(subparsers)
    add_mode_main(subparsers)
    show_mode_main(subparsers)
    list_mode_main(subparsers)
    args = parser.parse_args()

    if not args.func:
        parser.usage()
        return -1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
