import tempfile

from flask.ext.restful import reqparse
from flask.ext import restful

from flask import request


import runHotNet2 as hn2


DEFAULT_ARGS = [
    '--runname', 'SimpleExample',
    '--infmat_file',  'example/influence_matrices/example_ppr_0.6.mat',
    '--infmat_index_file', 'example/example_gene_index.txt',
    '--permuted_networks_path', 'example/influence_matrices/permuted/##NUM##/example_ppr_0.6.mat',
    '--display_score_file', 'example/example.dscore',
    '--heat_file', 'example/example.heat',
    '--edge_file', 'example/example_edgelist.txt',
    '--output_directory', 'example/output/simple2',
    '--delta_permutations', '10',
    '--significance_permutations', '10',
    '--network_name', 'Example'
]


class SimpleRun(restful.Resource):
    def __init__(self):
        self.__parser = reqparse.RequestParser()

    def post(self):
        body = request.data
        self.__parser.add_argument('network', type=str, help='Target Network')
        options = self.__parser.parse_args()
        print(options)

        f = tempfile.TemporaryFile(mode='w+t')
        try:
            f.write(body)
            f.seek(0)
            heat = self.run2(f)

        finally:
            f.close()

        hn2.run(hn2.get_parser().parse_args(DEFAULT_ARGS))
        return heat, 200

    def run2(self, temp_file):
        heat = []
        for line in temp_file:

            parts = line.rstrip().split('\t')
            heat.append({
                'gene': parts[0],
                'score': parts[1]
            })
        return heat
