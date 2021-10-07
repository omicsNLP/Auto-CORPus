<h3>Auto-CORPus</h3>

*Requires python 3.6+*

The Automated pipeline for Consistent Outputs from Research Publications (Auto-CORPus) is a tool for the standardisation and conversion of publication HTML to three convenient machine-interpretable outputs to support biomedical text analytics. Firstly, Auto-CORPus can be configured to convert HTML from various publication sources to [BioC format](http://bioc.sourceforge.net/). Secondly, Auto-CORPus transforms publication tables to a JSON format to store, exchange and annotate table data between text analytics systems. Finally, Auto-CORPus extracts abbreviations declared within publication text and provides an abbreviations JSON output that relates an abbreviation with the full definition.

We present a JSON format for sharing table content and metadata that is based on the BioC format. The [JSON schema](keyFiles/schema.json) for the tables JSON can be found within the [keyfiles](keyFiles) directory.

**Auto-CORPus recognises 2 types of input file which are:**

- Full text HTML documents covering the entire article
- HTML files which describe a single table

Current work in progress is extending this to include images of tables. See the [Alpha Testing](#alpha) section below.

Auto-CORPus does not provide functionality to retrieve input files directly from the publisher. Input file retrieval must be completed by the user in a way which the publisher permits.

Auto-CORPus relies on a standard naming convention to recognise the files and identify the correct order of tables. The naming convention can be seen below:

Full article HTML: {any_name_you_want}.html
- {any_name_you_want} is how Auto-CORPus will group articles and linked tables/image files

Linked table HTML: {any_name_you_want}_table_X.html
- {any_name_you_want} must be identical to the name given to the full text file followed by _table_X where X is the table number

If passing a single file via the file path then that file will be processed in the most suitable manner, if a directory is passed then 
Auto-CORPus will first group files based on common elements in their file name {any_name_you_want} and process all related files at once. Related files in separate directories will not be processed at the same time. Files processed at the same time will be output into the same files, an example input and output directory can be seen below:

**Input:**

    PMC1.html
    PMC1_table_1.html
    PMC1_table_2.html
    /subdir
        PMC1_table_3.html
        PMC1_table_4.html

**Output:**

    PMC1_bioc.json
    PMC1_abbreviations.json
    PMC1_tables.json (contains table 1 & 2 and any tables described within the main text)
    /subdir
        PMC1_tables.json (contains tables 3 & 4 only)
        
**Getting started:**

Clone the repo, e.g.:

$ git clone git@github.com:omicsNLP/Auto-CORPus.git or (using HTTPS) git clone https://github.com/omicsNLP/Auto-CORPus.git

$ cd Auto-CORPus

$ python3 -m venv env or (for Windows users) py -[v] -m venv env (where v is the version of Python used)

$ source env/bin/activate or (for Windows users) path/to/env/Scripts/activate.bat

$ pip install .

You might get an error here `ModuleNotFoundError: No module named 'skbuild'` if you do then run 

$ pip install --upgrade pip 

Or you might need to install the Microsoft Build Tools for Visual Studio 
(see https://www.scivision.dev/python-windows-visual-c-14-required for minimal installation requirements so that python-Levenshtein package can be installed)
first and then re-run

$ pip install .

Run the below command for a single file example

$ python run_app.py -c "configs/config_pmc.json" -t "output" -f "path/to/html/file" -o JSON

Run the below command for a directory of files example

$  python run_app.py -c "configs/config_pmc.json" -t "output" -f "path/to/directory/of/html/files" -o JSON

**Available arguments:**

`-f` (input file path) - file or directory to run Auto-CORPus on

`-t` (output file path) - file path where Auto-CORPus should output files

`-c` (config) - which config file to use

`-o`(output format) - either JSON or XML (defaults to JSON)


<h3><a name="alpha">Alpha testing</a></h3>

We are developing an Auto-CORPus plugin to process images of tables and we include an alpha version of this 
functionality. Table image files can be processed in either .png or .jpeg/jpg formats. We are working on improving the accuracy of both the table layout and character recognition aspects, and we will update this repo as the plugin advances.

We utilise [opencv](https://pypi.org/project/opencv-python/) for cell detection and [tesseract](https://github.com/tesseract-ocr/tesseract) for optical character recognition. Tesseract will need to be installed separately onto your system for the table image recognition aspect of Auto-CORPus to work. Please follow the guidance given by tesseract on how to do this.

We have made trained datasets available for use with this feature, but we will continue to train these datasets to 
increase their accuracy, and it is very likely that the trained datasets we offer will be updated frequently during
active development periods.

As with HTML input files, the image input files should be retrieved by the user in a way which the publisher permits. The naming convention is:

Table image file: {any_name_you_want}_table_X.png/jpg/jpeg
- {any_name_you_want} must be identical to the name given to the full text file followed by _table_X where X is the table number

**Additional argument:**

`-s` (trained dataset) - trained dataset to use for pytesseract OCR. Value should be given in a format
    recognised by pytesseract with a "+" between each datafile, such as "eng+all".
    
