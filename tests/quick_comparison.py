import os
import re

folder1_path = 'OldOutput'
folder2_path = 'NewOutput'
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

print("\n".join(different_files))
print(len(different_files))
