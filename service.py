import sys
import makeRequiredPPRFiles as make
from flask import Flask
from flask.ext import restful

import simple_run

app = Flask(__name__)
api = restful.Api(app)

# Routes
# api.add_resource(version.Version, '/v1/analyses/hotnet2')

# Simple Run
api.add_resource(simple_run.SimpleRun, '/v1/analyses/hotnet2/simple')

if __name__ == '__main__':
    # 1. Initialization: build permuted networks
    make.run(make.get_parser().parse_args(sys.argv[1:]))
    app.run(host='0.0.0.0', debug=True, port=5000)



