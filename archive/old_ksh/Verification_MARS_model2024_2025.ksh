#!/bin/ksh

#BaseDateS_arr=(20241015 20241101 20241201 20250101 20250201 20250301) 
#BaseDateF_arr=(20241031 20241130 20241231 20250131 20250228 20250331) 

BaseDateS_arr=(20241101 20250101 20250201 20250301) 
BaseDateF_arr=(20241130 20250131 20250228 20250331) 
#BaseDateS_arr=(20220301)
#BaseDateF_arr=(20220310)
DirDB=/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype2018_all/raw/raw_2024_2025/

# SETTING SOME VARIABLES

let len=${#BaseDateS_arr[@]}-1

for ind in $(seq 0 ${len}); do
    
    # DEFINING THE MONTH TO RETRIEVE
    BaseDateS=${BaseDateS_arr[${ind}]}
    BaseDateF=${BaseDateF_arr[${ind}]}

    ###################
    # MARS RETRIEVALS #
    ###################

    echo "Retrieving form Mars..."
    export MARS_MULTITARGET_STRICT_FORMAT=1 # to create file names with a standard format

    mars << EOF
#        retrieve,
#             class    =   od,
#             type     =   cf,
#            stream   =   enfo,
# 
#             expver   =   1, 
#             date     =   ${BaseDateS}/to/${BaseDateF}, 
#             time     =   00, 
#             levtype  =   sfc,
#             area     =   71/-11/33/35,
#              step     =   0/3/6/9/12/15/18/21/24/27/30/33/36/39/42/45/48/51/54/57/60/63/66/69/72/75/78/81/84/87/90/93/96/99/102/105/108/111/114/117/120/123/126/129/132/135/138/141/144/150/156/162/168, 
#             param    =   260048,  
#             fieldset =   total_rate_cf_pre
#         retrieve,
#             number   =   1/to/50,
#             type     =   pf,
#             param    =   260048, 
#             fieldset =   total_rate_pre
#         Compute,
#             formula  =  "total_rate_cf_pre*3600",
#             fieldset =  total_rate_cf   
#         Compute,
#             formula  =  "total_rate_pre*3600",
#             fieldset =  total_rate   
#         Write,
#             fieldset =  total_rate,
#             target   = "${DirDB}/total_prec_VERIF_{date}.grib"
#         Write,
#             fieldset =  total_rate_cf,
#             target   = "${DirDB}/total_prec_VERIF_{date}.grib"

        retrieve,
            class    =   od,
            type     =   cf,
            stream   =   enfo,
            expver   = 1, 
            date     =  ${BaseDateS}/to/${BaseDateF},
            time      = 00, 
            levtype  =   sfc,
            area     =  71/-11/33/35,
            step     =  0/3/6/9/12/15/18/21/24/27/30/33/36/39/42/45/48/51/54/57/60/63/66/69/72/75/78/81/84/87/90/93/96/99/102/105/108/111/114/117/120/123/126/129/132/135/138/141/144/150/156/162/168, 
            accuracy =   5,
            param    =   260015,
            fieldset   =  Prectype_control_raw   
        retrieve,
            number   =   1/to/50,
            type     =   pf,
            param    =   260015,
            fieldset  =  Prectype_raw 
        Write,
            fieldset =  Prectype_raw,
            target   = "${DirDB}/Prectype_raw_VERIF_{date}.grib"
        Write,
            fieldset =  Prectype_control_raw,
            target   = "${DirDB}/Prectype_raw_VERIF_{date}.grib"

EOF

done
