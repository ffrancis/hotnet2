import tempfile

from flask.ext.restful import reqparse
from flask.ext import restful

from flask import request


import runHotNet2 as hn2
import json


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

        finally:
            f.close()

        hn2.run(hn2.get_parser().parse_args(DEFAULT_ARGS))
        result = open('example/output/simple2/viz/subnetworks.json')
        data = json.load(result)
        cyjs = self.convert(data['subnetworks'])
        return cyjs, 200

    def convert(self, subnetworks):
        cyjs = []
        for key in subnetworks:

            subnetwork_list = subnetworks[key]
            for network in subnetwork_list:
                cynet = {
                    'elements': {
                        'nodes': [],
                        'edges': []
                    },
                    'data': {
                        'name': "hotnet2 delta: " + str(key)
                    }
                }
                nodes = network['nodes']
                edges = network['edges']

                cynet['elements']['nodes'] = self.get_nodes(nodes)
                cynet['elements']['edges'] = self.get_edges(edges)
                cyjs.append(cynet)

        return cyjs

    def get_nodes(self, original_nodes):
        nodes = []
        for n in original_nodes:
            node = {
                'data': {
                    'name': n['name'],
                    'id': n['name'],
                    'heat': n['heat']
                }
            }
            nodes.append(node)

        return nodes

    def get_edges(self, original_edges):
        edges = []
        for e in original_edges:
            edge = {
                'data': {
                    'source': e['source'],
                    'target': e['target']
                }
            }
            edges.append(edge)

        return edges
