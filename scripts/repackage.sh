#!/bin/bash
# In August 2014 Sirko sent Geert a single ZIP file containing re-processed
# flux data organized in a directory structure, rather than as a single ZIP
# file per night/station combination.  The meteorflux viewer is setup to accept
# only the latter, hence this script repackages the data accordingly.

TARGET='/tmp/repackaged'
if [ ! -d $TARGET ]; then
    mkdir $TARGET
fi

for year in `ls`; do
    if [ -d $year ]; then
        echo "Entering $year"
        for night in `ls $year`; do
            if [ -d $year/$night ]; then
                for station in `ls $year/$night`; do
                    filename=${night}_${station^^}.zip
                    echo "Creating "$filename
                    zip -q -j $TARGET/$filename $year/$night/$station/*
                done
            fi
        done
    fi
done
