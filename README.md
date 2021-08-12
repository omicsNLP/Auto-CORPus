git clone repo

cd into repo

python3 -m venv env

source venv/bin/activate

$ pip install .

Run the below command for a single file example

$ python run_app.py -c "configs/config_pmc.json" -t "output" -f "Tutorial/PMC4827154.html" 

run the below command for a directory of files example

$  python run_app.py -c "configs/config_pmc.json" -t "output" -f "pathTest" 
