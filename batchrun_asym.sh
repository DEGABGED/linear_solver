#!/bin/bash

all_demands=(450 600 750 900 1050 1200 1350 1500 1650 1800)
batch_demands=(1350 1500 1650 1800)

for ns_d in "${batch_demands[@]}"
do
    for ew_d in "${all_demands[@]}"
    do
        if [ $ew_d -lt $ns_d ]
        then
            echo "Skipping demand ${ns_d}, ${ew_d} for symmetry"
            continue
        fi

        # Run the python script
        python batchrunner_script.py $ns_d $ew_d
        echo "Done with demand ${ns_d}, ${ew_d}"
    done
done

echo "All done"
