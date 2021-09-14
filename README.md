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

-o (output type) - either JSON or XML

-m (mirror from) - must be used with the file path argument, value is a directory which must appear within the file path structure, the output file structure will mimic the input file structure but begin from the provided directory (inclusively). e.g. filepath of /home/user/Desktop/Html, output directory of output and -m of Desktop results in an output directory of output/Desktop/Html, omitting -m would result in an output of output/home/user/Desktop/Html


