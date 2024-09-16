import json
import os
import unittest
from os.path import isfile, join

old_directory: str = "OldOutput"
new_directory: str = "NewOutput"
current_test_file = ""
files_affected = []


def extract_study_references(study_json):
    references = []
    altered_study_json = study_json
    if altered_study_json["documents"][0]["passages"]:
        altered_study_json["documents"][0]["passages"] = [
            x for x in study_json["documents"][0]["passages"] if
            "infons" in x.keys() and x["infons"]["iao_id_1"] != "IAO:0000320"
        ]
        references = [x for x in study_json["documents"][0]["passages"] if
                      "infons" in x.keys() and x["infons"]["iao_id_1"] == "IAO:0000320"]
    return altered_study_json, references


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

    def _test_references(self, old_refs, new_refs):
        try:
            self.assertEqual(old_refs, new_refs)
            return True, None
        except AssertionError as ae:
            files_affected.append(F"{current_test_file}")
            return False, ae

    def _test_bioc_content(self, old_article, new_article):
        try:
            self.assertDictEqual(old_article, new_article)
            return True, None
        except AssertionError as ae:
            files_affected.append(F"{current_test_file}")
            return False, ae

    def _test_article_keys(self, old_keys, new_keys):
        try:
            self.assertEqual(old_keys, new_keys)
            return True, None
        except AssertionError as ae:
            files_affected.append(F"{current_test_file}")
            return False, ae

    def test_study_differences(self):
        global current_test_file
        for old_file in os.listdir(old_directory):
            if not isfile(join(old_directory, old_file)):
                continue
            current_test_file = old_file
            with open(join(old_directory, old_file), "r", encoding="utf-8") as old_file_content, \
                    open(join(new_directory, old_file), "r", encoding="utf-8") as new_file_content:
                old_json = json.load(old_file_content)
                new_json = json.load(new_file_content)
                try:
                    del old_json["date"]
                    for i in range(len(old_json["documents"])):
                        if "inputFile" in old_json["documents"][i].keys():
                            del old_json["documents"][i]["inputFile"]
                        else:
                            del old_json["documents"][i]["inputfile"]
                except KeyError as ke:
                    print(F"The old version of {old_file} is missing the following key: {ke}\n\n")
                    continue
                try:
                    del new_json["date"]
                    for i in range(len(old_json["documents"])):
                        del new_json["documents"][i]["inputfile"]
                except KeyError as ke:
                    print(F"The new version of {old_file} is missing the following key: {ke}\n\n")
                    continue
                old_keys = sorted(old_json.keys())
                new_keys = sorted(new_json.keys())
                old_json, old_references = extract_study_references(old_json)
                new_json, new_references = extract_study_references(new_json)
                keys_match, keys_msg = self._test_article_keys(old_keys, new_keys)
                content_match, content_msg = self._test_bioc_content(old_json, new_json)
                reference_match, ref_msg = self._test_references(old_references, new_references)
                try:
                    assert keys_match
                    assert content_match
                    assert reference_match
                except AssertionError as ae:
                    continue
        if files_affected:
            raise AssertionError(F"{len(files_affected)} files have different contents:\n" + "\n".join(files_affected))


if __name__ == '__main__':
    unittest.main()
