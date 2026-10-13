#!/bin/ksh

rm -f mars.txt

i="2023-10-15"
until [[ $i > "2024-03-30" ]]; do

  ##### stage the data #####
  cat>mars.txt<< EOF

RETRIEVE,
  REPRES = BUFR,
  TYPE = OB,
  OBSTYPE = 1/2/170/172/176/178,
  DATE   =  $i, 
  TIME = 00,
  RANGE = 1439,
  AREA = 71/-11/33/35,
  TARGET = "/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/SYNOP/2023_2024/SYNOP_mannual_${i}.bufr" 

EOF

  mars mars.txt  


  i=$(date -I -d "$i + 1 day")

done # end i loop

