import re
from pathlib import Path

folder1_path = Path('OldOutput')
folder2_path = Path('NewOutput')
lines_to_ignore = ["\"date\":", "\"offset\":", "\"inputfile\":"]

different_files = []

for folder1_file_path in folder1_path.rglob('*'):
    if "_bioc" not in folder1_file_path.name:
        continue
    folder2_file_path = folder2_path / folder1_file_path.name
    if folder2_file_path.exists():
        with open(folder1_file_path, 'r') as f1, open(folder2_file_path, 'r') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
            different_lines = [
                i for i, (line1, line2) in enumerate(zip(lines1, lines2))
                if re.sub(r"\s+", "", line1, flags=re.UNICODE) != re.sub(r"\s+", "", line2, flags=re.UNICODE) and
                not [x for x in lines_to_ignore if x in line1]
            ]
            false_positives = different_lines
            different_lines = []
            for i in range(len(false_positives)):
                if "[PMC free article]" not in lines1[false_positives[i]] and "[PMC free article]" in lines2[false_positives[i]]:
                    continue
                else:
                    different_lines.append(false_positives[i])

            if different_lines:
                different_files.append(folder1_file_path.name)

print("\n".join(different_files))
print(len(different_files))
