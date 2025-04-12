[deployment]
run = "python main.py"
build = ["pip install -r requirements.txt"]

# Workflow to run the Flask app
[flask_app]
run = "python main.py"
onBoot = false