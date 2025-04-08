"""Tables-JSON top-level builder script."""

import re
from datetime import datetime
from itertools import pairwise, product
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from .utils import get_data_element_node, handle_tables, navigate_contents

pval_regex = r"((\d+\.\d+)|(\d+))(\s?)[*××xX](\s{0,1})10[_]{0,1}([–−-])(\d+)"
pval_scientific_regex = r"((\d+.\d+)|(\d+))(\s{0,1})[eE](\s{0,1})([–−-])(\s{0,1})(\d+)"


def __table_to_2d(t: BeautifulSoup) -> list[list[str]] | None:
    """Transform tables from nested lists to JSON.

    Args:
        t (bs4.BeautifulSoup): html table, beautiful soup object

    Returns:
        (list): table in JSON format

    """
    # https://stackoverflow.com/questions/48393253/how-to-parse-table-with-rowspan-and-colspan
    rows: list[Tag] = t.find_all("tr")
    # fill colspan and rowspan
    for row in rows:
        for col in row.findAll(["th", "td"]):
            if "colspan" not in col.attrs:
                col.attrs["colspan"] = 1
            if "rowspan" not in col.attrs:
                col.attrs["rowspan"] = 1

    # first scan, see how many columns we need
    temp_row: Tag | NavigableString | None = t.find("tr")
    if not temp_row:
        return None
    temp_cells: list[Tag] = (
        temp_row.findAll(["th", "td"]) if isinstance(temp_row, Tag) else []
    )
    n_cols: int = (
        sum([int(i.attrs["colspan"]) for i in temp_cells]) if temp_cells else 0
    )

    # build an empty matrix for all possible cells
    table: list[list[str]] = [[""] * n_cols for row in rows]

    # fill matrix from row data
    # track pending rowspans, column number mapping to count
    rowspans: dict[int, int] = {}
    for row_idx, row in enumerate(rows):
        span_offset: int = 0  # how many columns are skipped due to row and colspans
        for col_idx, cell in enumerate(row.findAll(["td", "th"])):
            # adjust for preceding row and colspans
            col_idx += span_offset
            while rowspans.get(col_idx, 0):
                span_offset += 1
                col_idx += 1

            # fill table data
            rowspan = int(cell.attrs["rowspan"])
            rowspans[col_idx] = rowspan
            colspan: int = int(cell.attrs["colspan"])

            # next column is offset by the colspan
            span_offset += colspan - 1
            value: str = ""
            for item in cell.contents:
                value += navigate_contents(item)

            # clean the cell
            value = value.strip().replace("\u2009", " ").replace("&#x000a0;", " ")
            value = re.sub(r"\s", " ", value)
            value = re.sub("<\\/?span[^>\n]*>?|<hr\\/>?", "", value)
            value = re.sub("\\n", "", value)
            if value.startswith("(") and value.endswith(")"):
                value = value[1:-1]
            if re.match(pval_regex, value):
                value = re.sub(
                    r"(\s{0,1})[*××xX](\s{0,1})10(_{0,1})", "e", value
                ).replace("−", "-")
            if re.match(pval_scientific_regex, value):
                value = re.sub(r"(\s{0,1})[–−-](\s{0,1})", "-", value)
                value = re.sub(r"(\s{0,1})[eE]", "e", value)
            for drow, dcol in product(range(rowspan), range(colspan)):
                try:
                    table[row_idx + drow][col_idx + dcol] = value
                    rowspans[col_idx + dcol] = rowspan
                except IndexError:
                    # rowspan or colspan outside the confines of the table
                    pass

        # update rowspan bookkeeping
        rowspans = {c: s - 1 for c, s in rowspans.items() if s > 1}
    return table


def __check_superrow(cells: list[str]) -> bool:
    """Check if the current row is a superrow.

    Args:
        cells: Cells in row
    """
    cleaned_row: set[str] = set(
        cell for cell in cells if cell not in ("", "\n", "None")
    )
    return len(cleaned_row) == 1 and bool(re.match("[a-zA-Z]", next(iter(cleaned_row))))


def __get_headers(t: BeautifulSoup, config: dict[str, Any]) -> list[int]:
    """Identify headers from a table.

    Args:
        t (bs4.BeautifulSoup): BeautifulSoup object of table
        config (dict): configuration dictionary

    Returns:
        (list): a list of header index

    Raises:
        KeyError: Raises an exception.

    """
    idx_list: list[int] = []
    for idx, row in enumerate(
        get_data_element_node(config["tables"]["data"]["table-row"], t)
    ):
        if get_data_element_node(config["tables"]["data"]["header-element"], row):
            idx_list.append(idx)
        elif "class" in row.attrs:
            if "thead" in row.attrs["class"]:
                idx_list.append(idx)
    # if no table headers found
    if idx_list == []:
        idx_list = [0]
    return idx_list


def __is_number(s: str) -> bool:
    """Check if input string is a number.

    Args:
        s (str): input string

    Returns:
        (bool): True/False

    """
    try:
        float(s.replace(",", ""))
        return True
    except ValueError:
        return False


def __is_mix(s: str) -> bool:
    """Check if input string is a mix of number and text.

    Args:
        s (str): input string

    Returns:
        (bool): True/False

    """
    if any(char.isdigit() for char in s):
        if any(char for char in s if not char.isdigit()):
            return True
    return False


def __is_text(s: str) -> bool:
    """Check if input string is all text.

    Args:
        s: input string

    Returns:
        True/False

    """
    if any(char.isdigit() for char in s):
        return False
    return True


def __table2json(
    table_2d,
    header_idx,
    subheader_idx,
    superrow_idx,
    table_num,
    title,
    footer,
    caption,
):
    """Transform tables from nested lists to JSON.

    Args:
        table_2d (list): nested list tables
        header_idx (list): list of header indices
        subheader_idx (list): list of subheader indices
        superrow_idx (list): list of superrow indices
        table_num (int): table number
        title (str): table title
        footer (str): table footer
        caption (str): table caption

    Returns:
        tables (list): tables in JSON format

    """
    tables = []
    sections = []
    cur_table = {}
    cur_section = {}

    pre_header = []
    pre_superrow = None
    cur_header = ""
    cur_superrow = ""
    for row_idx, row in enumerate(table_2d):
        if not any([i for i in row if i not in ["", "None"]]):
            continue
        if row_idx in header_idx:
            cur_header = [
                table_2d[i] for i in next(i for i in subheader_idx if row_idx in i)
            ]
        elif row_idx in superrow_idx:
            cur_superrow = next(i for i in row if i not in ("", "None"))
        else:
            if cur_header != pre_header:
                sections = []
                pre_superrow = None
                cur_table = {
                    "identifier": str(table_num + 1),
                    "title": title,
                    "caption": caption,
                    "columns": cur_header,
                    "section": sections,
                    "footer": footer,
                }
                tables.append(cur_table)
            elif cur_header == pre_header:
                cur_table["section"] = sections
            if cur_superrow != pre_superrow:
                cur_section = {"section_name": cur_superrow, "results": [row]}
                sections.append(cur_section)
            elif cur_superrow == pre_superrow:
                cur_section["results"].append(row)

            pre_header = cur_header
            pre_superrow = cur_superrow

    if len(tables) > 1:
        for table_idx, table in enumerate(tables):
            table["identifier"] += f".{table_idx + 1}"
    return tables


def __format_table_bioc(table_json, tableIdentifier, file_path):
    bioc_format = {
        "source": "Auto-CORPus (tables)",
        "date": f"{datetime.today().strftime('%Y%m%d')}",
        "key": "autocorpus_tables.key",
        "infons": {},
        "documents": [],
    }
    for table in table_json["tables"]:
        if "." in table["identifier"] and tableIdentifier:
            table_identifier = (
                tableIdentifier + "_" + table["identifier"].split(".")[-1]
            )
        else:
            if tableIdentifier:
                table_identifier = tableIdentifier
            else:
                table_identifier = table["identifier"].replace(".", "_")
        identifier = table_identifier
        offset = 0
        table_dict = {
            "inputfile": file_path,
            "id": f"{identifier}",
            "infons": {},
            "passages": [
                {
                    "offset": 0,
                    "infons": {
                        "section_title_1": "table_title",
                        "iao_name_1": "document title",
                        "iao_id_1": "IAO:0000305",
                    },
                    "text": ". ".join(table["title"]),
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
                    "text": ". ".join(table["caption"]),
                }
            )
            offset += len("".join(table["caption"]))

        if "section" in table.keys():
            row_id = 2
            rsection = []
            this_offset = offset
            for sect in table["section"]:
                results_dict = {
                    "table_section_title_1": sect["section_name"],
                    "data_rows": [],
                }
                for resultrow in sect["results"]:
                    col_id = 1
                    rrow = []
                    for result in resultrow:
                        result_dict = {
                            "cell_id": f"{identifier}.{row_id}.{col_id}",
                            "cell_text": result,
                        }
                        col_id += 1
                        offset += len(str(result))
                        rrow.append(result_dict)
                    results_dict["data_rows"].append(rrow)
                    row_id += 1
                rsection.append(results_dict)

            columns = []
            for i, column in enumerate(table.get("columns", [])):
                columns.append(
                    {"cell_id": f"{identifier}.1.{i + 1}", "cell_text": column}
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
                    "data_section": rsection,
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
                    "text": ". ".join(table["footer"]),
                }
            )
            offset += len("".join(table["footer"]))
        bioc_format["documents"].append(table_dict)
    return bioc_format


def get_table_json(
    soup: BeautifulSoup, config: dict[str, Any], file_name: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extracts and processes tables from an HTML document using BeautifulSoup and a configuration dictionary.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML document.
        config (dict[str, Any]): A dictionary containing configuration options for table processing.
        file_name (str): The file name or path of the HTML document being processed.

    Returns:
        dict[str, Any]: A dictionary containing the processed table data in JSON format.
        list[dict[str, Any]]: A list of dictionaries representing empty tables.

    The function performs the following steps:
    1. Extracts tables from the HTML document based on the provided configuration.
    2. Removes empty tables and tables with specific classes (e.g., "table-group").
    3. Identifies and processes table headers, superrows, and subheaders.
    4. Converts tables into a 2D format and processes cell data types (e.g., numeric, text, mixed).
    5. Converts the processed table data into a JSON-compatible format.
    6. Merges headers and formats the final table data for output.
    """
    soup_tables: list[dict[str, Any]] = handle_tables(config["tables"], soup)

    file_path: str = file_name
    file_name = Path(file_name).name
    tableIdentifier: str | None = None
    if re.search(r"_table_\d+\.html", file_name):
        tableIdentifier = file_name.split("/")[-1].split("_")[-1].split(".")[0]

    # remove empty table and other table classes
    pop_list: list[int] = []
    empty_tables: list[dict[str, str]] = []

    for i, table in enumerate(soup_tables):
        if "class" in table["node"].attrs:
            if "table-group" in table["node"].attrs["class"]:
                pop_list.append(i)
        if table["node"].find_all("tbody") == []:
            pop_list.append(i)
            empty_tables.append(table)
    soup_tables = [soup_tables[i] for i in range(len(soup_tables)) if i not in pop_list]
    empty_tables = []
    for etable in empty_tables:
        if etable["node"].find("table"):
            pass
        # has a table element, not empty
        else:
            et_dict = {
                "title": " ".join(etable["title"]),
                "caption": " ".join(etable["caption"]),
                "footer": " ".join(etable["footer"]),
            }
            empty_tables.append(et_dict)

    # One table
    tables = []
    for table_num, table in enumerate(soup_tables):
        # remove empty table header
        if table["node"].find("td", "thead-hr"):
            table["node"].find("td", "thead-hr").parent.extract()

        header_idx: list[int] = __get_headers(table["node"], config)

        # span table to single-cells
        table_2d: list[list[Any]] | None = __table_to_2d(table["node"])
        if table_2d is None:
            continue

        # find superrows
        superrow_idx = []
        if table_2d is not None:
            for row_idx, row in enumerate(table_2d):
                if row_idx not in header_idx:
                    if __check_superrow(row):
                        superrow_idx.append(row_idx)

        # identify section names in index column
        if superrow_idx == []:
            first_col = [row[0] for row in table_2d]
            first_col_vals = [
                i for i in first_col if first_col.index(i) not in header_idx
            ]
            unique_vals = set([i for i in first_col_vals if i not in ["", "None"]])
            if len(unique_vals) <= len(first_col_vals) / 2:
                section_names = list(unique_vals)
                for i in section_names:
                    superrow_idx.append(first_col.index(i))
                n_cols = len(table_2d[0])
                for idx, val in zip(superrow_idx, section_names):
                    table_2d = table_2d[:idx] + [[val] * n_cols] + table_2d[idx:]
                # update superrow_idx after superrow insertion
                superrow_idx = []
                first_col = [row[0] for row in table_2d]
                for i in section_names:
                    superrow_idx.append(first_col.index(i))
                for row in table_2d:
                    row.pop(0)

        # Identify subheaders
        value_idx = [
            i for i in range(len(table_2d)) if i not in header_idx + superrow_idx
        ]
        col_type = []
        for col_idx in range(len(table_2d[0])):
            cur_col = [i[col_idx] for i in table_2d]
            num_cnt = 0
            txt_cnt = 0
            mix_cnt = 0
            for cell in cur_col:
                cell = str(cell).lower()
                if cell in [
                    "none",
                    "",
                    "-",
                ]:
                    continue
                elif __is_number(cell):
                    num_cnt += 1
                elif __is_mix(cell):
                    mix_cnt += 1
                elif __is_text(cell):
                    txt_cnt += 1
            if max(num_cnt, txt_cnt, mix_cnt) == num_cnt:
                col_type.append("num")
            elif max(num_cnt, txt_cnt, mix_cnt) == txt_cnt:
                col_type.append("txt")
            else:
                col_type.append("mix")
        subheader_idx: list[int] = []
        for row_idx in value_idx:
            cur_row = table_2d[row_idx]
            unmatch_cnt = 0
            for col_idx in range(len(cur_row)):
                cell = str(cur_row[col_idx]).lower()
                if (
                    __is_text(cell)
                    and col_type[col_idx] != "txt"
                    and cell
                    not in [
                        "none",
                        "",
                        "-",
                    ]
                ):
                    unmatch_cnt += 1
            if unmatch_cnt >= len(cur_row) / 2:
                subheader_idx.append(row_idx)
        header_idx += subheader_idx

        new_subheader_idx: list[list[int]] = []
        tmp: list[int] = [header_idx[0]]
        for i, j in pairwise(header_idx):
            if j == i + 1:
                tmp.append(j)
            else:
                new_subheader_idx.append(tmp)
                tmp = [j]
        new_subheader_idx.append(tmp)

        # convert to float
        for row in table_2d:
            for cell in range(len(row)):
                try:
                    row[cell] = float(
                        row[cell].replace("−", "-").replace("–", "-").replace(",", "")
                    )
                except Exception:
                    row[cell] = row[cell]

        cur_table = __table2json(
            table_2d,
            header_idx,
            new_subheader_idx,
            superrow_idx,
            table_num,
            table["title"],
            table["footer"],
            table["caption"],
        )
        # merge headers
        sep = "|"
        for table in cur_table:
            headers = table["columns"]
            new_header = []
            if not headers:
                continue
            for col_idx in range(len(headers[0])):
                new_element = ""
                for r_idx in range(len(headers)):
                    new_element += str(headers[r_idx][col_idx]) + sep
                new_element = new_element.rstrip(sep)
                new_header.append(new_element)
            table["columns"] = new_header

        tables += cur_table

    table_json = {"tables": tables}
    table_json = __format_table_bioc(table_json, tableIdentifier, file_path)
    return table_json, empty_tables


# def to_dict(self) -> tuple[dict[str, Any], list[dict[str, str]]]:
#     """Return the built tables and empty tables as two dictionaries.

#     Returns:
#         (dict): Tables-JSON
#         (list): Empty tables
#     """
#     return tables, empty_tables
