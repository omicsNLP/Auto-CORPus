import os
import re

import pytest


def compare_files(folder1_path, folder2_path):
    lines_to_ignore = ["\"date\":", "\"offset\":", "\"inputfile\":"]
    different_files = []

    for root, dirs, files in os.walk(folder1_path):
        for filename in files:
            if "_bioc" not in filename:
                continue
            folder1_file_path = os.path.join(root, filename)
            folder2_file_path = os.path.join(folder2_path, filename)
            if os.path.exists(folder2_file_path):
                with open(folder1_file_path, 'r') as f1, open(folder2_file_path, 'r') as f2:
                    lines1 = f1.readlines()
                    lines2 = f2.readlines()
                    different_lines = [i for i, (line1, line2) in enumerate(zip(lines1, lines2)) if
                                       re.sub(r"\s+", "", line1, flags=re.UNICODE) != re.sub(r"\s+", "", line2,
                                                                                             flags=re.UNICODE) and
                                       not [x for x in lines_to_ignore if x in line1]]
                    false_positives = different_lines
                    different_lines = []
                    for i in range(len(false_positives)):
                        if "[PMC free article]" not in lines1[false_positives[i]] and "[PMC free article]" in lines2[
                            false_positives[i]]:
                            continue
                        else:
                            different_lines.append(false_positives[i])

                    if different_lines:
                        different_files.append(filename)
    if different_files:
        print("\n".join(different_files))
        print(len(different_files))
    return different_files


@pytest.fixture
def new_output_path():
    return "NewOutput"


@pytest.fixture
def old_output_path():
    return "OldOutput"


def test_new_output_exists(new_output_path):
    assert os.path.exists(new_output_path)


def test_old_output_exists(old_output_path):
    assert os.path.exists(old_output_path)


def test_compare_files(new_output_path, old_output_path):
    """
    Comparison of the new build's output BioC files against the last working version (old output).
    Failing this test could be expected if intended changes to the output files are made, so check the
    printed log messages for this test and look manually at any differences.
    """
    assert compare_files(old_output_path, new_output_path) == []
