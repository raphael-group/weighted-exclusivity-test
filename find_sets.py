#!/usr/bin/env python

# Load required modules
import sys, os, argparse, numpy as np, json
from itertools import combinations
from collections import defaultdict
from time import time

# Load WExT, ensuring that it is in the path (unless this script was moved)
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from wext import *

# Argument parser
def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-mf', '--mutation_files', type=str, required=True, nargs='*')
    parser.add_argument('-wf', '--weights_files', type=str, required=True, nargs='*')
    parser.add_argument('-k', '--gene_set_size', type=int, required=True)
    parser.add_argument('-paf', '--patient_annotation_file', type=str, required=False, default=None)
    parser.add_argument('-o', '--output_prefix', type=str, required=True)
    parser.add_argument('-f', '--min_frequency', type=int, default=1, required=False)
    parser.add_argument('-fdr', '--fdr_threshold', type=float, default=0.5, required=False)
    parser.add_argument('-c', '--num_cores', type=int, required=False, default=1)
    parser.add_argument('-t', '--test', type=str, required=False, default='WRE', choices=['WRE'])
    parser.add_argument('-m', '--method', type=str, required=False, default='Saddlepoint', choices=['Saddlepoint'])
    parser.add_argument('-s', '--statistic', type=str, required=True, choices=['exclusivity', 'any-co-occurrence', 'all-co-occurrence'])
    parser.add_argument('-v', '--verbose', type=int, required=False, default=1, choices=range(5))
    parser.add_argument('-r', '--report_invalids', action='store_true', default=False, required=False)
    parser.add_argument('--json_format', action='store_true', default=False, required=False)
    return parser

def get_permuted_files(permuted_matrix_directories, num_permutations):
    # Group and restrict the list of files we're testing
    permuted_directory_files = []
    for permuted_matrix_dir in permuted_matrix_directories:
        files = sorted(os.listdir(permuted_matrix_dir))
        permuted_matrices = [ '{}/{}'.format(permuted_matrix_dir, f) for f in files if f.lower().endswith('.json') ]
        permuted_directory_files.append( permuted_matrices[:num_permutations] )
    assert( len(files) == num_permutations for files in permuted_directory_files )

    return zip(*permuted_directory_files)

# Load a list of weights files, merging them at the patient and gene level.
# Note that if a (gene, patient) pair is present in more than one file, it will
# be overwritten.
def load_weight_files(weights_files, genes, patients, typeToGeneIndex, typeToPatientIndex, masterGeneToIndex, masterPatientToIndex):
    # Master matrix of all weights
    P = np.zeros((len(genes), len(patients)))
    for i, weights_file in enumerate(weights_files):
        # Load the weights matrix for this cancer type and update the entries appropriately.
        # Note that since genes/patients can be measured in multiple types, we need to map
        # each patient to the "master" index.
        type_P                 = np.load(weights_file)

        ty_genes               = set(typeToGeneIndex[i].keys()) & genes
        ty_gene_indices        = [ typeToGeneIndex[i][g] for g in ty_genes ]
        master_gene_indices    = [ masterGeneToIndex[g] for g in ty_genes ]

        ty_patients            = set(typeToPatientIndex[i].keys()) & patients
        ty_patient_indices     = [ typeToPatientIndex[i][p] for p in ty_patients ]
        master_patient_indices = [ masterPatientToIndex[p] for p in ty_patients ]

        master_mesh            = np.ix_(master_gene_indices, master_patient_indices)
        ty_mesh                = np.ix_(ty_gene_indices, ty_patient_indices)

        if np.any( P[master_mesh] > 0 ):
            raise ValueError("Different weights for same gene-patient pair")
        else:
            P[ master_mesh ] = type_P[ ty_mesh  ]

    # Set any zero entries to the minimum (pseudocount). The only reason for zeros is if
    #  a gene wasn't mutated at all in a particular dataset.
    P[P == 0] = np.min(P[P > 0])

    return dict( (g, P[masterGeneToIndex[g]]) for g in genes )

def load_mutation_files(mutation_files):
    typeToGeneIndex, typeToPatientIndex = [], []
    genes, patients, geneToCases = set(), set(), defaultdict(set)
    for i, mutation_file in enumerate(mutation_files):
        # Load ALL the data, we restrict by mutation frequency later
        mutation_data = load_mutation_data( mutation_file, 0 )
        _, type_genes, type_patients, typeGeneToCases, _, params, _ = mutation_data

        # We take the union of all patients and genes
        patients |= set(type_patients)
        genes    |= set(type_genes)

        # Record the mutations in each gene
        for g, cases in typeGeneToCases.iteritems(): geneToCases[g] |= cases

        # Record the genes, patients, and their indices for later
        typeToGeneIndex.append(dict(zip(type_genes, range(len(type_genes)))))
        typeToPatientIndex.append(dict(zip(type_patients, range(len(type_patients)))))

    return genes, patients, geneToCases, typeToGeneIndex, typeToPatientIndex

def run( args ):
    # Provide additional checks on arguments
    assert( len(args.mutation_files) == len(args.weights_files) )

    # Load the mutation data
    if args.verbose > 0:
        print ('-' * 30), 'Input Mutation Data', ('-' * 29)
    genes, patients, geneToCases, typeToGeneIndex, typeToPatientIndex = load_mutation_files( args.mutation_files )
    num_all_genes, num_patients = len(genes), len(patients)

    # Restrict to genes mutated in a minimum number of samples
    geneToCases = dict( (g, cases) for g, cases in geneToCases.iteritems() if g in genes and len(cases) >= args.min_frequency )
    genes     = set(geneToCases.keys())
    num_genes = len(genes)

    # Load patient annotations (if provided) and add per patient events
    if args.patient_annotation_file:
        annotationToPatients = load_patient_annotation_file(args.patient_annotation_file)
        annotations = set( annotationToPatients.keys() )
        genes |= annotations

        # Since we are looking for co-occurrence between exclusive sets with
        # an annotation A, we add events for each patient NOT annotated by
        # the given annotation
        for annotation, cases in annotationToPatients.iteritems():
            not_cases = patients - cases
            if len(not_cases) > 0:
                geneToCases[annotation] = not_cases
    else:
        annotations = set()

    if args.verbose > 0:
        print '- Genes:', num_all_genes
        print '- Patients:', num_patients
        print '- Genes mutated in >={} patients: {}'.format(args.min_frequency, num_genes)
        if args.patient_annotation_file:
            print '- Patient annotations:', len(annotations)

    # Load the weights (if necessary)

    # Create master versions of the indices
    masterGeneToIndex    = dict(zip(sorted(genes), range(num_genes)))
    masterPatientToIndex = dict( zip(sorted(patients), range(num_patients)) )
    geneToP = load_weight_files(args.weights_files, genes, patients, typeToGeneIndex, typeToPatientIndex, masterGeneToIndex, masterPatientToIndex)

    if args.verbose > 0: print ('-' * 31), 'Enumerating Sets', ('-' * 31)
    k = args.gene_set_size
    # Create a list of sets to test
    sets = list( frozenset(t) for t in combinations(genes, k) )
    num_sets = len(sets)

    if args.verbose  > 0: print 'k={}: {} sets...'.format(k, num_sets)
    # Run the test
    method = nameToMethod['Saddlepoint']
    test = nameToTest['WRE']
    statistic = nameToStatistic[args.statistic]
    setToPval, setToRuntime, setToFDR, setToObs = general_test_sets(sets, geneToCases, num_patients, method, test, statistic, geneToP, args.num_cores,
                                                            verbose=args.verbose, report_invalids=args.report_invalids)
    output_enumeration_table( args, k, setToPval, setToRuntime, setToFDR, setToObs, args.fdr_threshold )

if __name__ == '__main__': run( get_parser().parse_args(sys.argv[1:]) )
