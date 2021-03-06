import hnio
from collections import defaultdict

def get_nodes(cc, gene2heat, d_score, d_name):
    scores = d_score if d_score else gene2heat
    return [{'name': d_name.get(gene, gene), 'heat': scores[gene]} for gene in cc]

def get_edges(cc, edges, networkName, d_name):
    edgeData = list()
    for i in range(len(cc)):
        for j in range(i+1, len(cc)):
            gene1 = min(cc[i], cc[j])
            gene2 = max(cc[i], cc[j])
            if (gene1, gene2) in edges or (gene2, gene1) in edges:
                edgeData.append({'source': d_name.get(gene1, gene1), 'target': d_name.get(gene2, gene2), 'networks': [networkName]})

    return edgeData

def get_component_json(cc, gene2heat, edges, networkName, d_score, d_name):
    nodes = get_nodes(cc, gene2heat, d_score, d_name)
    cc_edges = get_edges(cc, edges, networkName, d_name)

    return {'nodes': nodes, 'edges': cc_edges}

def get_oncoprint_json(cc, snvs, cnas, d_name):
    cc = set(cc)
    samples = set()

    M = defaultdict(lambda: defaultdict(list))
    for mut in snvs + cnas:
        if mut.gene in cc:
            M[d_name.get(mut.gene, mut.gene)][mut.sample].append(mut.mut_type)
            samples.add(mut.sample)

    return M

def write_index_file(index_file, out_file, deltas):
    index = hnio.load_file(index_file)
    index += '<ul>\n'
    for delta in sorted(deltas):
        index += '<li><a href="delta%s/subnetworks.html">&delta; = %s</a></li>\n' % (delta, delta)
    index += '</ul>'
    hnio.write_file(out_file, index)
