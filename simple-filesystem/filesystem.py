from typing import Any, Dict, List, Optional

# Create simple filesystem commands

# My failed attempt to get recursive typing to work with mypy
# See issue: https://github.com/python/mypy/issues/731
# T = TypeVar('T')
# DF = Mapping[str, Union[str, T]]
# Mapping[str, Union[str, Mapping[str, Union[str, Mapping[str, Union[str, Any]]]]]]

# A dictionary of dictionaries
filestore: Dict[str, Any] = dict()


def mkdir(path: str):
    global filestore
    leaf_dir = filestore
    directories = [d for d in path.split("/") if d != ""]
    for d in directories:
        if type(leaf_dir.get(d)) == dict:
            leaf_dir = leaf_dir[d]
        else:
            leaf_dir[d] = dict()
            leaf_dir = leaf_dir[d]
    return filestore


def list_files(path: str) -> Optional[List[str]]:
    leaf_dir = filestore
    directories = [d for d in path.split("/") if d != ""]
    for d in directories:
        if type(leaf_dir.get(d)) == dict:
            leaf_dir = leaf_dir[d]

    if leaf_dir:
        list_of_files: List[str] = []
        for k in leaf_dir:
            if type(leaf_dir[k]) == dict:
                list_of_files.append(f"dir {k}")
            else:
                list_of_files.append(f"fil {k}")
        return list_of_files
    return None


def get_file(path: str) -> Optional[str]:
    leaf_dir = filestore
    directories = [d for d in path.split("/") if d != ""]
    for d in directories:
        if type(leaf_dir.get(d)) == dict:
            leaf_dir = leaf_dir[d]
        else:
            return leaf_dir.get(d)
    return None


def write_file(path: str, data: str) -> Optional[str]:
    leaf_dir = filestore
    directories = [d for d in path.split("/") if d != ""]
    for d in directories:
        if type(leaf_dir.get(d)) == dict:
            leaf_dir = leaf_dir[d]
        else:
            leaf_dir[d] = data
            return data
    return None


i = 0


def p(i: int, thing: Any):
    print(f"{i} {thing}")


p(1, mkdir("/"))
p(2, mkdir("/a"))
p(3, list_files("/"))
p(4, mkdir("/a/b"))
p(5, list_files("/a"))
p(6, mkdir("/a/b/c"))
p(7, mkdir("/a/b/c/d/e/f/g"))
p(8, list_files("/a/b/c"))
p(9, list_files("/a/b/c/d"))

# File tests
print("\nFile tests")
p(1, write_file("/a/b/c", "c-stuff"))
p(2, write_file("/a/b/c/d/e", "e-stuff"))

p(3, write_file("/a/b/c/d-file", "d-things"))
p(4, get_file("/a/b/c/d-file"))
p(5, list_files("/a/b/c"))

p(6, get_file("/a/b/c/d/e"))
p(7, get_file("/a/b/c/d"))
p(8, get_file("/a/b/c"))
