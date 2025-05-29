# Inputs and Outputs

Auto-CORPus can be used directly on one file, or a list of files. However, to use it on
a directory containing multiple files and nested directories, there is an assumed
structure. This is useful for analysing an article along with its associated tables
and supplementary information.

## Input

Auto-CORPus processes two categories of biomedical literature: **full text with tables**
and **supplementary information**.

Full text input files can be in HTML, XML or PDF formats, with an option to process
standalone HTML files which describe a single table.

Supplementary information files can be in PDF, word processor (doc, docx), spreadsheet
(xlsx, xls, csv, tsv) and presentation (pptx, ppt, pptm, odp) formats.

Auto-CORPus relies on a prescriptive directory structure and naming convention to
distinguish and group full text, table and supplementary information files.

The input directory passed to Auto-CORPus should contain article full text files and
optional subdirectories for tables and supplementary information for each article.

The article full text file is named:

- `{article_name}.html` or `{article_name}.xml` or `{article_name}.pdf`

Article table HTML files are placed in a subdirectory named:

- `{article_name}_tbl`

The table files in the subdirectory must contain _X at the end of the file name, where X
is the table number.

- `{any_name_you_want}_X.html`

Article supplementary information files are placed in a subdirectory named:

- `{article_name}_si`

The supplementary information files in the subdirectory can have any name, but must
contain a `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.csv`, `.tsv`, `.pptx`, `.ppt`,
`.pptm` or `.odp` file extension.

## Output

Auto-COPRus will write output to the “root” location passed to it, replicating the input
directory structure.

<!-- markdownlint-disable MD033 -->
<table>
<tr>
<th>Input</th>
<th>Output</th>
</tr>
<tr>
<td>

```text
inputs
├── PMC1.html
├── PMC1_tbl
│   ├── results_tbl_1.html
│   └── results_tbl_2.html
└── PMC1_si
    └── suppl_methods.docx
```

</td>
<td>

```text
outputs
├── PMC1_bioc.json
├── PMC1_abbreviations.json
├── PMC1_tbl
│   └── PMC1_tables.json
└── PMC1_si
    └── suppl_methods.docx_bioc.json
```

</td>
</tr>
<tr>
<td>

```text
inputs
├── article1.pdf
└── article1_si
    ├── extended_results.xlsx
    └── file3454.pdf
```

</td>
<td>

```text
outputs
├── article1_bioc.json
├── article1_abbreviations.json
├── article1_tables.json
└── article1_si
    ├── extended_results.xlsx_tables.json
    └── file3454.pdf_bioc.json
```

</td>
</tr>
</table>
<!-- markdownlint-enable MD033 -->

For each full text file, a bioc and abbreviations json file is output to the root.

If a tables subdirectory was not given for the article, the tables json file is output
to the root.

If a tables subdirectory was given, the tables json file is output to the subdirectory.
The tables json contains all tables from the separate HTML files and any tables
described within the main text.

The processed supplementary files are output to the supplementary subdirectory. If
Auto-CORPus detects text in the input file, a bioc file is output with \_bioc.json
appended to the end of the original filename. If Auto-CORPus detects one or more tables
in the input file, a tables json file is output with \_tables.json appended to the end
of the original filename. If both text and tables are detected, then both formats will
be output.
