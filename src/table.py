import json
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

from src.utils import *
from utils import is_mixed_data_type, is_text


class TableParser:
    """
    Public interface class for table construction
    """

    def __init__(self, config: dict):
        self.__header_idx: list = []
        self.__superrow_idx: list = []
        self.__subheader_idx: list = []
        self.__table_2d: list = []
        self.config = config
        self.soup_tables = None
        self.is_parsed = False
        self.file_name = ""
        self.row_size = 0

    def reset_parsed_state(self):
        self.__header_idx: list = []
        self.__superrow_idx: list = []
        self.__subheader_idx: list = []
        self.__table_2d: list = []
        self.soup_tables = False
        self.is_parsed = False
        self.file_name = ""
        self.row_size = 0

    @staticmethod
    def get_pval_regex() -> str:
        return r'((\d+\.\d+)|(\d+))(\s?)[*××xX](\s{0,1})10[_]{0,1}([–−-])(\d+)'

    @staticmethod
    def get_pval_scientific_regex() -> str:
        return r'((\d+.\d+)|(\d+))(\s{0,1})[eE](\s{0,1})([–−-])(\s{0,1})(\d+)'

    def __get_empty_tables(self) -> tuple:
        pop_list = []
        empty_tables = []

        for i in range(len(self.soup_tables)):
            table = self.soup_tables[i]
            if 'class' in table['node'].attrs:
                if 'Table-group' in table['node'].attrs['class']:
                    pop_list.append(i)
            if not table['node'].find_all('tbody'):
                pop_list.append(i)
                empty_tables.append(table)

        return pop_list, empty_tables

    def __contains_superrow(self, row: list) -> bool:
        first_col = [row[0] for row in self.__table_2d]
        first_col_vals = [i for i in first_col if first_col.index(i) not in self.__header_idx]
        unique_vals = TableParser.get_unique_values(first_col_vals)

        if len(unique_vals) > 1:
            # iterate through unique cell indexes
            cell_count = len(row[1:])
            blank_cell_count = 0
            duplicated_cell_count = 0
            if not cell_count:
                return True
            # iterate through cells in the row of current unique cell
            for cell_idx in range(cell_count):
                # ignore first cell (it is the unique cell)
                cell = row[cell_idx + 1]
                # Super rows should be a single cell/value with no content other than duplicates
                # in other cells within the row.
                if cell:
                    if cell == row[0]:
                        duplicated_cell_count += 1
                    else:
                        continue
                else:
                    blank_cell_count += 1

            # Conditions for super row identification
            if cell_count in [blank_cell_count, duplicated_cell_count, blank_cell_count + duplicated_cell_count]:
                return True
        return False

    @staticmethod
    def get_unique_values(vals: list) -> set:
        return set([i for i in vals if i not in ['', 'None']])

    def __get_headers(self, t: BeautifulSoup) -> list:
        """
        identify headers from a Table

        Args:
            t: BeautifulSoup object of Table

        Returns:
            idx_list: a list of header index

        Raises:
            KeyError: Raises an exception.
        """
        idx_list = []
        rows = get_data_element_node(self.config['tables']['data']['table-row'], t)
        for idx in range(len(rows)):
            row = rows[idx]
            if get_data_element_node(self.config['tables']['data']['header-element'], row):
                idx_list.append(idx)
            elif 'class' in row.attrs:
                if 'thead' in row.attrs['class']:
                    idx_list.append(idx)
        # if no Table headers found
        if not idx_list:
            idx_list = [0]
        return idx_list

    def __table_to_2d(self, t: BeautifulSoup) -> None:
        """
        transform tables from nested lists to JSON

        Args:
            t: html table, beautiful soup object

        Returns:
            list: table in JSON format

        """
        # https://stackoverflow.com/questions/48393253/how-to-parse-table-with-rowspan-and-colspan
        rows = t.find_all('tr')
        # fill colspan and rowspan
        for row in rows:
            for col in row.findAll(['th', 'td']):
                if 'colspan' not in col.attrs:
                    col.attrs['colspan'] = 1
                if 'rowspan' not in col.attrs:
                    col.attrs['rowspan'] = 1

        # first scan, see how many columns we need
        n_cols = sum([int(i.attrs['colspan']) for i in t.find('tr').findAll(['th', 'td'])])
        self.row_size = n_cols
        # build an empty matrix for all possible cells
        table = []
        for i in range(len(rows)):
            table += [[''] * n_cols]

        # fill matrix from row data
        rowspans = {}  # track pending rowspans, column number mapping to count
        for row_idx in range(len(rows)):
            row = rows[row_idx]
            span_offset = 0  # how many columns are skipped due to row and colspans
            matches = row.findAll(['td', 'th'])
            for col_idx in range(len(matches)):
                cell = matches[col_idx]
                # adjust for preceding row and colspans
                col_idx += span_offset
                while rowspans.get(col_idx, 0):
                    span_offset += 1
                    col_idx += 1

                # fill Table data
                rowspan = rowspans[col_idx] = int(cell.attrs['rowspan'])
                colspan = int(cell.attrs['colspan'])
                # next column is offset by the colspan
                span_offset += colspan - 1

                c_cont = cell.contents
                value = ""
                for item in c_cont:
                    value += navigate_contents(item)

                # clean the cell
                value = value.strip().replace('\u2009', ' ').replace("&#x000a0;", " ")
                value = re.sub(r"\s", " ", value)
                value = re.sub(r"</?span[^>\n]*>?|<hr/>?", "", value)
                value = re.sub(r"\n", "", value)
                if value.startswith('(') and value.endswith(')'):
                    value = value[1:-1]
                if re.match(TableParser.get_pval_regex(), value):
                    value = re.sub(r'(\s?)[*×xX](\s?)10(_?)', 'e', value).replace('−', '-')
                if re.match(TableParser.get_pval_scientific_regex(), value):
                    value = re.sub(r'(\s?)[–−-](\s?)', '-', value)
                    value = re.sub(r'(\s?)[eE]', 'e', value)
                for drow, dcol in product(range(rowspan), range(colspan)):
                    try:
                        table[row_idx + drow][col_idx + dcol] = value
                        rowspans[col_idx + dcol] = rowspan
                    except IndexError:
                        # rowspan or colspan outside the confines of the Table
                        pass
            # update rowspan bookkeeping
            rowspans = {c: s - 1 for c, s in rowspans.items() if s > 1}
        self.__table_2d = table

    def __get_superrows(self) -> list:
        superrow_list = []
        if self.__table_2d:
            for row_idx in range(len(self.__table_2d)):
                row = self.__table_2d[row_idx]
                if row_idx not in self.__header_idx:
                    if self.__contains_superrow(row):
                        superrow_list.append(row_idx)
        return superrow_list

    def __get_subheaders(self, table_2d: list) -> None:
        value_idx = [i for i in range(len(table_2d)) if i not in self.__header_idx + self.__superrow_idx]
        col_type = []
        for col_idx in range(len(table_2d[1])):  # Ignore header row (0 index) length
            cur_col = [i[col_idx] for i in table_2d]
            num_cnt = 0
            txt_cnt = 0
            mix_cnt = 0
            for cell in cur_col:
                cell = str(cell).lower()
                if cell in ['none', '', '-', ]:
                    continue
                elif is_number(cell):
                    num_cnt += 1
                elif is_mixed_data_type(cell):
                    mix_cnt += 1
                elif is_text(cell):
                    txt_cnt += 1
            if max(num_cnt, txt_cnt, mix_cnt) == num_cnt:
                col_type.append('num')
            elif max(num_cnt, txt_cnt, mix_cnt) == txt_cnt:
                col_type.append('txt')
            else:
                col_type.append('mix')
        self.__subheader_idx = []
        for row_idx in value_idx:
            cur_row = table_2d[row_idx]
            unmatch_cnt = 0
            for col_idx in range(len(cur_row)):
                cell = str(cur_row[col_idx]).lower()
                if is_text(cell) and col_type[col_idx] != 'txt' and cell not in ['none', '', '-', 'na']:
                    unmatch_cnt += 1
            if unmatch_cnt >= len(cur_row) / 2 or self.__contains_superrow(cur_row):
                self.__subheader_idx.append(row_idx)
        self.__header_idx += self.__subheader_idx
        self.__subheader_idx = []
        tmp = [self.__header_idx[0]]
        if len(self.__header_idx) < 2:
            self.__subheader_idx.append([self.__header_idx[0]])
        else:
            for i, j in zip(self.__header_idx, self.__header_idx[1:]):
                if j == i + 1:
                    tmp.append(j)
                else:
                    self.__subheader_idx.append(tmp)
                    tmp = [j]
            self.__subheader_idx.append(tmp)

    def __parse_table(self, table_idx: int, table: dict) -> list:
        # remove empty Table header
        if table['node'].find('td', 'thead-hr'):
            table['node'].find('td', 'thead-hr').parent.extract()

        self.__header_idx = self.__get_headers(table['node'])

        # span Table to single-cells
        self.__table_to_2d(table['node'])

        # find superrows
        self.__superrow_idx = self.__get_superrows()

        # identify section names in index column
        # self.__get_section_names()

        # Identify subheaders
        self.__get_subheaders(self.__table_2d)

        title = table['title'][0] if table['title'] else ""
        caption = table['caption'][0] if table['caption'] else ""
        footer = table['footer'][0] if table['footer'] else ""

        tables = Table.build_table(table_idx, self.__table_2d, self.__header_idx,
                                   self.__subheader_idx, self.__superrow_idx, title, caption,
                                   footer,
                                   file_path=self.file_name)
        return tables

    def get_tables(self, soup: BeautifulSoup, file_name: str) -> tuple:
        self.file_name = Path(file_name).resolve().__str__()

        self.soup_tables = handle_tables(self.config['tables'], soup)

        # remove empty Table and other Table classes
        pop_list, empty_tables = self.__get_empty_tables()

        soup_tables = [self.soup_tables[i] for i in range(len(self.soup_tables)) if i not in pop_list]

        for etable in empty_tables:
            if etable['node'].find("Table"):
                pass
            # has a Table element, not empty
            else:
                et_dict = {
                    "title": " ".join(etable['title']),
                    "caption": " ".join(etable['caption']),
                    "footer": " ".join(etable['footer'])
                }
                empty_tables.append(et_dict)

        table_docs: list = [self.__parse_table(i + 1, soup_tables[i]) for i in range(len(soup_tables))]
        # Flatten structure to a single list for output
        table_docs = [x for y in table_docs for x in y]
        current_datetime = f'{datetime.today().strftime("%Y%m%d")}'
        output_tables = TableBioc("Auto-CORPus (tables)", current_datetime, "autocorpus_tables.key", {}, table_docs)
        output_tables = json.loads(json.dumps(output_tables, default=complex_handler))
        self.reset_parsed_state()
        return output_tables, empty_tables


class TableBioc:

    def __init__(self, source: str, date: str, key: str, infons: dict, documents: list) -> None:
        if documents is None:
            documents = []
        if infons is None:
            infons = {}
        self.source: str = source
        self.date: str = date
        self.key: str = key
        self.infons: dict = infons
        self.documents: list = self.flatten_documents(documents)

    @staticmethod
    def flatten_documents(docs: list) -> list:
        new_docs = []
        for doc in docs:
            if type(doc) == list:
                new_docs += doc
            else:
                new_docs.append(doc)
        return new_docs

    def get_dict(self) -> dict:
        return self.__dict__


class Table:

    def __init__(self, identifier: str, file_path: str, passages: list = None) -> None:
        if passages is None:
            passages = []
        self.inputFile: str = file_path
        self.id = identifier
        self.__table_2d: List[list] = []
        self.infons: Optional[Infons, dict] = {}
        self.passages: Optional[List[TablePassage]] = passages
        self.content_passage: Optional[TableContentPassage] = None
        self.__offset = 0

    def add_passage(self, infons_type: int, passage_type: callable, text: str = None) -> None:
        text_length = len(text) if text else 0
        new_passage = passage_type(self.__offset, infons_type, text)
        self.__offset += text_length
        self.passages.append(new_passage)

    def add_table_content_passage(self, column_headings: 'TableRow') -> None:
        new_passage = TableContentPassage(self.__offset, column_headings)
        self.__offset += new_passage.update_text_length()
        self.passages.append(new_passage)
        self.content_passage = new_passage

    def add_data_section(self, data_rows: list, infons_type: int, text: str) -> 'TableDataSection':
        new_data_section = TableDataSection(data_rows, self.__offset, infons_type, text)
        self.__offset += new_data_section.update_text_length()
        self.content_passage.add_data_section(new_data_section)
        return new_data_section

    def get_dict(self) -> dict:
        output = self.__dict__
        if "_Table__table_2d" in output.keys():
            del output["_Table__table_2d"]
        if "content_passage" in output.keys():
            del output["content_passage"]
        if "_Table__offset" in output.keys():
            del output["_Table__offset"]
        return output

    @staticmethod
    def __create_headers(headings: list, table_ident: int) -> 'TableRow':
        """

        Args:
            headings:
            table_ident:

        Returns:

        """
        # merge headers
        sep = '|'
        for header in headings:
            if len(header) == len(headings[0]) - 1:
                header.insert(0, '')

        new_header = TableRow()
        for col_idx in range(len(headings[0])):
            new_cell_content = ''
            for r_idx in range(len(headings)):
                if not headings[r_idx][col_idx]:
                    continue
                # Ensure no duplication of heading due to row span value.
                temp_val = str(headings[r_idx][col_idx])
                if temp_val in new_cell_content.split(sep):  # new_cell_content.rstrip(sep) == temp_val:
                    continue
                new_cell_content += str(headings[r_idx][col_idx]) + sep
            new_cell_content = new_cell_content.rstrip(sep)
            new_cell = TableCell(new_cell_content, F"{table_ident}.1.{col_idx + 1}")
            new_header.cells.append(new_cell)
        return new_header

    @staticmethod
    def __create_row_cells(row: list, table_ident: int, row_idx: int) -> 'TableRow':
        """
        Returns a TableRow object from the list of cell data.
        Args:
            row: list of cells in a single row containing cell contents
            table_ident: parent table identifier
            row_idx: index of the row within the table

        Returns:
            row_obj: TableRow object constructed from input data.
        """
        cell_objs = [TableCell(row[x], F"{table_ident}.{row_idx}.{x + 1}") for x in range(len(row))]
        row_obj = TableRow(cell_objs)
        return row_obj

    @staticmethod
    def build_table(table_identifier: int, table_2d: list, header_idx: list, subheader_idx: list,
                    superrow_idx: list, title: str, caption: str, footer: str,
                    file_path: str) -> list:
        """

        Args:
            table_identifier: Table number
            table_2d: Two dimensional list containing rows with cell values.
            header_idx: list of row indexes designated as table headers
            subheader_idx: list of row indexes designated as table subheaders
            superrow_idx: list of row indexes designated as super rows
            title: title text of the table
            caption: caption text of the table
            footer: footer text of the table
            file_path: file path string of the table's file.

        Returns: Table object containing restructured input data.

        """
        tables = []
        cur_table = {}
        prev_table = {}
        cur_data_section = {}
        cur_header = ''
        prev_header = ''
        cur_superrow = []
        prev_superrow = []
        split_table_identifier = 0
        final_row = len(table_2d)
        superrows_created = 0  # Deduct this row count when adding data rows with cell ids.
        data_row_added = False

        for row_idx in range(len(table_2d)):
            row = table_2d[row_idx]
            # Ignore blank rows.
            if not any([i for i in row if i not in ['', 'None']]):
                continue

            # Add table header if within the header indexes and skip to next row.
            if row_idx in header_idx:
                header_data = [table_2d[i] for i in [i for i in subheader_idx if row_idx in i][0]]
                cur_header = Table.__create_headers(header_data, split_table_identifier + 1)

            # Create a new table if row is flagged as a super row
            # or if no data rows have been added yet (initial table creation)
            if ((cur_header != prev_header) and data_row_added) or not cur_table:
                # Is this a start of a split table?
                if prev_table:
                    if footer:
                        prev_table.add_passage(Infons.TYPE_FOOTER, TablePassage, footer)

                # Incremented this way due to potentially multiple table objects
                # from 1 original input table.
                split_table_identifier += 1
                if row_idx in superrow_idx:
                    cur_superrow = next(i for i in row if i)
                # if no data has been added yet, do not split the table here.
                # Create a new table
                cur_table = Table(F"{table_identifier}_{split_table_identifier}", file_path=file_path)
                if title:
                    cur_table.add_passage(Infons.TYPE_TITLE, TablePassage, title)
                if caption:
                    cur_table.add_passage(Infons.TYPE_CAPTION, TablePassage, caption)
                cur_table.add_table_content_passage(cur_header)
                tables.append(cur_table)
                prev_table = cur_table
                data_row_added = False
                cur_data_section = {}

            elif row_idx in superrow_idx:
                cur_superrow = next(i for i in row if i)

            # If final row, add the last section to the table.
            elif row_idx + 1 == final_row:
                row = Table.__create_row_cells(row, split_table_identifier, row_idx - superrows_created)
                cur_data_section.data_rows.append(row)
                if footer:
                    prev_table.add_passage(Infons.TYPE_FOOTER, TablePassage, footer)

            # Row contains content data
            elif row_idx not in header_idx:
                # Add content to current table section if one is in progress
                if cur_data_section and prev_superrow == cur_superrow:
                    row = Table.__create_row_cells(row, split_table_identifier, row_idx - superrows_created)
                    cur_data_section.data_rows.append(row)

                # Create a new data section
                else:
                    row = Table.__create_row_cells(row, split_table_identifier, row_idx - superrows_created)
                    cur_data_section = cur_table.add_data_section([row], Infons.TYPE_DATA_SECTION, cur_superrow)
                    prev_superrow = cur_superrow
                # Data rows have started being added.
                data_row_added = True
            # For splitting subheaders part-way down the original table.
            prev_header = cur_header

        return tables


class TablePassage:

    def __init__(self, offset: int, infons_type: int, text: str) -> None:
        self.offset: int = offset
        self.infons: Infons = Infons.get_infons(infons_type)
        self.text: str = text
        self.passage_text_length = len(text)
        self.annotations = []
        self.relations = []

    def get_dict(self) -> dict:
        # Remove undesired outputs for BioC
        output = self.__dict__
        if "passage_text_length" in output.keys():
            del output["passage_text_length"]
        if "text" in output.keys():
            if not output["text"]:
                del output["text"]
        return output


class TableContentPassage(TablePassage):
    def __init__(self, offset: int, column_headings: 'TableRow', data_section: list = None) -> None:
        super().__init__(offset, Infons.TYPE_SECTION, "")
        if data_section is None:
            data_section = []
        self.column_headings: TableRow = column_headings
        self.data_section: List[TableDataSection] = data_section
        self.passage_text_length = 0

    def update_text_length(self) -> int:
        # Calculate the text length of elements within this passage.
        length = len(str(self.text))
        for cell in self.column_headings.cells:
            length += len(str(cell.cell_text))
        for section in self.data_section:
            for row in section.data_rows:
                for cell in row.cells:
                    length += len(str(cell.cell_text))
        self.passage_text_length = length
        return length

    def add_data_section(self, data_section: 'TableDataSection') -> None:
        self.data_section.append(data_section)

    def get_dict(self) -> dict:
        # Remove undesired outputs for BioC
        output = self.__dict__
        if "passage_text_length" in output.keys():
            del output["passage_text_length"]
        if "text" in output.keys():
            if not output["text"]:
                del output["text"]
        return output


class TableDataSection(TablePassage):
    def __init__(self, data_rows: list or 'TableRow', offset: int, infons_type: int, text: str) -> None:
        super().__init__(offset, infons_type, text)
        if type(data_rows) is TableRow:
            data_rows = [data_rows]
        self.data_rows = data_rows
        self.section_text_length = 0

    def update_text_length(self) -> int:
        length = len(str(self.text))
        for row in self.data_rows:
            for cell in row.cells:
                length += len(str(cell.cell_text))
        self.section_text_length = length
        return length

    def get_dict(self) -> dict:
        output = self.__dict__
        if "section_text_length" in output.keys():
            del output["section_text_length"]
        if "passage_text_length" in output.keys():
            del output["passage_text_length"]
        if "text" in output.keys():
            if not output["text"]:
                del output["text"]
                del output["infons"]
                del output["offset"]
        return output


class TableRow:
    def __init__(self, cells: list = None) -> None:
        if cells is None:
            cells = []
        self.cells = cells

    def get_dict(self) -> list:
        return self.cells


class TableCell:
    def __init__(self, text: str, cell_id: str) -> None:
        self.cell_id = cell_id
        self.cell_text = self.__convert_to_float(text)

    def get_dict(self) -> dict:
        return self.__dict__

    @staticmethod
    def __convert_to_float(text: str) -> float:
        try:
            text = float(text.replace('−', '-').replace('–', '-').replace(',', ''))
            return text
        except ValueError:
            return text


class Infons:
    TYPE_TITLE = 1
    TYPE_CAPTION = 2
    TYPE_FOOTER = 3
    TYPE_SECTION = 4
    TYPE_DATA_SECTION = 5

    def __init__(self, section_title: str, iao_name: str, iao_id: str, infons_type: int) -> None:
        self.section_title_1 = section_title
        self.iao_name_1 = iao_name
        self.iao_id_1 = iao_id
        self.infons_type = infons_type

    def get_dict(self) -> dict:
        output = self.__dict__
        if "infons_type" in output.keys():
            del output["infons_type"]
        return output

    @staticmethod
    def get_infons(infons_type: int) -> 'Infons':
        # validation of provided infons type
        if infons_type < 1 or infons_type > 5:
            raise ValueError

        if infons_type == Infons.TYPE_TITLE:
            section_title = "table_title"
            iao_name = "document title"
            iao_id = "IAO:0000305"
        elif infons_type == Infons.TYPE_CAPTION:
            section_title = "table_caption"
            iao_name = "caption"
            iao_id = "IAO:0000304"
        elif infons_type == Infons.TYPE_FOOTER:
            section_title = "table_footer"
            iao_name = "caption"
            iao_id = "IAO:0000304"
        elif infons_type == Infons.TYPE_SECTION:
            section_title = "table_content"
            iao_name = "table"
            iao_id = "IAO:0000306"
        else:
            section_title = "table_section_title"
            iao_name = "section title"
            iao_id = "IAO:0000304"

        return Infons(section_title, iao_name, iao_id, infons_type)


def complex_handler(obj: object) -> dict:
    """
    JSON default handler for dumping Table objects and nested children.
    Args:
        obj: Any Table Object (Table, TablePassage etc.)

    Returns:
        Nested dictionary object for JSON.dump structuring.
    """
    if hasattr(obj, 'get_dict'):
        return obj.get_dict()
    else:
        raise TypeError(F'Object of type {type(obj)} with value of {repr(obj)} is not JSON serializable')
