from datetime import datetime
from operator import itemgetter
from pathlib import Path

import cv2
import pytesseract


class TableImage:
    def img2text(self, img, x, y, w, h):
        """Function: translate image into texts
        Input: original image, and location of text boxes
        Output: extracted texts
        """
        roi = img[y - 3 : (y + h + 6), x - 3 : (x + w + 6)]

        # change the 'lang' here for different traineddata
        text = pytesseract.image_to_string(
            roi, lang=self.trainedData, config="--psm 6 --oem 3"
        ).strip()
        new_text = text.replace("\n", " ")
        return new_text

    def rm_lines(self, img):
        """Function: remove all the horizontal and vertical lines in image and binary it
        Input: original image
        Output: image after preprocessing
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            ~gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, -5
        )
        rows, cols = binary.shape

        # detect horizontal lines
        scale = 40
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (cols // scale, 1))
        eroded = cv2.erode(binary, kernel, iterations=1)
        dilatedcol = cv2.dilate(eroded, kernel, iterations=2)

        # detect vertical lines
        scale = 20
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, rows // scale))
        eroded = cv2.erode(binary, kernel, iterations=1)
        dilatedrow = cv2.dilate(eroded, kernel, iterations=2)

        # merge two groups of lines
        merge = cv2.add(dilatedcol, dilatedrow)
        after = cv2.add(gray, merge)

        return after

    def find_cells(self, img):
        """Function: find cells in table images and sort them from top-left to bottom-right
        Input: original image
        Output: ordered table cells, and processed image
        """
        added = cv2.copyMakeBorder(
            img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255]
        )
        size = added.shape
        gray = self.rm_lines(img)
        ret, thresh = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY)

        rows, cols = thresh.shape
        scale = 150  # the larger, the rectangles smaller

        # the second parameter of kernel and morphology iterations /
        # need to be fine-tuned according to the image size
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (cols // scale, rows // scale + 2)
        )

        # Another method for erosion
        eroded = cv2.erode(thresh, kernel, iterations=3)

        # Add white borders before finding contours
        eroded = cv2.copyMakeBorder(
            eroded, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255]
        )
        thresh = cv2.copyMakeBorder(
            thresh, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255]
        )
        contours, _ = cv2.findContours(eroded, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # 'cells' save the location and sort
        cells = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            # case 1：eliminate rectangles that are too thin (might be lines)
            if w > h * 20 or h > w * 20:
                continue
            # case 2：remove a box similar to the whole image
            if (w > size[1] * 0.8) and (h > size[0] * 0.8):
                continue

            # case 3: eliminate small boxes that could be noises
            area = cv2.contourArea(c)
            # Assume constant area. Does not work on images that are too large or too
            # small
            if area < 250:
                continue

            cells.append((x, y, w, h))

        # To avoid location errors in one line
        cells = sorted(cells, key=itemgetter(1, 0))

        return cells, added, thresh

    def cell2table(self, cells, added, thresh, target_dir, pmc):
        """Function: save table texts in several rows
        Input: ordered table cells, and processed image
        Output: table text saved line by line
        """
        # after sort, read cells line by line
        color = (0, 255, 0)  # box color
        table_row = []
        row = []

        for i, (x, y, w, h) in enumerate(cells):
            cv2.rectangle(added, (x, y), (x + w, y + h), color, 1)
            row.append(cells[i])

            # the last cell, footer or normal cell
            if i == len(cells) - 1:
                # save the last line
                table_row.append(row)
                break

            # newlines: [i] x+w >[i+1] x // [i+1] y > [i] y+h (latter is used, more accurate)
            # minus 5 in case two lines are too close
            if cells[i + 1][1] > cells[i][1] + cells[i][3] - 5:
                table_row.append(row)
                # save a new line
                row = []

        for row in table_row:
            row.sort(key=lambda x: x[0])
            for i, (x, y, w, h) in enumerate(row):
                row[i] = self.img2text(thresh, x, y, w, h)

        return table_row

    def text2json(self, table_row):
        """Function: save table into a formatted json file
        Input: table text saved line by line
        Output: formatted json file of tables
        """
        identifier = ""
        title = ""
        footer = ""
        superline = ""
        cnt1 = cnt2 = 0  # count to identify the column name line

        for i, row in enumerate(table_row):
            if len(row) == 1:
                if i == 0:
                    while len(table_row[i]) == 1:
                        superline = superline + " " + "".join(table_row[i])
                        i = i + 1
                        cnt1 = cnt1 + 1
                    low = superline.lower()
                    identifier = superline[low.find("table") : low.find("table") + 7]
                    title = superline[low.find("table") + 9 :].strip()
                if i == len(table_row) - 1:
                    superline = ""
                    while len(table_row[i]) == 1:
                        superline = "".join(table_row[i]) + " " + superline
                        i = i - 1
                        cnt2 = cnt2 + 1
                    footer = superline

        # remove titles and footers
        table_row = table_row[cnt1 : len(table_row) - cnt2]

        table = {}
        sections = []
        cur_section = {}

        pre_header = []
        pre_superrow = None
        cur_header = ""
        cur_superrow = ""

        for i, row in enumerate(table_row):
            if i == 0:
                cur_header = row
            elif i != 0 and len(row) == 1:
                if i != len(table_row) - 1:
                    cur_superrow = row

            # skip blank rows (rarely happen)
            if not any([i for i in row if i not in ["", "None"]]):
                continue

            else:
                if cur_header != pre_header:
                    sections = []
                    pre_superrow = None
                    table = {
                        "identifier": identifier,
                        "title": title,
                        "columns": cur_header,
                        "section": sections,
                        "footer": footer,
                    }
                elif cur_header == pre_header:
                    table["section"] = sections

                if cur_superrow != pre_superrow:
                    cur_section = {"section_name": cur_superrow, "results": []}
                    sections.append(cur_section)
                elif cur_superrow == pre_superrow:
                    cur_section["results"].append(row)

                pre_header = cur_header
                pre_superrow = cur_superrow

        return table

    def __reformat_table_json(self, table):
        if table == {}:
            return {}
        offset = 0
        if "title" not in table:
            print("no title")
        table_dict = {
            "inputfile": self.file_name,
            "id": self.tableIdentifier,
            "infons": {},
            "passages": [
                {
                    "offset": 0,
                    "infons": {
                        "section_title_1": "table_title",
                        "iao_name_1": "document title",
                        "iao_id_1": "IAO:0000305",
                    },
                    "text": table["title"],
                }
            ],
        }
        offset += len(table["title"])
        if "caption" in table.keys() and not table["caption"] == "":
            table_dict["passages"].append(
                {
                    "offset": offset,
                    "infons": {
                        "section_title_1": "table_caption",
                        "iao_name_1": "caption",
                        "iao_id_1": "IAO:0000304",
                    },
                    "text": table["caption"],
                }
            )
            offset += len(table["caption"])

        if "section" in table.keys():
            row_id = 2
            rsection = []
            this_offset = offset
            for sect in table["section"]:
                results_dict = {
                    "table_section_title_1": sect["section_name"],
                    "data_rows": [],
                }
                for result_row in sect["results"]:
                    col_id = 1
                    rrow = []
                    for result in result_row:
                        result_dict = {
                            "cell_id": f"{self.tableIdentifier}.{row_id}.{col_id}",
                            "cell_text": result,
                        }
                        col_id += 1
                        offset += len(str(result))
                        rrow.append(result_dict)
                    results_dict["data_rows"].append(rrow)
                    row_id += 1
                rsection.append(results_dict)

                columns = []
            for i, column in enumerate(table.get("column_headings", [])):
                columns.append(
                    {
                        "cell_id": f"{self.tableIdentifier}.1.{i + 1}",
                        "cell_text": column,
                    }
                )
            table_dict["passages"].append(
                {
                    "offset": this_offset,
                    "infons": {
                        "section_title_1": "table_content",
                        "iao_name_1": "table",
                        "iao_id_1": "IAO:0000306",
                    },
                    "column_headings": columns,
                    "results_section": rsection,
                }
            )

        if "footer" in table.keys() and not table["footer"] == "":
            table_dict["passages"].append(
                {
                    "offset": offset,
                    "infons": {
                        "section_title_1": "table_footer",
                        "iao_name_1": "caption",
                        "iao_id_1": "IAO:0000304",
                    },
                    "text": table["footer"],
                }
            )
            offset += len(table["footer"])
        return table_dict

    def __init__(self, table_images, base_dir, trained_data="eng"):
        self.trainedData = trained_data
        self.tables = {
            "source": "Auto-CORPus (tables)",
            "date": f"{datetime.today().strftime('%Y%m%d')}",
            "key": "autocorpus_tables.key",
            "infons": {},
            "documents": [],
        }
        base_dir = Path(base_dir)
        for image_path in table_images:
            image_path = Path(image_path)
            imgname = image_path.name
            self.tableIdentifier = imgname.split("_")[-1].split(".")[0]
            self.file_name = str(image_path.relative_to(base_dir))
            pmc = imgname.stem

            img = cv2.imread(str(image_path))

            cells, added, thresh = self.find_cells(img)
            table_row = self.cell2table(cells, added, thresh, "imagesOut", pmc)
            self.tables["documents"].append(
                self.__reformat_table_json(self.text2json(table_row))
            )

    def to_dict(self):
        return self.tables
