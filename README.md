*Requires python 3.6+*

**Auto-CORPus**

Automated pipeline for Consistent Outputs from Research Publications (Auto-CORPus) is a tool for the standardisation and conversion of publication HTML and table image files to three convenient machine-interpretable outputs to support biomedical text analytics. Firstly, Auto-CORPus can be configured to convert HTML from various publication sources to BioC. Secondly, Auto-CORPus transforms publication tables to a JSON format to store, exchange and annotate table data between text analytics systems. Finally, Auto-CORPus extracts abbreviations declared within publication text and provides an abbreviations JSON output that relates an abbreviation with the full definition.

The BioC specification does not include a data structure for representing publication table data, so we present a JSON format for sharing table content and metadata, the [JSON schema](keyFiles/schema.json) for which can be found within the [keyfiles](keyFiles) directory.

**Auto-CORPus recognises 3 types of file which are:**

- Full text HTML documents covering the entire article
- HTML files which describe a single table
- Images of tables. (WIP, still in Alpha, see [Alpha section](#alpha) below)

Auto-CORPus does not provide functionality to retrieve these files directly from the publisher, initial file retrieval must be completed by the user in a way which the publisher permits.

Auto-CORPus relies on a standard naming convention to recognise the files and identify the correct order of tables. The naming convention can be seen below:

Full article HTML: {any_name_you_want}.html
- {any_name_you_want} is how Auto-CORPus will group articles and linked tables/image files

Linked table HTML: {any_name_you_want}_table_X.html
- {any_name_you_want} must be identical to the name given to the full text file followed by _table_X where X is the table number.

Table image file [WIP]: {any_name_you_want}_table_X.png/jpg/jpeg
- {any_name_you_want} must be identical to the name given to the full text file followed by _table_X where X is the table number.

If passing a single file via the file path then that file will be processed in the most suitable manner, if a directory is passed then autoCORPus will first group files based on common elements in their file name {any_name_you_want} and process all related files at once. Related files in separate directories will not be processed at the same time. Files processed at the same time will be output into the same files, an example input and output directory can be seen below:

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

`-f` (input file path) - file or directory to run autoCORPus on.

`-o` (output type) - either JSON or XML (defaults to JSON).

`-c` (config) - which config file to use.


<h2><a name="alpha">Alpha section</a></h2>

We are looking to implement table image processing into auto-CORPus, we have included an alpha version of this 
functionality within this repo which can be tested simply by providing table image files in either .png or .jpeg/jpg 
formats. We are working on improving the accuracy of both the table layout and character recognition aspects, and we will
update this repo with any advancements made.

We utilise [opencv](https://pypi.org/project/opencv-python/) for cell detection and [tesseract](https://github.com/tesseract-ocr/tesseract) for optical character recognition. Tesseract will need to be installed separately onto your system for the table image recognition aspect of Auto-CORPus to work. Please follow the guidance given by tesseract on how to do so.

The table image recognition and processing code is self-contained, so updates to this feature will not influence the 
outputs from the HTML processing AC is built upon.

We have made trained datasets available for use with this feature, but we will continue to train these datasets to 
increase their accuracy, and it is very likely that the trained datasets we offer will be updated frequently during
active development periods.

We welcome constructive feedback about all facets of AC, but we would be especially keen to hear about ways of improving the table
image processing.

**Additional arguments:**

`-s` (trained dataset) - trained dataset to use for pytesseract OCR. Value should be given in a format
    recognised by pytesseract with a "+" between each datafile, such as "eng+all".
    
**Using Auto-CORPus as a python package and not a CLI tool***

Auto-CORPus is intended to become a standalone python package in the future as well as a CLI tool, the ground work has already been completed for this move and once you have ran `pip install .` AutoCORPus will be accessible as a python package within your environment. Auto-CORPus has not been submitted to a python package repository as of yet but this will be done as Auto-CORPus matures.

example python code:

```
import autoCORPus


AC = autoCORPus(config, base_dir=base_dir, main_text=main_text, linked_tables=linked_tables_list, table_images=table_images_list, trainedData=trained_data)


#config is the config file to use which tells AC how to parse the HTML provided

#base_dir is provided to neaten up the output filenames, e.g., base_dir = '/a/dir', main_text = 'a/dir/main' results in a file name of 'main'

#main_text is a single file path to the articles full HTML

#linked_tables is a list of file paths to linked table HTML's

#table_images is a list of file paths to table images

#trainedData is a pyTesseract formatted string of which trained datasets to use, e.g. All+eng, default is eng



BioC_output_as_dict = AC.to_bioc() # python dictionary output

BioC_output_as_JSON = AC.main_text_to_bioc_json(indent=2) # JSON string output

BioC_output_as_xml = AC.main_text_to_bioc_xml() # XML string output


BioC_tables_JSON = AC.tables_to_bioc_json(indent=2) # tables to JSON string output

BioC_abbreviations_JSON = AC.abbreviations_to_bioc_json(indent=2) # abbreviations to JSON string output
```


