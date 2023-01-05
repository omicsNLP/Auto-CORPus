import json
import os
import unittest
from os.path import isfile, join

old_directory: str = "OldOutput"
new_directory: str = "NewOutput"


class FileDifferences(unittest.TestCase):

    def test_files_exist(self):
        files_affected = []
        for old_file in os.listdir(old_directory):
            try:
                self.assertTrue(old_file in os.listdir(new_directory))
            except AssertionError as ae:
                files_affected.append(old_file)
        if files_affected:
            raise AssertionError(
                F"{len(files_affected)} are missing from the new output:\n" + "\n".join(files_affected))

    def test_object_differences(self):
        files_affected = []
        for old_file in os.listdir(old_directory):
            if not isfile(join(old_directory, old_file)):
                continue
            with open(join(old_directory, old_file), "r", encoding="utf-8") as old_file_content, \
                    open(join(new_directory, old_file), "r", encoding="utf-8") as new_file_content:
                old_json = json.load(old_file_content)
                new_json = json.load(new_file_content)
                try:
                    del old_json["date"]
                    if "inputFile" in old_json["documents"][0].keys():
                        del old_json["documents"][0]["inputFile"]
                    else:
                        del old_json["documents"][0]["inputfile"]
                except KeyError as ke:
                    print(F"The old version of {old_file} is missing the following key: {ke}\n\n")
                    continue
                try:
                    del new_json["date"]
                    del new_json["documents"][0]["inputfile"]
                except KeyError as ke:
                    print(F"The new version of {old_file} is missing the following key: {ke}\n\n")
                    continue
                old_keys = sorted(old_json.keys())
                new_keys = sorted(new_json.keys())
                try:
                    self.assertEqual(old_keys, new_keys)
                    self.assertDictEqual(old_json, new_json)
                except AssertionError as ae:
                    files_affected.append(F"{old_file}")
        if files_affected:
            raise AssertionError(F"{len(files_affected)} files have different contents:\n" + "\n".join(files_affected))


if __name__ == '__main__':
    unittest.main()
