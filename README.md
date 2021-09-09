$ git clone https://github.com/Tom-Shorter/autoCORPus.git

$ cd autoCORPus

$ python3 -m venv env

$ source env/bin/activate

$ pip install .

You might get an error here `ModuleNotFoundError: No module named 'skbuild'` if you do then run $ pip install --upgrade pip first and then re run $ pip install .

Run the below command for a single file example

$ python run_app.py -c "configs/config_pmc.json" -t "output" -f "path/to/html/file" -o JSON

run the below command for a directory of files example

$  python run_app.py -c "configs/config_pmc.json" -t "output" -f "path/to/directory/of/html/files" -o JSON


