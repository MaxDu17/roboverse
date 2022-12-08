#!/bin/bash

# running for debugging purposes
# python scripted_collect.py -n 5 -t 250 -e Widow250OfficeRand-v0 -pl tableclean -a table_clean -d office_TA
# python scripted_collect.py -n 5 -t 250 -e Widow250OfficeRand-v0 -pl pickplace_target -a target_place_success -d office_eraser

# real collection
# python scripted_collect.py -n 400 -t 250 -e Widow250OfficeRand-v0 -pl tableclean -a table_clean -d office_TA
# python scripted_collect.py -n 400 -t 250 -e Widow250OfficeRand-v0 -pl pickplace_target -a target_place_success -d office_eraser_more


# python scripted_collect.py -n 1200 -t 100 -e Widow250OfficeRand-v0 -pl pickplace_target -a target_place_success -d office_TA_pp_with_prop

# python scripted_collect.py -n 3 -t 100 -e Widow250OfficeRand-v0 -pl pickplace_target -a target_place_success -d eraser_drawer
# python scripted_collect.py -n 1000 -t 120 -e Widow250OfficeRand-v0 -pl tableclean -a table_clean -d office_single_tray_drawer \
#  --config ../roboverse/envs/configs/single_pp_eraser_drawer_TRAIN.json

# python scripted_collect.py -n 20 -t 120 -e Widow250OfficeRand-v0 -pl tableclean -a table_clean -d office_single_tray_drawer_expert \
#  --config ../roboverse/envs/configs/single_pp_eraser_drawer_TEST.json

 python scripted_collect.py -n 20 -t 120 -e Widow250OfficeRand-v0 -pl tableclean -a table_clean -d office_eraser_tray_shed_container_expert \
  --config ../roboverse/envs/configs/pp_welding_eraser_tray_shed_container_TEST.json
