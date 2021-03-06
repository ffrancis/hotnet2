#!/usr/bin/python

# Load required modules
import sys, os, networkx as nx, scipy as sp, scipy.io
import os.path
sys.path.append(os.path.split(os.path.split(sys.argv[0])[0])[0])
from hotnet2 import hnap

# Parse arguments
def get_parser():
    description = 'Create the personalized pagerank matrix for the given '\
                  'network and restart probability beta.'
    parser = hnap.HotNetArgParser(description=description, fromfile_prefix_chars='@')
    parser.add_argument('-e', '--edgelist_file', required=True,
                        help='Location of edgelist file.')
    parser.add_argument('-i', '--gene_index_file', required=True,
                        help='Location of gene-index file.')
    parser.add_argument('-o', '--output_dir', required=True,
	                help="Output dir.")
    parser.add_argument('-p', '--prefix', required=True,
	                help="Output prefix.")
    parser.add_argument('-s', '--start_index', default=1, type=int,
	                help="Index to output edge list, etc..")
    parser.add_argument('-a', '--alpha', required=True, type=float,
	                help="Page Rank dampening factor.")
    parser.add_argument("--matlab", default=False, action="store_true",
                    help="Create the PPR matrix using an external call "\
                             "to a MATLAB script instead of Scipy.")
    parser.add_argument("--path_to_matlab_script", default='createPPRMat.m',
                    help="Path to MATLAB script if you want to use MATLAB to"\
                         " create the PPR matrix. Change this path if you are not"\
                         " running this script in the same directory as createPPRMat.m.")
    return parser

def run(args):
    # Load gene-index map
    arrs = [l.rstrip().split() for l in open(args.gene_index_file)]
    index2gene = dict((int(arr[0]), arr[1]) for arr in arrs)
    G = nx.Graph()
    G.add_nodes_from( index2gene.values() ) # in case any nodes have degree zero

    # Load graph
    print "* Loading PPI..."
    edges = [map(int, l.rstrip().split()[:2]) for l in open(args.edgelist_file)]
    G.add_edges_from( [(index2gene[u], index2gene[v]) for u,v in edges] )
    print "\t- Edges:", len(G.edges())
    print "\t- Nodes:", len(G.nodes())

    # Remove self-loops and restrict to largest connected component
    print "* Removing self-loops, multi-edges, and restricting to",
    print "largest connected component..."
    self_loops = [(u, v) for u, v in G.edges() if u == v]
    G.remove_edges_from( self_loops )
    G = G.subgraph( sorted(nx.connected_components( G ), key=lambda cc: len(cc),
                           reverse=True)[0] )
    nodes = sorted(G.nodes())
    n = len(nodes)
    print "\t- Largest CC Edges:", len( G.edges() )
    print "\t- Largest CC Nodes:", len( G.nodes() )

    # Set up output directory
    print "* Saving updated graph to file..."
    os.system( 'mkdir -p ' + args.output_dir )
    output_prefix = "{}/{}".format(args.output_dir, args.prefix)
    pprfile = "{}_ppr_{:g}.mat".format(output_prefix, args.alpha)
    
    # Index mapping for genes
    index_map = [ "{} {}".format(i+args.start_index, nodes[i]) for i in range(n) ]
    open("{}_index_genes".format(output_prefix), 'w').write( "\n".join(index_map) )

    # Edge list
    edges = [sorted([nodes.index(u) + args.start_index,
                     nodes.index(v) + args.start_index])
             for u, v in G.edges()]
    edgelist = [ "{} {} 1".format(u, v) for u, v in edges ]
    open("{}_edge_list".format(output_prefix), 'w').write( "\n".join(edgelist) )

    ## Create the PPR matrix either using Scipy or MATLAB
    # Create "walk" matrix (normalized adjacency matrix)
    print "* Creating PPR  matrix..."
    W = nx.to_numpy_matrix( G , nodelist=nodes, dtype='f' )
    W = W / W.sum(axis=1) # normalization step

    if not args.matlab:
        ## Create PPR matrix using Python
        from scipy.linalg import inv
        PPR = (1.0-args.alpha)*inv(sp.eye(n)-args.alpha*sp.transpose(W))            
        scipy.io.savemat( pprfile, dict(PPR=PPR), oned_as='column')
        
    else:
        ## Create PPR matrix using MATLAB
        # Set up a params file
        params = dict(W=W, outputfile=pprfile, alpha=args.alpha)
        scipy.io.savemat( "params.mat", params, oned_as='column')

        # Run the MATLAB script, then cleanup the params file
        if not os.path.isfile(args.path_to_matlab_script):
            sys.stderr.write("Warning: {} script not found! Proceeding anyway...\n".format(args.path_to_matlab_script))
        os.system('matlab -nojvm -nodisplay -nodesktop -nosplash < {}'.format(args.path_to_matlab_script))
        os.system( 'rm params.mat' )


if __name__ == "__main__":
    run(get_parser().parse_args(sys.argv[1:]))
