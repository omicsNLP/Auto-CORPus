AutoCORPus recognises 3 tyes of file which are:

- Full text HTML documents covering the entire aticle
- HTML files which describe a single table
- Images of tables.

If passing a single file via the file path then that file will be processed in the most suitable 
manner, if a directory is passed then autoCORPus will first group files within directories based on common elements in 
their file name and process all related files at once. Related files in separate directories will not be processed at 
the same time. Files processed at the same time will be output into the same files, an example input and output directory
can be seen below:

input:

    PMC1.html
    PMC1_table_1.html
    PMC1_table_2.PNG
    /subdir
        PMC1_table_3.HTML
        PMC1_table_4.png

output:

    PMC1_bioc.json
    PMC1_abbreviations.json
    PMC1_tables.json (contains table 1 & 2 and any tables described within the main text)
    /subdir
        PMC1_tables.json (contains tables 3 & 4 only)
        

$ git clone git@github.com:Tom-Shorter/autoCORPus.git

$ cd autoCORPus

$ python3 -m venv env or (for Windows users) py -[v] -m venv env (where v is the version of Python used)

$ source env/bin/activate or (for Windows users) path/to/env/Scripts/activate.bat

$ pip install .

You might get an error here `ModuleNotFoundError: No module named 'skbuild'` if you do then run 

$ pip install --upgrade pip 

or you might need to install the Microsoft Build Tools for Visual Studio 
(see https://www.scivision.dev/python-windows-visual-c-14-required for minimal installation requirements so that python-Levenshtein package can be installed)
first and then re run 

$ pip install .

Run the below command for a single file example

$ python run_app.py -c "configs/config_pmc.json" -t "output" -f "path/to/html/file" -o JSON

run the below command for a directory of files example

$  python run_app.py -c "configs/config_pmc.json" -t "output" -f "path/to/directory/of/html/files" -o JSON

Available arguments:

-f (input file path) - file or directory to run autoCORPus on.

-o (output type) - either JSON or XML

-m (mirror from) - must be used with the file path argument, value is a directory which must appear within the file path structure, the output file structure will mirror the input file structure but begin from the provided directory (inclusively). e.g. filepath of /home/user/Desktop/Html, output directory of output and -m of Desktop results in an output directory of output/Desktop/Html, omitting -m would result in an output of output/home/user/Desktop/Html

-c (config) - which config file to use

