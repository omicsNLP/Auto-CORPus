*Requires python 3.6+*

**AutoCORPus recognises 3 types of file which are:**

- Full text HTML documents covering the entire article
- HTML files which describe a single table
- Images of tables. (WIP, still in Alpha, see Alpha section below)

If passing a single file via the file path then that file will be processed in the most suitable 
manner, if a directory is passed then autoCORPus will first group files within directories based on common elements in 
their file name and process all related files at once. Related files in separate directories will not be processed at 
the same time. Files processed at the same time will be output into the same files, an example input and output directory
can be seen below:

**Input:**

    PMC1.html
    PMC1_table_1.html
    PMC1_table_2.png
    /subdir
        PMC1_table_3.HTML
        PMC1_table_4.png

**Output:**

    PMC1_bioc.json
    PMC1_abbreviations.json
    PMC1_tables.json (contains table 1 & 2 and any tables described within the main text)
    /subdir
        PMC1_tables.json (contains tables 3 & 4 only)
        
**Getting started:**

Clone the repo, e.g.:

$ git clone git@github.com:omicsNLP/Auto-CORPus.git or (using HTTPS) git clone https://github.com/Tom-Shorter/autoCORPus.git

$ cd autoCORPus

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

Available arguments:

`-f` (input file path) - file or directory to run autoCORPus on.

`-o` (output type) - either JSON or XML (defaults to JSON)

`-c` (config) - which config file to use


<h2>Alpha section</h2>

We are looking to implement table image processing into auto-CORPus, we have included an alpha version of this 
functionality within this repo which can be tested simply by providing table image files in either .png or .jpeg/jpg 
formats. We are working on improving the accuracy of both the table layout and character recognition aspects, and we will
update this repo with any advancements made.

The table image recognition and processing code is self-contained, so updates to this feature will not influence the 
outputs from the HTML processing AC is built upon.

We have made trained datasets available for use with this feature, but we will continue to train these datasets to 
increase their accuracy, and it is very likely that the trained datasets we offer will be updated frequently during
active development periods.

We welcome constructive feedback about all facets of AC, but we would be especially keen to hear about ways of improving the table
image processing.

**Additional arguments:**

`-s` (trained dataset) - trained dataset to use for pytesseract OCR. Value should be given in a format
    recognised by pytesseract with a "+" between each datafile, such as "eng+all"

