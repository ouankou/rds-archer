from flask import Flask, request, render_template, redirect, Response
from subprocess import PIPE, run
import flask
import os
import json
import subprocess
import time
from werkzeug import secure_filename
import logjson
UPLOAD_FOLDER = '/tmp/rds'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def api_root():
    return render_template('index.html', val="")


# benchmark API for Archer
@app.route('/benchmark', methods=['POST'])
def benchmark():
    print("request received")

    # Running first command
    cmd = "sh /home/rds/dataracebench/check-data-races.sh"
    tstart = time.time()
    result = run(cmd.split(),
                 stdout=PIPE,
                 stderr=subprocess.STDOUT,
                 universal_newlines=True)
    tend = time.time()
    benchmarkTime = tend - tstart
    print(benchmarkTime)
    if (result.returncode == 1):
        str = result.stderr
    else:
        str = result.stdout
    print(str)

    with open(os.path.join(app.config['UPLOAD_FOLDER'], "archerbenchmark.txt"),
              "w") as tsanfile:
        print("Benchmark time: ", benchmarkTime, file=tsanfile)
    return flask.make_response(flask.jsonify({'tsan': json.loads(str)}), 200)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    try:
        os.makedirs(UPLOAD_FOLDER)
    except FileExistsError:
        pass
    name = ""
    if request.method == "POST":
        if 'file' in request.files:
            f = request.files['file']
            if not f:
                print("file is empty")
                name = ""
            else:
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                name = f.filename
        else:
            name = ""

        # 1. Remove all the files in the benchmark folder.
        # 2. Copy the received input file to the benchmark folder.
        # 3. Run the test and generate the log file.
        cmd_list = [
            "/home/rds/rds-archer/check.sh"
         ]
        for cmd in cmd_list:
            result = run(cmd.split(), universal_newlines=True)

        # The output log may not exist because the tool doesn't support the input.
        # In this case, an empty JSON response will be returned.
        logFile = "/home/rds/dataracebench/results/log/" + name + ".archer.parser.log"
        if os.path.exists(logFile):
            jsonResult = logjson.jsonify(logFile)
        else:
            jsonResult = flask.jsonify({})
        if request.args.get('type') == 'json':
            return flask.make_response(jsonResult, 200)
        else:
            return render_template('index.html', val=output.split('\n'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
