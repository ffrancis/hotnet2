import json
import os
import numpy as np
import scipy.io
from constants import MAX_CC_SIZE, NUM_CCS, HEAT_JSON, JSON_OUTPUT, COMPONENTS_TSV, SIGNIFICANCE_TSV
from bin import findThreshold as ft
import heat as hnheat
import hnio
import hotnet2 as hn
import stats
import permutations as p

def run_helper(args, infmat_name, get_deltas_fn, extra_delta_args):
    """Helper shared by simpleRun and simpleRunClassic.
    """
    # create output directory if doesn't exist; warn if it exists and is not empty
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)
    if len(os.listdir(args.output_directory)) > 0:
        print("WARNING: Output directory is not empty. Any conflicting files will be overwritten. "
              "(Ctrl-c to cancel).")
    
    infmat = scipy.io.loadmat(args.infmat_file)[infmat_name]
    full_index2gene = hnio.load_index(args.infmat_index_file)
    
    using_json_heat = os.path.splitext(args.heat_file.lower())[1] == '.json'
    if using_json_heat:
        heat = json.load(open(args.heat_file))['heat']
    else:
        heat = hnio.load_heat_tsv(args.heat_file)
    print "* Loaded heat scores for %s genes" % len(heat)
    
    # filter out genes not in the network
    heat = hnheat.filter_heat_to_network_genes(heat, set(full_index2gene.values()))
    
    # genes with score 0 cannot be in output components, but are eligible for heat in permutations
    heat, addtl_genes = hnheat.filter_heat(heat, None, False, 'There are ## genes with heat score 0')
    
    deltas = get_deltas_fn(full_index2gene, heat, args.delta_permutations, args.num_cores, infmat, addtl_genes, *extra_delta_args)
    
    sim, index2gene = hn.similarity_matrix(infmat, full_index2gene, heat, True)

    results_files = []
    for delta in deltas:
        # create output directory
        delta_out_dir = args.output_directory + "/delta_" + str(delta)
        if not os.path.isdir(delta_out_dir):
            os.mkdir(delta_out_dir)
        
        # find connected components
        G = hn.weighted_graph(sim, index2gene, delta, directed=True)
        ccs = hn.connected_components(G, args.min_cc_size)
        
        # calculate significance (using all genes with heat scores)
        print "* Performing permuted heat statistical significance..."
        heat_permutations = p.permute_heat(heat, full_index2gene.values(),
                                           args.significance_permutations, addtl_genes,
                                           args.num_cores)
        sizes = range(2, 11)
        print "\t- Using no. of components >= k (k \\in",
        print "[%s, %s]) as statistic" % (min(sizes), max(sizes))
        sizes2counts = stats.calculate_permuted_cc_counts(infmat, full_index2gene,
                                                          heat_permutations, delta, sizes, True,
                                                          args.num_cores)
        real_counts = stats.num_components_min_size(G, sizes)
        size2real_counts = dict(zip(sizes, real_counts))
        sizes2stats = stats.compute_statistics(size2real_counts, sizes2counts,
                                               args.significance_permutations)
    
        # sort ccs list such that genes within components are sorted alphanumerically, and components
        # are sorted first by length, then alphanumerically by name of the first gene in the component
        ccs = [sorted(cc) for cc in ccs]
        ccs.sort(key=lambda comp: comp[0])
        ccs.sort(key=len, reverse=True)

        # write output
        if not using_json_heat:
            heat_dict = {"heat": heat, "parameters": {"heat_file": args.heat_file}}
            heat_out = open(os.path.abspath(delta_out_dir) + "/" + HEAT_JSON, 'w')
            json.dump(heat_dict, heat_out, indent=4)
            heat_out.close()
            args.heat_file = os.path.abspath(delta_out_dir) + "/" + HEAT_JSON
        
        args.delta = delta  # include delta in parameters section of output JSON
        output_dict = {"parameters": vars(args), "sizes": hn.component_sizes(ccs),
                       "components": ccs, "statistics": sizes2stats}
        hnio.write_significance_as_tsv(os.path.abspath(delta_out_dir) + "/" + SIGNIFICANCE_TSV,
                                       sizes2stats)
        
        json_out = open(os.path.abspath(delta_out_dir) + "/" + JSON_OUTPUT, 'w')
        json.dump(output_dict, json_out, indent=4)
        json_out.close()
        results_files.append( os.path.abspath(delta_out_dir) + "/" + JSON_OUTPUT )
        
        hnio.write_components_as_tsv(os.path.abspath(delta_out_dir) + "/" + COMPONENTS_TSV, ccs)

    # write visualization output if edge file given
    if args.edge_file:
        from bin import makeResultsWebsite as MRW
        viz_args = [ "-r" ] + results_files
        viz_args += ["-ef", args.edge_file, "-o", args.output_directory + "/viz" ]
        if args.network_name: viz_args += [ "-nn", args.network_name ]
        if args.display_score_file: viz_args += [ "-dsf", args.display_score_file ]
        if args.display_name_file: viz_args += [ "-dnf", args.display_name_file ]
        MRW.run( MRW.get_parser().parse_args(viz_args) )

def get_deltas_hotnet2(full_index2gene, heat, num_perms, num_cores, _infmat, _addtl_genes,
                       permuted_networks_path, infmat_name, max_cc_sizes):
    # find smallest delta
    deltas = ft.get_deltas_for_network(permuted_networks_path, heat, infmat_name, full_index2gene,
                                       MAX_CC_SIZE, max_cc_sizes, False, num_perms, num_cores)

    # and run HotNet with the median delta for each size
    return [np.median(deltas[size]) for size in deltas]

def get_deltas_classic(full_index2gene, heat, num_perms, num_cores, infmat, addtl_genes, min_cc_size, max_cc_size):
    # find delta that maximizes # CCs of size >= min_cc_size for each permuted data set
    deltas = ft.get_deltas_for_heat(infmat, full_index2gene, heat, addtl_genes, num_perms, NUM_CCS,
                                    [min_cc_size], True, num_cores)

    # find the multiple of the median delta s.t. the size of the largest CC in the real data
    # is <= MAX_CC_SIZE
    medianDelta = np.median(deltas[min_cc_size])

    sim, index2gene = hn.similarity_matrix(infmat, full_index2gene, heat, False)

    for i in range(1, 11):
        G = hn.weighted_graph(sim, index2gene, i*medianDelta)
        largest_cc_size = max([len(cc) for cc in hn.connected_components(G)])
        if largest_cc_size <= max_cc_size:
            break

    # and run HotNet with that multiple and the next 4 multiples
    return [i*medianDelta for i in range(i, i+5)]
