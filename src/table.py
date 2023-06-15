from datetime import datetime
from itertools import product
from pathlib import Path

from src.utils import *


class table:

    def __table_to_2d(self, t, config):
        """
		transform tables from nested lists to JSON

		Args:
			t: html table, beautiful soup object
			config: configuration dictionary

		Returns:
			table: table in JSON format

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

        # build an empty matrix for all possible cells
        table = [[''] * n_cols for row in rows]

        # fill matrix from row data
        rowspans = {}  # track pending rowspans, column number mapping to count
        for row_idx, row in enumerate(rows):
            span_offset = 0  # how many columns are skipped due to row and colspans
            for col_idx, cell in enumerate(row.findAll(['td', 'th'])):
                # adjust for preceding row and colspans
                col_idx += span_offset
                while rowspans.get(col_idx, 0):
                    span_offset += 1
                    col_idx += 1

                # fill table data
                rowspan = rowspans[col_idx] = int(cell.attrs['rowspan'])
                colspan = int(cell.attrs['colspan'])
                # next column is offset by the colspan
                span_offset += colspan - 1
                # value = ''.join(str(x) for x in cell.get_text())
                cCont = cell.contents
                value = ""
                for item in cCont:
                    value += navigate_contents(item)
                # if isinstance(item, bs4.element.NavigableString):
                # 	value += item + " "
                # if isinstance(item, bs4.element.Tag):
                # 	if item.name == "sup" or item.name == "sub":
                # 		value += "<" + item.name + ">"
                # 		value += item.get_text()
                # 		value += "</" + item.name + ">"
                # 	else:
                # 		value += item.get_text()
                # clean the cell
                value = value.strip().replace('\u2009', ' ').replace("&#x000a0;", " ")
                value = re.sub("\s", " ", value)
                value = re.sub("<\/?span[^>\n]*>?|<hr\/>?", "", value)
                value = re.sub("\\n", "", value)
                if value.startswith('(') and value.endswith(')'):
                    value = value[1:-1]
                if re.match(self.pval_regex, value):
                    value = re.sub(r'(\s{0,1})[*××xX](\s{0,1})10(_{0,1})', 'e', value).replace('−', '-')
                if re.match(self.pval_scientific_regex, value):
                    value = re.sub(r'(\s{0,1})[–−-](\s{0,1})', '-', value)
                    value = re.sub(r'(\s{0,1})[eE]', 'e', value)
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

    def __check_superrow(self, row):
        """
		check if the current row is a superrow

		Args:
			row: python list

		Return:
			True/False

		"""
        cleaned_row = set([i for i in row if (str(i) != '') & (str(i) != '\n') & (str(i) != 'None')])
        if len(cleaned_row) == 1 and bool(re.match("[a-zA-Z]", list(cleaned_row)[0])):
            return True
        else:
            return False

    def __find_format(self, header):
        """
		determine if there exists a splittable pattern in the header cell

		Args:
			header: single header str

		Returns:
			pattern: regex object

		Raises:
			KeyError: Raises an exception.
		"""

        if header == '':
            return None
        #     parts = nltk.tokenize.word_tokenize(header)
        a = re.split(r'[:|/,;]', header)
        b = re.findall(r'[:|/,;]', header)
        parts = []
        for i in range(len(b)):
            parts += [a[i], b[i]]
        parts.append(a[-1])

        # identify special character
        special_char_idx = []
        for idx, part in enumerate(parts):
            if part in ':|\/,;':
                special_char_idx.append(idx)

        # generate regex pattern
        if special_char_idx:
            pattern = r''
            for idx in range(len(parts)):
                if idx in special_char_idx:
                    char = parts[idx]
                    pattern += '({})'.format(char)
                else:
                    pattern += '(\w+)'
            pattern = re.compile(pattern)
            return pattern
        else:
            return None

    def __test_format(self, pattern, s):
        """
		check if the element conforms to the regex pattern

		Args:
			header: single header str
			s: element in string format

		Returns:
			result: bool

		Raises:
			KeyError: Raises an exception.
		"""

        if re.search(pattern, s):
            return True
        return False

    def __split_format(self, pattern, s):
        """
		split s according to regex pattern

		Args:
			pattern: regex object
			s: element in string format

		Returns:
			list of substrings

		Raises:
			KeyError: Raises an exception.
		"""
        return [i for i in re.split(r'[:|/,;]', s) if i not in ':|\/,;']

    def __get_headers(self, t, config):
        """
		identify headers from a table

		Args:
			t: BeautifulSoup object of table

		Returns:
			idx_list: a list of header index

		Raises:
			KeyError: Raises an exception.
		"""
        idx_list = []
        for idx, row in enumerate(get_data_element_node(config['tables']['data']['table-row'], t)):
            if get_data_element_node(config['tables']['data']['header-element'], row):
                idx_list.append(idx)
            elif 'class' in row.attrs:
                if 'thead' in row.attrs['class']:
                    idx_list.append(idx)
        # if no table headers found
        if idx_list == []:
            idx_list = [0]
        return idx_list

    def __get_superrows(self, t):
        """
		determine supperrows in a table

		Args:
			t: BeautifulSoup object of table

		Returns:
			idx_list: a list of superrow index

		"""
        idx_list = []
        for idx, row in enumerate(t):
            if idx not in self.__get_headers(t):
                if self.__check_superrow(row):
                    idx_list.append(idx)
        return idx_list

    def __is_number(self, s):
        """
		check if input string is a number

		Args:
			s: input string

		Returns:
			True/False

		"""
        try:
            float(s.replace(',', ''))
            return True
        except ValueError:
            return False

    def __is_mix(self, s):
        """
		check if input string is a mix of number and text

		Args:
			s: input string

		Returns:
			True/False

		"""
        if any(char.isdigit() for char in s):
            if any(char for char in s if char.isdigit() == False):
                return True
        return False

    def __is_text(self, s):
        """
		check if input string is all text

		Args:
			s: input string

		Returns:
			True/False

		"""
        if any(char.isdigit() for char in s):
            return False
        return True

    def __table2json(self, table_2d, header_idx, subheader_idx, superrow_idx, table_num, title, footer, caption):
        """
		transform tables from nested lists to JSON

		Args:
			table_2d: nested list tables
			header_idx: list of header indices
			subheader_idx: list of subheader indices
			superrow_idx: list of superrow indices
			table_num: table number
			caption: table caption
			footer: table footer

		Returns:
			tables: tables in JSON format

		"""
        tables = []
        sections = []
        cur_table = {}
        cur_section = {}

        pre_header = []
        pre_superrow = None
        cur_header = ''
        cur_superrow = ''
        for row_idx, row in enumerate(table_2d):
            if not any([i for i in row if i not in ['', 'None']]):
                continue
            if row_idx in header_idx:
                cur_header = [table_2d[i] for i in [i for i in subheader_idx if row_idx in i][0]]
            elif row_idx in superrow_idx:
                cur_superrow = [i for i in row if i not in ['', 'None']][0]
            else:
                if cur_header != pre_header:
                    sections = []
                    pre_superrow = None
                    cur_table = {'identifier': str(table_num + 1),
                                 'title': title,
                                 'caption': caption,
                                 'columns': cur_header,
                                 'section': sections,
                                 'footer': footer}
                    tables.append(cur_table)
                elif cur_header == pre_header:
                    cur_table['section'] = sections
                if cur_superrow != pre_superrow:
                    cur_section = {'section_name': cur_superrow,
                                   'results': [row]}
                    sections.append(cur_section)
                elif cur_superrow == pre_superrow:
                    cur_section['results'].append(row)

                pre_header = cur_header
                pre_superrow = cur_superrow

        if len(tables) > 1:
            for table_idx, table in enumerate(tables):
                table['identifier'] += '.{}'.format(table_idx + 1)
        return tables

    def __reformat_table_json(self, table_json):
        bioc_format = {
            "source": "Auto-CORPus (tables)",
            "date": f'{datetime.today().strftime("%Y%m%d")}',
            "key": "autocorpus_tables.key",
            "infons": {},
            "documents": []
        }
        for table in table_json['tables']:
            if "." in table['identifier'] and self.tableIdentifier:
                tableIdentifier = self.tableIdentifier + "_" + table['identifier'].split(".")[-1]
            else:
                if self.tableIdentifier:

                    tableIdentifier = self.tableIdentifier
                else:
                    tableIdentifier = table['identifier'].replace('.', '_')
            identifier = tableIdentifier
            offset = 0
            tableDict = {
                "inputfile": self.file_path,
                "id": F"{identifier}",
                "infons": {},
                "passages": [
                    {
                        "offset": 0,
                        "infons": {
                            "section_title_1": "table_title",
                            "iao_name_1": "document title",
                            "iao_id_1": "IAO:0000305"
                        },
                        "text": table['title']
                    }
                ]
            }
            offset += len(table['title'])
            if "caption" in table.keys() and not table['caption'] == "":
                tableDict['passages'].append(
                    {
                        "offset": offset,
                        "infons": {
                            "section_title_1": "table_caption",
                            "iao_name_1": "caption",
                            "iao_id_1": "IAO:0000304"
                        },
                        "text": ". ".join(table["caption"])
                    }
                )
                offset += len("".join(table["caption"]))

            if "section" in table.keys():
                rowID = 2
                rsection = []
                this_offset = offset
                for sect in table["section"]:

                    resultsDict = {
                        "table_section_title_1": sect['section_name'],
                        "data_rows": []
                    }
                    for resultrow in sect["results"]:
                        colID = 1
                        rrow = []
                        for result in resultrow:
                            resultDict = {
                                "cell_id": F"{identifier}.{rowID}.{colID}",
                                "cell_text": result
                            }
                            colID += 1
                            offset += len(str(result))
                            rrow.append(resultDict)
                        resultsDict["data_rows"].append(rrow)
                        rowID += 1
                    rsection.append(resultsDict)

                columns = []
                for i, column in enumerate(table.get("columns", [])):
                    columns.append(
                        {
                            "cell_id": F"{identifier}.1.{i + 1}",
                            "cell_text": column
                        }
                    )
                tableDict['passages'].append(
                    {
                        "offset": this_offset,
                        "infons": {
                            "section_title_1": "table_content",
                            "iao_name_1": "table",
                            "iao_id_1": "IAO:0000306"
                        },
                        "column_headings": columns,
                        "data_section": rsection
                    }
                )

            if "footer" in table.keys() and not table['footer'] == "":
                tableDict['passages'].append(
                    {
                        "offset": offset,
                        "infons": {
                            "section_title_1": "table_footer",
                            "iao_name_1": "caption",
                            "iao_id_1": "IAO:0000304"
                        },
                        "text": ". ".join(table["footer"])
                    }
                )
                offset += len("".join(table["footer"]))
            bioc_format["documents"].append(tableDict)
        return bioc_format

    def __main(self, soup, config):
        soup_tables = handle_tables(config['tables'], soup)

        # remove empty table and other table classes
        pop_list = []
        empty_tables = []

        for i, table in enumerate(soup_tables):
            if 'class' in table['node'].attrs:
                if 'table-group' in table['node'].attrs['class']:
                    pop_list.append(i)
            if table['node'].find_all('tbody') == []:
                pop_list.append(i)
                empty_tables.append(table)
        soup_tables = [soup_tables[i] for i in range(len(soup_tables)) if i not in pop_list]
        self.empty_tables = []
        for etable in empty_tables:
            if etable['node'].find("table"):
                pass
            # has a table element, not empty
            else:
                etDict = {
                    "title": " ".join(etable['title']),
                    "caption": " ".join(etable['caption']),
                    "footer": " ".join(etable['footer'])
                }
                self.empty_tables.append(etDict)

        # One table
        tables = []
        for table_num, table in enumerate(soup_tables):

            # remove empty table header
            if table['node'].find('td', 'thead-hr'):
                table['node'].find('td', 'thead-hr').parent.extract()

            header_idx = self.__get_headers(table['node'], config)

            # span table to single-cells
            table_2d = self.__table_to_2d(table['node'], config)

            # find superrows
            superrow_idx = []
            if table_2d != None:
                for row_idx, row in enumerate(table_2d):
                    if row_idx not in header_idx:
                        if self.__check_superrow(row):
                            superrow_idx.append(row_idx)

            # identify section names in index column
            if superrow_idx == []:
                first_col = [row[0] for row in table_2d]
                first_col_vals = [i for i in first_col if first_col.index(i) not in header_idx]
                unique_vals = set([i for i in first_col_vals if i not in ['', 'None']])
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
            value_idx = [i for i in range(len(table_2d)) if i not in header_idx + superrow_idx]
            col_type = []
            for col_idx in range(len(table_2d[0])):
                cur_col = [i[col_idx] for i in table_2d]
                num_cnt = 0
                txt_cnt = 0
                mix_cnt = 0
                for cell in cur_col:
                    cell = str(cell).lower()
                    if cell in ['none', '', '-', ]:
                        continue
                    elif self.__is_number(cell):
                        num_cnt += 1
                    elif self.__is_mix(cell):
                        mix_cnt += 1
                    elif self.__is_text(cell):
                        txt_cnt += 1
                if max(num_cnt, txt_cnt, mix_cnt) == num_cnt:
                    col_type.append('num')
                elif max(num_cnt, txt_cnt, mix_cnt) == txt_cnt:
                    col_type.append('txt')
                else:
                    col_type.append('mix')
            subheader_idx = []
            for row_idx in value_idx:
                cur_row = table_2d[row_idx]
                unmatch_cnt = 0
                for col_idx in range(len(cur_row)):
                    cell = str(cur_row[col_idx]).lower()
                    if self.__is_text(cell) and col_type[col_idx] != 'txt' and cell not in ['none', '', '-', ]:
                        unmatch_cnt += 1
                if unmatch_cnt >= len(cur_row) / 2:
                    subheader_idx.append(row_idx)
            header_idx += subheader_idx

            subheader_idx = []
            tmp = [header_idx[0]]
            for i, j in zip(header_idx, header_idx[1:]):
                if j == i + 1:
                    tmp.append(j)
                else:
                    subheader_idx.append(tmp)
                    tmp = [j]
            subheader_idx.append(tmp)

            # convert to float
            for row in table_2d:
                for cell in range(len(row)):
                    try:
                        row[cell] = float(row[cell].replace('−', '-').replace('–', '-').replace(',', ''))
                    except:
                        row[cell] = row[cell]

            cur_table = self.__table2json(table_2d, header_idx, subheader_idx, superrow_idx, table_num, table['title'],
                                          table['footer'], table['caption'])
            # merge headers
            sep = '|'
            for table in cur_table:
                headers = table['columns']
                new_header = []
                if not headers:
                    continue
                for col_idx in range(len(headers[0])):
                    new_element = ''
                    for r_idx in range(len(headers)):
                        new_element += str(headers[r_idx][col_idx]) + sep
                    new_element = new_element.rstrip(sep)
                    new_header.append(new_element)
                table['columns'] = new_header

            tables += cur_table

        table_json = {'tables': tables}
        table_json = self.__reformat_table_json(table_json)
        return table_json

    def __init__(self, soup, config, file_name, base_dir):
        self.file_path = file_name
        file_name = Path(file_name).name
        self.tableIdentifier = None
        self.base_dir = base_dir
        if re.search("_table_\d+\.html", file_name):
            self.tableIdentifier = file_name.split("/")[-1].split("_")[-1].split(".")[0]
        self.pval_regex = r'((\d+\.\d+)|(\d+))(\s?)[*××xX](\s{0,1})10[_]{0,1}([–−-])(\d+)'
        self.pval_scientific_regex = r'((\d+.\d+)|(\d+))(\s{0,1})[eE](\s{0,1})([–−-])(\s{0,1})(\d+)'
        self.tables = self.__main(soup, config)
        pass

    def to_dict(self):
        return self.tables, self.empty_tables
