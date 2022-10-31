#!/bin/bash

# running for debugging purposes
# python scripted_collect.py -n 5 -t 250 -e Widow250OfficeRand-v0 -pl tableclean -a table_clean -d office_TA
# python scripted_collect.py -n 5 -t 250 -e Widow250OfficeRand-v0 -pl pickplace_target -a target_place_success -d office_eraser

# real collection
# python scripted_collect.py -n 400 -t 250 -e Widow250OfficeRand-v0 -pl tableclean -a table_clean -d office_TA
 python scripted_collect.py -n 400 -t 250 -e Widow250OfficeRand-v0 -pl pickplace_target -a target_place_success -d office_eraser_more
# python scripted_collect.py -n 400 -t 250 -e Widow250OfficeRand-v0 -pl pickplace_target -a target_place_success -d office_TA_pp