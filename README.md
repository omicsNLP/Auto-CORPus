# Auto-CORPus

[![DOI:10.1101/2021.01.08.425887](http://img.shields.io/badge/DOI-10.1101/2021.01.08.425887-BE2536.svg)](https://doi.org/10.1101/2021.01.08.425887)
[![DOI:10.3389/fdgth.2022.788124](http://img.shields.io/badge/DOI-10.3389/fdgth.2022.788124-70286A.svg)](https://doi.org/10.3389/fdgth.2022.788124)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/omicsNLP/Auto-CORPus/main.svg)](https://results.pre-commit.ci/latest/github/omicsNLP/Auto-CORPus/main)
[![PyPI version](https://badge.fury.io/py/autocorpus.svg)](https://badge.fury.io/py/autocorpus)
[![codecov](https://codecov.io/gh/omicsNLP/Auto-CORPus/graph/badge.svg?token=ZTKK4URM4A)](https://codecov.io/gh/omicsNLP/Auto-CORPus)

*Requires Python 3.10+* <!-- markdownlint-disable-line MD036 -->

The Automated pipeline for Consistent Outputs from Research Publications (Auto-CORPus) is a tool for the standardisation and conversion of publication HTML to three convenient machine-interpretable outputs to support biomedical text analytics. Firstly, Auto-CORPus can be configured to convert HTML from various publication sources to [BioC format]. Secondly, Auto-CORPus transforms publication tables to a JSON format to store, exchange and annotate table data between text analytics systems. Finally, Auto-CORPus extracts abbreviations declared within publication text and provides an abbreviations JSON output that relates an abbreviation with the full definition.

We present a JSON format for sharing table content and metadata that is based on the BioC format. The [JSON schema] for the tables JSON can be found within the [keyFiles] directory.

The documentation for Auto-CORPus is available on our [GitHub Pages site].

[BioC format]: http://bioc.sourceforge.net/
[JSON schema]: https://github.com/omicsNLP/Auto-CORPus/blob/main/keyFiles/table_schema.json
[keyFiles]: https://github.com/omicsNLP/Auto-CORPus/tree/main/keyFiles
[GitHub Pages site]: https://omicsnlp.github.io/Auto-CORPus/

## Installation

Install with pip

```sh
pip install autocorpus
```

## Usage

Run the below command for a single file example

```sh
auto-corpus -c "autocorpus/configs/config_pmc.json" -t "output" -f "path/to/html/file" -o JSON
```

Run the main app for a directory of files example

```sh
auto-corpus -c "autocorpus/configs/config_pmc.json" -t "output" -f "path/to/directory/of/html/files" -o JSON
```

### Available arguments

| Flag | Name             | Description                                               |
|------|------------------|-----------------------------------------------------------|
| `-f` | Input File Path  | File or directory to run Auto-CORPus on                   |
| `-t` | Output File Path | Directory path where Auto-CORPus should save output files |
| `-c` | Config           | Which config file to use                                  |
| `-o` | Output Format    | Either `JSON` or `XML` (defaults to `JSON`)               |

## Config files

If you wish to contribute or edit a config file then please follow the instructions in the [config guide].

Auto-CORPus is able to parse HTML from different publishers, which utilise different HTML structures and naming conventions. This is made possible by the inclusion of config files which tell Auto-CORPus how to identify specific sections of the article/table within the source HTML. We have supplied a config template along with example config files for [PubMed Central], [PLOS Genetics] and [Nature Genetics] in the [configs] directory. Users of Auto-CORPus can submit their own config files for different sources via the [issues] tab.

**Auto-CORPus recognises 2 types of input file which are:**

- Full text HTML documents covering the entire article
- HTML files which describe a single table

Auto-CORPus does not provide functionality to retrieve input files directly from the publisher. Input file retrieval must be completed by the user in a way which the publisher permits.

Auto-CORPus relies on a standard naming convention to recognise the files and identify the correct order of tables. The naming convention can be seen below:

Full article HTML: {any_name_you_want}.html

- {any_name_you_want} is how Auto-CORPus will group articles and linked tables/image files

Linked table HTML: {any_name_you_want}_table_X.html

- {any_name_you_want} must be identical to the name given to the full text file followed by_table_X where X is the table number

If passing a single file via the file path then that file will be processed in the most suitable manner, if a directory is passed then
Auto-CORPus will first group files based on common elements in their file name {any_name_you_want} and process all related files at once. Related files in separate directories will not be processed at the same time. Files processed at the same time will be output into the same files, an example input and output directory can be seen below:

**Input:**

```txt
PMC1.html
PMC1_table_1.html
PMC1_table_2.html
/subdir
    PMC1_table_3.html
    PMC1_table_4.html
```

**Output:**

```txt
PMC1_bioc.json
PMC1_abbreviations.json
PMC1_tables.json (contains table 1 & 2 and any tables described within the main text)
/subdir
    PMC1_tables.json (contains tables 3 & 4 only)
```

A log file is produced in the output directory providing details of the day/time Auto-CORPus was run,
the arguments used and information about which files were successfully/unsuccessfully processed with a relevant error message.

[config guide]: https://omicsnlp.github.io/Auto-CORPus/config_tutorial/
[PubMed Central]: https://github.com/omicsNLP/Auto-CORPus/blob/main/autocorpus/configs/config_pmc.json
[PLOS Genetics]: https://github.com/omicsNLP/Auto-CORPus/blob/main/autocorpus/configs/config_plos_genetics.json
[Nature Genetics]: https://github.com/omicsNLP/Auto-CORPus/blob/main/autocorpus/configs/config_nature_genetics.json
[configs]: https://github.com/omicsNLP/Auto-CORPus/tree/main/autocorpus/configs
[issues]: https://github.com/omicsNLP/Auto-CORPus/issues

## For developers

This is a Python application that uses [poetry](https://python-poetry.org) for packaging
and dependency management. It also provides [pre-commit](https://pre-commit.com/) hooks
for various linters and formatters and automated tests using
[pytest](https://pytest.org/) and [GitHub Actions](https://github.com/features/actions).

To get started:

1. [Download and install Poetry](https://python-poetry.org/docs/#installation) following the instructions for your OS.
1. Clone this repository and make it your working directory
1. Set up the virtual environment:

   ```sh
   poetry install
   ```

1. Activate the virtual environment (alternatively, ensure any Python-related command is preceded by `poetry run`):

   ```sh
   poetry shell
   ```

1. Install the git hooks:

   ```sh
   pre-commit install
   ```

1. Run the main app for a single file example:

   ```sh
   auto-corpus -c "autocorpus/configs/config_pmc.json" -t "output" -f "path/to/html/file" -o JSON
   ```

1. Run the main app for a directory of files example

   ```sh
   auto-corpus -c "autocorpus/configs/config_pmc.json" -t "output" -f "path/to/directory/of/html/files" -o JSON
   ```
