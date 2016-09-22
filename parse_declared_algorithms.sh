#!/bin/bash

sourcedir=$1
outdir=$2

grep -rI '\(DECLARE_ALGORITHM\|DECLARE_NEXUS_FILELOADER_ALGORITHM\|DECLARE_FILELOADER_ALGORITHM\|AlgorithmFactory.subscribe\)'\([A-Z]  $sourcedir > $outdir/declared-algorithms
cat $outdir/declared-algorithms | grep -v '/test/' | cut -d\( -f2 | cut -d\) -f1 | sed s/$/1/g | sed s/21$/\.v2/ | sed s/31$/\.v3/ | sed s/1$/\.v1/ > $outdir/all-algorithms
#for i in $(cat $outdir/all-algorithms); do echo -n "$i " && grep -c \ $i $outdir/algorithm-usage; done | grep 0$ | cut -d' ' -f1 | sort > $outdir/unused-algorithms

# list of deprecated algorithms
grep -rI DeprecatedAlgorithm $sourcedir | grep public | cut -d':' -f1 > $outdir/deprecated-algorithms
