#!/usr/bin/env bash

znoyder browse-osp packages --output component,osp-project \
    | sort --key 1,2 \
    | uniq \
    | gawk '
      function add(array, component, project) {
          array[component][length(array[component]) + 1] = project
      }
      NF == 2 {
          component = $1
          project = $2
          add(projects, component, project)
      }
      END {
          print "---"
          PROCINFO["sorted_in"] = "@val_num_asc"
          for(component in projects) {
              print component ":"
              for(key in projects[component]) {
                  print "  - " projects[component][key]
              }
          }
      }
      ' \
    | tee projects.yml 
