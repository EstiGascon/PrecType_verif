# R script. Bias verification depending on different precipitation rates for ENS precipitation type.
# Calculate the bias of ENS precipitation type variable for 5 different precipitation rates: 0.02,0.05,0.07,0.1 and 0,12 mm/h.
# We want to enforce the bias to 1 for each precipitation type. 
#---------------------------------------
# Estibaliz Gascon 10/06/2017
########################################

 PATH_plots <- '/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/Plots/Plots_2023_48r1esuite/' 
 Prates <- c('002','005','007','01','012') 

val <- '005' 
bias_rain0 <- list()
bias_rain24 <- list()
bias_rain96 <- list()
bias_snow0 <- list()
bias_snow24 <- list()
bias_snow96 <- list()
bias_freezrain0 <- list()
bias_freezrain24 <- list()
bias_freezrain96 <- list()
bias_freezdrizzle0 <- list()
bias_freezdrizzle24 <- list()
bias_freezdrizzle96 <- list()
bias_icepellets0 <- list()
bias_icepellets24 <- list()
bias_icepellets96 <- list()
bias_sleet0 <- list()
bias_sleet24 <- list()
bias_sleet96 <- list()
pi <- 0
  
for (val in Prates) {
  print(val)
  pi <- pi + 1
  
   PATH_model_mannual <- paste0('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite/ENS_Europe/ENS',val,'_Europe/') 
   PATH_SYNOP_mannual <- paste0('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite/SYN_Europe/SYN',val,'_Europe/') 
  
  ############################## READ MODEL #################################### 
  
 model_mannual_rain0 <- list.files(path=PATH_model_mannual,pattern="^Loc_rain_(.*)_(0|3|6|9|12|15|18|21).gpt$")
 model_mannual_rain24 <- list.files(path=PATH_model_mannual,pattern="^Loc_rain_(.*)_(24|27|30|33|36|39|42|45).gpt$")
 model_mannual_rain96 <- list.files(path=PATH_model_mannual,pattern="^Loc_rain_(.*)_(96|99|102|105|108|111|114|117).gpt$")
 # model_mannual_rain0 <- list.files(path=PATH_model_mannual,pattern="^Loc_rain_(.*)_(0|12|24).gpt$")
 # model_mannual_rain24 <- list.files(path=PATH_model_mannual,pattern="^Loc_rain_(.*)_(24|36|48).gpt$")
 # model_mannual_rain96 <- list.files(path=PATH_model_mannual,pattern="^Loc_rain_(.*)_(96|108|120).gpt$")

  MODEL_mannual_rain0 <- file.path(PATH_model_mannual, model_mannual_rain0)
  MODEL_mannual_rain24 <- file.path(PATH_model_mannual, model_mannual_rain24)
  MODEL_mannual_rain96 <- file.path(PATH_model_mannual, model_mannual_rain96)
  
  
  #lstmod_rain_man0 <- lapply(MODEL_mannual_rain0, read.table,  header=FALSE, comment.char="#")
  
  lstmod_rain_man0 <- lapply(MODEL_mannual_rain0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_rain_man0 <- lapply(lstmod_rain_man0, function(x){x[, 6]})
  
  MOD_man_rain0_list <- NULL
  for (i in 1:length(lstmod_rain_man0)) {
    MOD_man_rain0_list <- append(MOD_man_rain0_list, lstmod_rain_man0[[i]])
  }
  
  lstmod_rain_man24 <- lapply(MODEL_mannual_rain24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_rain_man24 <- lapply(lstmod_rain_man24, function(x){x[, 6]})
  
  MOD_man_rain24_list <- NULL
  for (i in 1:length(lstmod_rain_man24)) {
    MOD_man_rain24_list <- append(MOD_man_rain24_list, lstmod_rain_man24[[i]])
  }
  
  lstmod_rain_man96 <- lapply(MODEL_mannual_rain96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_rain_man96 <- lapply(lstmod_rain_man96, function(x){x[, 6]})
  
  MOD_man_rain96_list <- NULL
  for (i in 1:length(lstmod_rain_man96)) {
    MOD_man_rain96_list <- append(MOD_man_rain96_list, lstmod_rain_man96[[i]])
  }
  
  
  ############################## READ SYNOP ####################################
  
  synop_mannual_rain0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_rain_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  synop_mannual_rain24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_rain_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  synop_mannual_rain96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_rain_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  #  synop_mannual_rain0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_rain_(.*)_(0|12|24).gpt$")
  #  synop_mannual_rain24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_rain_(.*)_(24|36|48).gpt$")
  #  synop_mannual_rain96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_rain_(.*)_(96|108|120).gpt$")
  
  SYNOP_mannual_rain0 <- file.path(PATH_SYNOP_mannual, synop_mannual_rain0)
  SYNOP_mannual_rain24 <- file.path(PATH_SYNOP_mannual, synop_mannual_rain24)
  SYNOP_mannual_rain96 <- file.path(PATH_SYNOP_mannual, synop_mannual_rain96)
  
  lstsyn_rain_man0 <- lapply(SYNOP_mannual_rain0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_rain_man0 <- lapply(lstsyn_rain_man0, function(x){x[, 6]})
  
  SYN_man_rain0_list <- NULL
  for (i in 1:length(lstsyn_rain_man0)) {
    SYN_man_rain0_list <- append(SYN_man_rain0_list, lstsyn_rain_man0[[i]])
  }
  
  lstsyn_rain_man24 <- lapply(SYNOP_mannual_rain24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_rain_man24 <- lapply(lstsyn_rain_man24, function(x){x[, 6]})
  
  SYN_man_rain24_list <- NULL
  for (i in 1:length(lstsyn_rain_man24)) {
    SYN_man_rain24_list <- append(SYN_man_rain24_list, lstsyn_rain_man24[[i]])
  }
  
  lstsyn_rain_man96 <- lapply(SYNOP_mannual_rain96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_rain_man96 <- lapply(lstsyn_rain_man96, function(x){x[, 6]})
  
  SYN_man_rain96_list <- NULL
  for (i in 1:length(lstsyn_rain_man96)) {
    SYN_man_rain96_list <- append(SYN_man_rain96_list, lstsyn_rain_man96[[i]])
  }
  
  ################ VERIFICATION ROC #################################################################
  library(verification)
  library(ROCR)
  library(reshape)
  
  mat0_rain <- matrix(NA, ncol = 51, nrow = length(MOD_man_rain0_list))
  for (i in 1:length(MOD_man_rain0_list)) {
   # print(i)
    if(MOD_man_rain0_list[i]>100) {MOD_man_rain0_list[i] <- 100} 
    MOD_man_rain0_list_YES <- round((MOD_man_rain0_list[i]*51)/100)
    list_MODyes0 <- rep(1, MOD_man_rain0_list_YES)
    MOD_man_rain0_list_NO <- round(((100-MOD_man_rain0_list[i])*51)/100)
    list_MODno0 <- rep(0, MOD_man_rain0_list_NO)
    list_MODyesno0 <- append(list_MODyes0,list_MODno0)
    mat0_rain[i,] <- list_MODyesno0
  }
  mat0_rain_vect <- as.vector(t(mat0_rain))
  
  mat_SYN_rain0 <- matrix(NA, ncol = 51, nrow = length(SYN_man_rain0_list))
  for (i in 1:length(SYN_man_rain0_list)) {
    list_SYN0 <- rep(SYN_man_rain0_list[i], 51)
    mat_SYN_rain0[i,] <- list_SYN0
  }
  mat_SYN_rain0_vect <- as.vector(t(mat_SYN_rain0))
  
  matSYN_MOD0_vec <- data.frame("Syn" = mat_SYN_rain0_vect, "Mod" = mat0_rain_vect, 
                                "a" = ifelse(mat_SYN_rain0_vect == 1 & mat0_rain_vect == 1, 1, 0),
                                "b" = ifelse(mat_SYN_rain0_vect == 0 & mat0_rain_vect == 1, 1, 0),
                                "c" = ifelse(mat_SYN_rain0_vect == 1 & mat0_rain_vect == 0, 1, 0),
                                "d" = ifelse(mat_SYN_rain0_vect == 0 & mat0_rain_vect == 0, 1, 0))
  
  a0_vec <- sum(matSYN_MOD0_vec$a)
  b0_vec <- sum(matSYN_MOD0_vec$b)
  c0_vec <- sum(matSYN_MOD0_vec$c)
  d0_vec <- sum(matSYN_MOD0_vec$d)
  
  write.table(c(a0_vec,b0_vec,c0_vec,d0_vec), file=paste0(PATH_model_mannual,'indexes_rain0_',val,'.txt'), row.names=F, col.names=F) 
  
  bias_rain0[pi] <-  (a0_vec+b0_vec)/(a0_vec+c0_vec)
  names(bias_rain0)[pi] <- paste0("BIAS0_probs_rain",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_rain24_list","SYN_man_rain24_list","MOD_man_rain96_list","SYN_man_rain96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  mat24_rain <- matrix(NA, ncol = 51, nrow = length(MOD_man_rain24_list))
  for (i in 1:length(MOD_man_rain24_list)) {
    #  print(i)
    if(MOD_man_rain24_list[i]>100) {MOD_man_rain24_list[i] <- 100} 
    MOD_man_rain24_list_YES <- round((MOD_man_rain24_list[i]*51)/100)
    list_MODyes24 <- rep(1, MOD_man_rain24_list_YES)
    MOD_man_rain24_list_NO <- round(((100-MOD_man_rain24_list[i])*51)/100)
    list_MODno24 <- rep(0, MOD_man_rain24_list_NO)
    list_MODyesno24 <- append(list_MODyes24,list_MODno24)
    mat24_rain[i,] <- list_MODyesno24
  }
  mat24_rain_vect <- as.vector(t(mat24_rain))
  
  
  mat_SYN_rain24 <- matrix(NA, ncol = 51, nrow = length(SYN_man_rain24_list))
  for (i in 1:length(SYN_man_rain24_list)) {
    list_SYN24 <- rep(SYN_man_rain24_list[i], 51)
    mat_SYN_rain24[i,] <- list_SYN24
  }
  mat_SYN_rain24_vect <- as.vector(t(mat_SYN_rain24))
  
  matSYN_MOD24_vec <- data.frame("Syn" = mat_SYN_rain24_vect, "Mod" = mat24_rain_vect, 
                                 "a" = ifelse(mat_SYN_rain24_vect == 1 & mat24_rain_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_rain24_vect == 0 & mat24_rain_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_rain24_vect == 1 & mat24_rain_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_rain24_vect == 0 & mat24_rain_vect == 0, 1, 0))
  
  a24_vec <- sum(matSYN_MOD24_vec$a)
  b24_vec <- sum(matSYN_MOD24_vec$b)
  c24_vec <- sum(matSYN_MOD24_vec$c)
  d24_vec <- sum(matSYN_MOD24_vec$d)
  
  write.table(c(a24_vec,b24_vec,c24_vec,d24_vec), file=paste0(PATH_model_mannual,'indexes_rain24_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_rain24[pi] <-  (a24_vec+b24_vec)/(a24_vec+c24_vec)
  names(bias_rain24)[pi] <- paste0("BIAS24_probs_rain",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_rain96_list","SYN_man_rain96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  
  mat96_rain <- matrix(NA, ncol = 51, nrow = length(MOD_man_rain96_list))
  for (i in 1:length(MOD_man_rain96_list)) {
    #  print(i)
    if(MOD_man_rain96_list[i]>100) {MOD_man_rain96_list[i] <- 100} 
    MOD_man_rain96_list_YES <- round((MOD_man_rain96_list[i]*51)/100)
    list_MODyes96 <- rep(1, MOD_man_rain96_list_YES)
    MOD_man_rain96_list_NO <- round(((100-MOD_man_rain96_list[i])*51)/100)
    list_MODno96 <- rep(0, MOD_man_rain96_list_NO)
    list_MODyesno96 <- append(list_MODyes96,list_MODno96)
    mat96_rain[i,] <- list_MODyesno96
  }
  mat96_rain_vect <- as.vector(t(mat96_rain))
  
  mat_SYN_rain96 <- matrix(NA, ncol = 51, nrow = length(SYN_man_rain96_list))
  for (i in 1:length(SYN_man_rain96_list)) {
    list_SYN96 <- rep(SYN_man_rain96_list[i], 51)
    mat_SYN_rain96[i,] <- list_SYN96
  }
  mat_SYN_rain96_vect <- as.vector(t(mat_SYN_rain96))
  
  
  matSYN_MOD96_vec <- data.frame("Syn" = mat_SYN_rain96_vect, "Mod" = mat96_rain_vect, 
                                 "a" = ifelse(mat_SYN_rain96_vect == 1 & mat96_rain_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_rain96_vect == 0 & mat96_rain_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_rain96_vect == 1 & mat96_rain_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_rain96_vect == 0 & mat96_rain_vect == 0, 1, 0))
  
  a96_vec <- sum(matSYN_MOD96_vec$a)
  b96_vec <- sum(matSYN_MOD96_vec$b)
  c96_vec <- sum(matSYN_MOD96_vec$c)
  d96_vec <- sum(matSYN_MOD96_vec$d)
  
  write.table(c(a96_vec,b96_vec,c96_vec,d96_vec), file=paste0(PATH_model_mannual,'indexes_rain96_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_rain96[pi] <- (a96_vec+b96_vec)/(a96_vec+c96_vec)
  names(bias_rain96)[pi] <- paste0("BIAS96_probs_rain",val) 
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  #******************************************* SNOW 
  ############################## READ MODEL ####################################
  
  model_mannual_snow0 <- list.files(path=PATH_model_mannual,pattern="^Loc_snow_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  model_mannual_snow24 <- list.files(path=PATH_model_mannual,pattern="^Loc_snow_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  model_mannual_snow96 <- list.files(path=PATH_model_mannual,pattern="^Loc_snow_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  #  model_mannual_snow0 <- list.files(path=PATH_model_mannual,pattern="^Loc_snow_(.*)_(0|12|24).gpt$")
  #  model_mannual_snow24 <- list.files(path=PATH_model_mannual,pattern="^Loc_snow_(.*)_(24|36|48).gpt$")
  # model_mannual_snow96 <- list.files(path=PATH_model_mannual,pattern="^Loc_snow_(.*)_(96|108|120).gpt$")
  
  MODEL_mannual_snow0 <- file.path(PATH_model_mannual, model_mannual_snow0)
  MODEL_mannual_snow24 <- file.path(PATH_model_mannual, model_mannual_snow24)
  MODEL_mannual_snow96 <- file.path(PATH_model_mannual, model_mannual_snow96)
  
  
  lstmod_snow_man0 <- lapply(MODEL_mannual_snow0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_snow_man0 <- lapply(lstmod_snow_man0, function(x){x[, 6]})
  
  MOD_man_snow0_list <- NULL
  for (i in 1:length(lstmod_snow_man0)) {
    MOD_man_snow0_list <- append(MOD_man_snow0_list, lstmod_snow_man0[[i]])
  }
  
  lstmod_snow_man24 <- lapply(MODEL_mannual_snow24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_snow_man24 <- lapply(lstmod_snow_man24, function(x){x[, 6]})
  
  MOD_man_snow24_list <- NULL
  for (i in 1:length(lstmod_snow_man24)) {
    MOD_man_snow24_list <- append(MOD_man_snow24_list, lstmod_snow_man24[[i]])
  }
  
  lstmod_snow_man96 <- lapply(MODEL_mannual_snow96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_snow_man96 <- lapply(lstmod_snow_man96, function(x){x[, 6]})
  
  MOD_man_snow96_list <- NULL
  for (i in 1:length(lstmod_snow_man96)) {
    MOD_man_snow96_list <- append(MOD_man_snow96_list, lstmod_snow_man96[[i]])
  }
  
  # #****** wetsnow *******
  
  model_mannual_wetsnow0 <- list.files(path=PATH_model_mannual,pattern="^Loc_wetsnow_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  model_mannual_wetsnow24 <- list.files(path=PATH_model_mannual,pattern="^Loc_wetsnow_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  model_mannual_wetsnow96 <- list.files(path=PATH_model_mannual,pattern="^Loc_wetsnow_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  
  #  model_mannual_wetsnow0 <- list.files(path=PATH_model_mannual,pattern="^Loc_wetsnow_(.*)_(0|12|24).gpt$")
  #  model_mannual_wetsnow24 <- list.files(path=PATH_model_mannual,pattern="^Loc_wetsnow_(.*)_(24|36|48).gpt$")
  #  model_mannual_wetsnow96 <- list.files(path=PATH_model_mannual,pattern="^Loc_wetsnow_(.*)_(96|108|120).gpt$")
  
  MODEL_mannual_wetsnow0 <- file.path(PATH_model_mannual, model_mannual_wetsnow0)
  MODEL_mannual_wetsnow24 <- file.path(PATH_model_mannual, model_mannual_wetsnow24)
  MODEL_mannual_wetsnow96 <- file.path(PATH_model_mannual, model_mannual_wetsnow96)
  
  lstmod_wetsnow_man0 <- lapply(MODEL_mannual_wetsnow0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_wetsnow_man0 <- lapply(lstmod_wetsnow_man0, function(x){x[, 6]})
  
  MOD_man_wetsnow0_list <- NULL
  for (i in 1:length(lstmod_wetsnow_man0)) {
    MOD_man_wetsnow0_list <- append(MOD_man_wetsnow0_list, lstmod_wetsnow_man0[[i]])
  }
  
  lstmod_wetsnow_man24 <- lapply(MODEL_mannual_wetsnow24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_wetsnow_man24 <- lapply(lstmod_wetsnow_man24, function(x){x[, 6]})
  
  MOD_man_wetsnow24_list <- NULL
  for (i in 1:length(lstmod_wetsnow_man24)) {
    MOD_man_wetsnow24_list <- append(MOD_man_wetsnow24_list, lstmod_wetsnow_man24[[i]])
  }
  
  lstmod_wetsnow_man96 <- lapply(MODEL_mannual_wetsnow96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_wetsnow_man96 <- lapply(lstmod_wetsnow_man96, function(x){x[, 6]})
  
  MOD_man_wetsnow96_list <- NULL
  for (i in 1:length(lstmod_wetsnow_man96)) {
    MOD_man_wetsnow96_list <- append(MOD_man_wetsnow96_list, lstmod_wetsnow_man96[[i]])
  }
  
  MOD_man_snow0_list = round(MOD_man_snow0_list,2) + round(MOD_man_wetsnow0_list,2)
  MOD_man_snow24_list = round(MOD_man_snow24_list,2) + round(MOD_man_wetsnow24_list,2)
  MOD_man_snow96_list = round(MOD_man_snow96_list,2) + round(MOD_man_wetsnow96_list,2)
  
  ############################## READ SYNOP ####################################
  
  synop_mannual_snow0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_snow_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  synop_mannual_snow24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_snow_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  synop_mannual_snow96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_snow_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  #  synop_mannual_snow0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_snow_(.*)_(0|12|24).gpt$")
  #  synop_mannual_snow24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_snow_(.*)_(24|36|48).gpt$")
  #  synop_mannual_snow96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_snow_(.*)_(96|108|120).gpt$")
  
  SYNOP_mannual_snow0 <- file.path(PATH_SYNOP_mannual, synop_mannual_snow0)
  SYNOP_mannual_snow24 <- file.path(PATH_SYNOP_mannual, synop_mannual_snow24)
  SYNOP_mannual_snow96 <- file.path(PATH_SYNOP_mannual, synop_mannual_snow96)
  
  lstsyn_snow_man0 <- lapply(SYNOP_mannual_snow0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_snow_man0 <- lapply(lstsyn_snow_man0, function(x){x[, 6]})
  
  SYN_man_snow0_list <- NULL
  for (i in 1:length(lstsyn_snow_man0)) {
    SYN_man_snow0_list <- append(SYN_man_snow0_list, lstsyn_snow_man0[[i]])
  }
  
  lstsyn_snow_man24 <- lapply(SYNOP_mannual_snow24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_snow_man24 <- lapply(lstsyn_snow_man24, function(x){x[, 6]})
  
  SYN_man_snow24_list <- NULL
  for (i in 1:length(lstsyn_snow_man24)) {
    SYN_man_snow24_list <- append(SYN_man_snow24_list, lstsyn_snow_man24[[i]])
  }
  
  lstsyn_snow_man96 <- lapply(SYNOP_mannual_snow96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_snow_man96 <- lapply(lstsyn_snow_man96, function(x){x[, 6]})
  
  SYN_man_snow96_list <- NULL
  for (i in 1:length(lstsyn_snow_man96)) {
    SYN_man_snow96_list <- append(SYN_man_snow96_list, lstsyn_snow_man96[[i]])
  }
  
  
  ################ VERIFICATION ROC #################################################################
  library(verification)
  library(ROCR)
  
  
  MOD_man_snow0_list[MOD_man_snow0_list>100] <- 100
  MOD_man_snow0_list[MOD_man_snow0_list>100] <- 100
  
  
  
  mat0_snow <- matrix(NA, ncol = 51, nrow = length(MOD_man_snow0_list))
  for (i in 1:length(MOD_man_snow0_list)) {
    # print(i)
    if(MOD_man_snow0_list[i]>100) {MOD_man_snow0_list[i] <- 100} 
    MOD_man_snow0_list_YES <- round((MOD_man_snow0_list[i]*51)/100)
    list_MODyes0 <- rep(1, MOD_man_snow0_list_YES)
    MOD_man_snow0_list_NO <- round(((100-MOD_man_snow0_list[i])*51)/100)
    list_MODno0 <- rep(0, MOD_man_snow0_list_NO)
    list_MODyesno0 <- append(list_MODyes0,list_MODno0)
    mat0_snow[i,] <- list_MODyesno0
  }
  mat0_snow_vect <- as.vector(t(mat0_snow))
  
  mat_SYN_snow0 <- matrix(NA, ncol = 51, nrow = length(SYN_man_snow0_list))
  for (i in 1:length(SYN_man_snow0_list)) {
    list_SYN0 <- rep(SYN_man_snow0_list[i], 51)
    mat_SYN_snow0[i,] <- list_SYN0
  }
  mat_SYN_snow0_vect <- as.vector(t(mat_SYN_snow0))
  
  matSYN_MOD0_vec <- data.frame("Syn" = mat_SYN_snow0_vect, "Mod" = mat0_snow_vect, 
                                "a" = ifelse(mat_SYN_snow0_vect == 1 & mat0_snow_vect == 1, 1, 0),
                                "b" = ifelse(mat_SYN_snow0_vect == 0 & mat0_snow_vect == 1, 1, 0),
                                "c" = ifelse(mat_SYN_snow0_vect == 1 & mat0_snow_vect == 0, 1, 0),
                                "d" = ifelse(mat_SYN_snow0_vect == 0 & mat0_snow_vect == 0, 1, 0))
  
  a0_vec <- sum(matSYN_MOD0_vec$a)
  b0_vec <- sum(matSYN_MOD0_vec$b)
  c0_vec <- sum(matSYN_MOD0_vec$c)
  d0_vec <- sum(matSYN_MOD0_vec$d)
  
  write.table(c(a0_vec,b0_vec,c0_vec,d0_vec), file=paste0(PATH_model_mannual,'indexes_snow0_',val,'.txt'), row.names=F, col.names=F) 
  
  bias_snow0[pi] <-  (a0_vec+b0_vec)/(a0_vec+c0_vec)
  names(bias_snow0)[pi] <- paste0("BIAS0_probs_snow",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_snow24_list","SYN_man_snow24_list","MOD_man_snow96_list","SYN_man_snow96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  mat24_snow <- matrix(NA, ncol = 51, nrow = length(MOD_man_snow24_list))
  for (i in 1:length(MOD_man_snow24_list)) {
    #  print(i)
    if(MOD_man_snow24_list[i]>100) {MOD_man_snow24_list[i] <- 100} 
    MOD_man_snow24_list_YES <- round((MOD_man_snow24_list[i]*51)/100)
    list_MODyes24 <- rep(1, MOD_man_snow24_list_YES)
    MOD_man_snow24_list_NO <- round(((100-MOD_man_snow24_list[i])*51)/100)
    list_MODno24 <- rep(0, MOD_man_snow24_list_NO)
    list_MODyesno24 <- append(list_MODyes24,list_MODno24)
    mat24_snow[i,] <- list_MODyesno24
  }
  mat24_snow_vect <- as.vector(t(mat24_snow))
  
  
  mat_SYN_snow24 <- matrix(NA, ncol = 51, nrow = length(SYN_man_snow24_list))
  for (i in 1:length(SYN_man_snow24_list)) {
    list_SYN24 <- rep(SYN_man_snow24_list[i], 51)
    mat_SYN_snow24[i,] <- list_SYN24
  }
  mat_SYN_snow24_vect <- as.vector(t(mat_SYN_snow24))
  
  matSYN_MOD24_vec <- data.frame("Syn" = mat_SYN_snow24_vect, "Mod" = mat24_snow_vect, 
                                 "a" = ifelse(mat_SYN_snow24_vect == 1 & mat24_snow_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_snow24_vect == 0 & mat24_snow_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_snow24_vect == 1 & mat24_snow_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_snow24_vect == 0 & mat24_snow_vect == 0, 1, 0))
  
  a24_vec <- sum(matSYN_MOD24_vec$a)
  b24_vec <- sum(matSYN_MOD24_vec$b)
  c24_vec <- sum(matSYN_MOD24_vec$c)
  d24_vec <- sum(matSYN_MOD24_vec$d)
  
  write.table(c(a24_vec,b24_vec,c24_vec,d24_vec), file=paste0(PATH_model_mannual,'indexes_snow24_',val,'.txt'), row.names=F, col.names=F) 
  
  bias_snow24[pi] <-  (a24_vec+b24_vec)/(a24_vec+c24_vec)
  names(bias_snow24)[pi] <- paste0("BIAS24_probs_snow",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_snow96_list","SYN_man_snow96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  
  mat96_snow <- matrix(NA, ncol = 51, nrow = length(MOD_man_snow96_list))
  for (i in 1:length(MOD_man_snow96_list)) {
    #  print(i)
    if(MOD_man_snow96_list[i]>100) {MOD_man_snow96_list[i] <- 100} 
    MOD_man_snow96_list_YES <- round((MOD_man_snow96_list[i]*51)/100)
    list_MODyes96 <- rep(1, MOD_man_snow96_list_YES)
    MOD_man_snow96_list_NO <- round(((100-MOD_man_snow96_list[i])*51)/100)
    list_MODno96 <- rep(0, MOD_man_snow96_list_NO)
    list_MODyesno96 <- append(list_MODyes96,list_MODno96)
    mat96_snow[i,] <- list_MODyesno96
  }
  mat96_snow_vect <- as.vector(t(mat96_snow))
  
  mat_SYN_snow96 <- matrix(NA, ncol = 51, nrow = length(SYN_man_snow96_list))
  for (i in 1:length(SYN_man_snow96_list)) {
    list_SYN96 <- rep(SYN_man_snow96_list[i], 51)
    mat_SYN_snow96[i,] <- list_SYN96
  }
  mat_SYN_snow96_vect <- as.vector(t(mat_SYN_snow96))
  
  
  matSYN_MOD96_vec <- data.frame("Syn" = mat_SYN_snow96_vect, "Mod" = mat96_snow_vect, 
                                 "a" = ifelse(mat_SYN_snow96_vect == 1 & mat96_snow_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_snow96_vect == 0 & mat96_snow_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_snow96_vect == 1 & mat96_snow_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_snow96_vect == 0 & mat96_snow_vect == 0, 1, 0))
  
  a96_vec <- sum(matSYN_MOD96_vec$a)
  b96_vec <- sum(matSYN_MOD96_vec$b)
  c96_vec <- sum(matSYN_MOD96_vec$c)
  d96_vec <- sum(matSYN_MOD96_vec$d)
  
  write.table(c(a96_vec,b96_vec,c96_vec,d96_vec), file=paste0(PATH_model_mannual,'indexes_snow96_',val,'.txt'), row.names=F, col.names=F) 
  
  bias_snow96[pi] <- (a96_vec+b96_vec)/(a96_vec+c96_vec)
  names(bias_snow96)[pi] <- paste0("BIAS96_probs_snow",val) 
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  #******************************************* FREEZING RAIN 
  
  ############################## READ MODEL ####################################
  
  model_mannual_freezrain0 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezrain_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  model_mannual_freezrain24 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezrain_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  model_mannual_freezrain96 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezrain_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  #  model_mannual_freezrain0 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezrain_(.*)_(0|12|24).gpt$")
  #  model_mannual_freezrain24 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezrain_(.*)_(24|36|48).gpt$")
  # model_mannual_freezrain96 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezrain_(.*)_(96|108|120).gpt$")
  
  MODEL_mannual_freezrain0 <- file.path(PATH_model_mannual, model_mannual_freezrain0)
  MODEL_mannual_freezrain24 <- file.path(PATH_model_mannual, model_mannual_freezrain24)
  MODEL_mannual_freezrain96 <- file.path(PATH_model_mannual, model_mannual_freezrain96)
  
  
  lstmod_freezrain_man0 <- lapply(MODEL_mannual_freezrain0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_freezrain_man0 <- lapply(lstmod_freezrain_man0, function(x){x[, 6]})
  
  MOD_man_freezrain0_list_pre <- NULL
  for (i in 1:length(lstmod_freezrain_man0)) {
    MOD_man_freezrain0_list_pre <- append(MOD_man_freezrain0_list_pre, lstmod_freezrain_man0[[i]])
  }
  MOD_man_freezrain0_list <- MOD_man_freezrain0_list_pre[(which(MOD_man_freezrain0_list_pre <= 100))] 
  
  lstmod_freezrain_man24 <- lapply(MODEL_mannual_freezrain24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_freezrain_man24 <- lapply(lstmod_freezrain_man24, function(x){x[, 6]})
  
  MOD_man_freezrain24_list_pre <- NULL
  for (i in 1:length(lstmod_freezrain_man24)) {
    MOD_man_freezrain24_list_pre <- append(MOD_man_freezrain24_list_pre, lstmod_freezrain_man24[[i]])
  }
  MOD_man_freezrain24_list <- MOD_man_freezrain24_list_pre[(which(MOD_man_freezrain24_list_pre <= 100))]
  
  lstmod_freezrain_man96 <- lapply(MODEL_mannual_freezrain96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_freezrain_man96 <- lapply(lstmod_freezrain_man96, function(x){x[, 6]})
  
  MOD_man_freezrain96_list_pre <- NULL
  for (i in 1:length(lstmod_freezrain_man96)) {
    MOD_man_freezrain96_list_pre <- append(MOD_man_freezrain96_list_pre, lstmod_freezrain_man96[[i]])
  }
  MOD_man_freezrain96_list <- MOD_man_freezrain96_list_pre[(which(MOD_man_freezrain96_list_pre <= 100))] 
  
  ############################## READ SYNOP ####################################
  
  synop_mannual_freezrain0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezrain_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  synop_mannual_freezrain24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezrain_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  synop_mannual_freezrain96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezrain_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  
  # synop_mannual_freezrain0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezrain_(.*)_(0|12|24).gpt$")
  # synop_mannual_freezrain24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezrain_(.*)_(24|36|48).gpt$")
  # synop_mannual_freezrain96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezrain_(.*)_(96|108|120).gpt$")  

  SYNOP_mannual_freezrain0 <- file.path(PATH_SYNOP_mannual, synop_mannual_freezrain0)
  SYNOP_mannual_freezrain24 <- file.path(PATH_SYNOP_mannual, synop_mannual_freezrain24)
  SYNOP_mannual_freezrain96 <- file.path(PATH_SYNOP_mannual, synop_mannual_freezrain96)
  
  
  lstsyn_freezrain_man0 <- lapply(SYNOP_mannual_freezrain0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_freezrain_man0 <- lapply(lstsyn_freezrain_man0, function(x){x[, 6]})
  
  SYN_man_freezrain0_list_pre <- NULL
  for (i in 1:length(lstsyn_freezrain_man0)) {
    SYN_man_freezrain0_list_pre <- append(SYN_man_freezrain0_list_pre, lstsyn_freezrain_man0[[i]])
  }
  SYN_man_freezrain0_list <- SYN_man_freezrain0_list_pre[(which(MOD_man_freezrain0_list_pre <= 100))] 
  
  
  lstsyn_freezrain_man24 <- lapply(SYNOP_mannual_freezrain24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_freezrain_man24 <- lapply(lstsyn_freezrain_man24, function(x){x[, 6]})
  
  SYN_man_freezrain24_list_pre <- NULL
  for (i in 1:length(lstsyn_freezrain_man24)) {
    SYN_man_freezrain24_list_pre <- append(SYN_man_freezrain24_list_pre, lstsyn_freezrain_man24[[i]])
  }
  SYN_man_freezrain24_list <- SYN_man_freezrain24_list_pre[(which(MOD_man_freezrain24_list_pre <= 100))] 
  
    
  lstsyn_freezrain_man96 <- lapply(SYNOP_mannual_freezrain96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_freezrain_man96 <- lapply(lstsyn_freezrain_man96, function(x){x[, 6]})
  
  SYN_man_freezrain96_list_pre <- NULL
  for (i in 1:length(lstsyn_freezrain_man96)) {
    SYN_man_freezrain96_list_pre <- append(SYN_man_freezrain96_list_pre, lstsyn_freezrain_man96[[i]])
  }
  SYN_man_freezrain96_list <- SYN_man_freezrain96_list_pre[(which(MOD_man_freezrain96_list_pre <= 100))] 
  
  num0 <- table(SYN_man_freezrain0_list)
  num0 = num0[names(num0)!=0]          # total observations with freezdrizzle
  total0 = length(SYN_man_freezrain0_list)  # total observations 
  
  num24 <- table(SYN_man_freezrain24_list)
  num24 = num24[names(num24)!=0]
  total24= length(SYN_man_freezrain24_list)
  
  num96 <- table(SYN_man_freezrain96_list)
  num96 = num96[names(num96)!=0]
  total96 = length(SYN_man_freezrain96_list)
  
  ################ VERIFICATION ROC #################################################################
  library(verification)
  library(ROCR)
  
  mat0_freezrain <- matrix(NA, ncol = 51, nrow = length(MOD_man_freezrain0_list))
  for (i in 1:length(MOD_man_freezrain0_list)) {
    #print(i)
    MOD_man_freezrain0_list_YES <- round((MOD_man_freezrain0_list[i]*51)/100)
    list_MODyes0 <- rep(1, MOD_man_freezrain0_list_YES)
    MOD_man_freezrain0_list_NO <- round(((100-MOD_man_freezrain0_list[i])*51)/100)
    list_MODno0 <- rep(0, MOD_man_freezrain0_list_NO)
    list_MODyesno0 <- append(list_MODyes0,list_MODno0)
    mat0_freezrain[i,] <- list_MODyesno0
  }
  mat0_freezrain_vect <- as.vector(t(mat0_freezrain))
  
  mat_SYN_freezrain0 <- matrix(NA, ncol = 51, nrow = length(SYN_man_freezrain0_list))
  for (i in 1:length(SYN_man_freezrain0_list)) {
    list_SYN0 <- rep(SYN_man_freezrain0_list[i], 51)
    mat_SYN_freezrain0[i,] <- list_SYN0
  }
  mat_SYN_freezrain0_vect <- as.vector(t(mat_SYN_freezrain0))
  
  matSYN_MOD0_vec <- data.frame("Syn" = mat_SYN_freezrain0_vect, "Mod" = mat0_freezrain_vect, 
                                "a" = ifelse(mat_SYN_freezrain0_vect == 1 & mat0_freezrain_vect == 1, 1, 0),
                                "b" = ifelse(mat_SYN_freezrain0_vect == 0 & mat0_freezrain_vect == 1, 1, 0),
                                "c" = ifelse(mat_SYN_freezrain0_vect == 1 & mat0_freezrain_vect == 0, 1, 0),
                                "d" = ifelse(mat_SYN_freezrain0_vect == 0 & mat0_freezrain_vect == 0, 1, 0))
  
  a0_vec <- sum(matSYN_MOD0_vec$a)
  b0_vec <- sum(matSYN_MOD0_vec$b)
  c0_vec <- sum(matSYN_MOD0_vec$c)
  d0_vec <- sum(matSYN_MOD0_vec$d)
  
  write.table(c(a0_vec,b0_vec,c0_vec,d0_vec), file=paste0(PATH_model_mannual,'indexes_freezrain0_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_freezrain0[pi] <-  (a0_vec+b0_vec)/(a0_vec+c0_vec)
  names(bias_freezrain0)[pi] <- paste0("BIAS0_probs_freezrain",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_freezrain24_list","SYN_man_freezrain24_list","MOD_man_freezrain96_list","SYN_man_freezrain96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  mat24_freezrain <- matrix(NA, ncol = 51, nrow = length(MOD_man_freezrain24_list))
  for (i in 1:length(MOD_man_freezrain24_list)) {
   # print(i)
    MOD_man_freezrain24_list_YES <- round((MOD_man_freezrain24_list[i]*51)/100)
    list_MODyes24 <- rep(1, MOD_man_freezrain24_list_YES)
    MOD_man_freezrain24_list_NO <- round(((100-MOD_man_freezrain24_list[i])*51)/100)
    list_MODno24 <- rep(0, MOD_man_freezrain24_list_NO)
    list_MODyesno24 <- append(list_MODyes24,list_MODno24)
    mat24_freezrain[i,] <- list_MODyesno24
  }
  mat24_freezrain_vect <- as.vector(t(mat24_freezrain))
  
  
  mat_SYN_freezrain24 <- matrix(NA, ncol = 51, nrow = length(SYN_man_freezrain24_list))
  for (i in 1:length(SYN_man_freezrain24_list)) {
    list_SYN24 <- rep(SYN_man_freezrain24_list[i], 51)
    mat_SYN_freezrain24[i,] <- list_SYN24
  }
  mat_SYN_freezrain24_vect <- as.vector(t(mat_SYN_freezrain24))
  
  matSYN_MOD24_vec <- data.frame("Syn" = mat_SYN_freezrain24_vect, "Mod" = mat24_freezrain_vect, 
                                 "a" = ifelse(mat_SYN_freezrain24_vect == 1 & mat24_freezrain_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_freezrain24_vect == 0 & mat24_freezrain_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_freezrain24_vect == 1 & mat24_freezrain_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_freezrain24_vect == 0 & mat24_freezrain_vect == 0, 1, 0))
  
  a24_vec <- sum(matSYN_MOD24_vec$a)
  b24_vec <- sum(matSYN_MOD24_vec$b)
  c24_vec <- sum(matSYN_MOD24_vec$c)
  d24_vec <- sum(matSYN_MOD24_vec$d)
  
  write.table(c(a24_vec,b24_vec,c24_vec,d24_vec), file=paste0(PATH_model_mannual,'indexes_freezrain24_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_freezrain24[pi] <-  (a24_vec+b24_vec)/(a24_vec+c24_vec)
  names(bias_freezrain24)[pi] <- paste0("BIAS24_probs_freezrain",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_freezrain96_list","SYN_man_freezrain96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  
  mat96_freezrain <- matrix(NA, ncol = 51, nrow = length(MOD_man_freezrain96_list))
  for (i in 1:length(MOD_man_freezrain96_list)) {
   # print(i)
    MOD_man_freezrain96_list_YES <- round((MOD_man_freezrain96_list[i]*51)/100)
    list_MODyes96 <- rep(1, MOD_man_freezrain96_list_YES)
    MOD_man_freezrain96_list_NO <- round(((100-MOD_man_freezrain96_list[i])*51)/100)
    list_MODno96 <- rep(0, MOD_man_freezrain96_list_NO)
    list_MODyesno96 <- append(list_MODyes96,list_MODno96)
    mat96_freezrain[i,] <- list_MODyesno96
  }
  mat96_freezrain_vect <- as.vector(t(mat96_freezrain))
  
  mat_SYN_freezrain96 <- matrix(NA, ncol = 51, nrow = length(SYN_man_freezrain96_list))
  for (i in 1:length(SYN_man_freezrain96_list)) {
    list_SYN96 <- rep(SYN_man_freezrain96_list[i], 51)
    mat_SYN_freezrain96[i,] <- list_SYN96
  }
  mat_SYN_freezrain96_vect <- as.vector(t(mat_SYN_freezrain96))
  
  
  matSYN_MOD96_vec <- data.frame("Syn" = mat_SYN_freezrain96_vect, "Mod" = mat96_freezrain_vect, 
                                 "a" = ifelse(mat_SYN_freezrain96_vect == 1 & mat96_freezrain_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_freezrain96_vect == 0 & mat96_freezrain_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_freezrain96_vect == 1 & mat96_freezrain_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_freezrain96_vect == 0 & mat96_freezrain_vect == 0, 1, 0))
  
  a96_vec <- sum(matSYN_MOD96_vec$a)
  b96_vec <- sum(matSYN_MOD96_vec$b)
  c96_vec <- sum(matSYN_MOD96_vec$c)
  d96_vec <- sum(matSYN_MOD96_vec$d)
  
  
  write.table(c(a96_vec,b96_vec,c96_vec,d96_vec), file=paste0(PATH_model_mannual,'indexes_freezrain96_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_freezrain96[pi] <- (a96_vec+b96_vec)/(a96_vec+c96_vec)
  names(bias_freezrain96)[pi] <- paste0("BIAS96_probs_freezrain",val) 
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  #******************************************* FREEZING DRIZZLE
  
  ############################## READ MODEL ####################################  
  

  model_mannual_freezdrizzle0 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezdrizzle_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  model_mannual_freezdrizzle24 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezdrizzle_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  model_mannual_freezdrizzle96 <- list.files(path=PATH_model_mannual,pattern="^Loc_freezdrizzle_(.*)_(96|99|102|105|108|111|114|117).gpt$")

  MODEL_mannual_freezdrizzle0 <- file.path(PATH_model_mannual, model_mannual_freezdrizzle0)
  MODEL_mannual_freezdrizzle24 <- file.path(PATH_model_mannual, model_mannual_freezdrizzle24)
  MODEL_mannual_freezdrizzle96 <- file.path(PATH_model_mannual, model_mannual_freezdrizzle96)

  
  lstmod_freezdrizzle_man0 <- lapply(MODEL_mannual_freezdrizzle0, read.table,  header=FALSE, comment.char="#")
  lstmod_freezdrizzle_man0 <- lapply(lstmod_freezdrizzle_man0, function(x){x[, 6]})
  
  MOD_man_freezdrizzle0_list_pre <- NULL
  for (i in 1:length(lstmod_freezdrizzle_man0)) {
    MOD_man_freezdrizzle0_list_pre <- append(MOD_man_freezdrizzle0_list_pre, lstmod_freezdrizzle_man0[[i]])
  }
  MOD_man_freezdrizzle0_list <- MOD_man_freezdrizzle0_list_pre[(which(MOD_man_freezdrizzle0_list_pre <= 100))] 
  
  lstmod_freezdrizzle_man24 <- lapply(MODEL_mannual_freezdrizzle24, read.table,  header=FALSE, comment.char="#")
  lstmod_freezdrizzle_man24 <- lapply(lstmod_freezdrizzle_man24, function(x){x[, 6]})
  
  MOD_man_freezdrizzle24_list_pre <- NULL
  for (i in 1:length(lstmod_freezdrizzle_man24)) {
    MOD_man_freezdrizzle24_list_pre <- append(MOD_man_freezdrizzle24_list_pre, lstmod_freezdrizzle_man24[[i]])
  }
  MOD_man_freezdrizzle24_list <- MOD_man_freezdrizzle24_list_pre[(which(MOD_man_freezdrizzle24_list_pre <= 100))] 
  
  
  lstmod_freezdrizzle_man96 <- lapply(MODEL_mannual_freezdrizzle96, read.table,  header=FALSE, comment.char="#")
  lstmod_freezdrizzle_man96 <- lapply(lstmod_freezdrizzle_man96, function(x){x[, 6]})
  
  MOD_man_freezdrizzle96_list_pre <- NULL
  for (i in 1:length(lstmod_freezdrizzle_man96)) {
    MOD_man_freezdrizzle96_list_pre <- append(MOD_man_freezdrizzle96_list_pre, lstmod_freezdrizzle_man96[[i]])
  }
  MOD_man_freezdrizzle96_list <- MOD_man_freezdrizzle96_list_pre[(which(MOD_man_freezdrizzle96_list_pre <= 100))] 
  

  ############################## READ SYNOP ####################################
  

  synop_mannual_freezdrizzle0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezdrizzle_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  synop_mannual_freezdrizzle24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezdrizzle_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  synop_mannual_freezdrizzle96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_freezdrizzle_(.*)_(96|99|102|105|108|111|114|117).gpt$")

  SYNOP_mannual_freezdrizzle0 <- file.path(PATH_SYNOP_mannual, synop_mannual_freezdrizzle0)
  SYNOP_mannual_freezdrizzle24 <- file.path(PATH_SYNOP_mannual, synop_mannual_freezdrizzle24)
  SYNOP_mannual_freezdrizzle96 <- file.path(PATH_SYNOP_mannual, synop_mannual_freezdrizzle96)
  
  lstsyn_freezdrizzle_man0 <- lapply(SYNOP_mannual_freezdrizzle0, read.table,  header=FALSE, comment.char="#")
  lstsyn_freezdrizzle_man0 <- lapply(lstsyn_freezdrizzle_man0, function(x){x[, 6]})
  
  SYN_man_freezdrizzle0_list_pre <- NULL
  for (i in 1:length(lstsyn_freezdrizzle_man0)) {
    SYN_man_freezdrizzle0_list_pre <- append(SYN_man_freezdrizzle0_list_pre, lstsyn_freezdrizzle_man0[[i]])
  }
  SYN_man_freezdrizzle0_list <- SYN_man_freezdrizzle0_list_pre[(which(MOD_man_freezdrizzle0_list_pre <= 100))] 
  
  lstsyn_freezdrizzle_man24 <- lapply(SYNOP_mannual_freezdrizzle24, read.table,  header=FALSE, comment.char="#")
  lstsyn_freezdrizzle_man24 <- lapply(lstsyn_freezdrizzle_man24, function(x){x[, 6]})
  
  SYN_man_freezdrizzle24_list_pre <- NULL
  for (i in 1:length(lstsyn_freezdrizzle_man24)) {
    SYN_man_freezdrizzle24_list_pre <- append(SYN_man_freezdrizzle24_list_pre, lstsyn_freezdrizzle_man24[[i]])
  }
  SYN_man_freezdrizzle24_list <- SYN_man_freezdrizzle24_list_pre[(which(MOD_man_freezdrizzle24_list_pre <= 100))] 
  
  
  lstsyn_freezdrizzle_man96 <- lapply(SYNOP_mannual_freezdrizzle96, read.table,  header=FALSE, comment.char="#")
  lstsyn_freezdrizzle_man96 <- lapply(lstsyn_freezdrizzle_man96, function(x){x[, 6]})
  
  SYN_man_freezdrizzle96_list_pre <- NULL
  for (i in 1:length(lstsyn_freezdrizzle_man96)) {
    SYN_man_freezdrizzle96_list_pre <- append(SYN_man_freezdrizzle96_list_pre, lstsyn_freezdrizzle_man96[[i]])
  }
  SYN_man_freezdrizzle96_list <- SYN_man_freezdrizzle96_list_pre[(which(MOD_man_freezdrizzle96_list_pre <= 100))] 
 
  ################ VERIFICATION ROC #################################################################
  library(verification)
  library(ROCR)
  
  mat0_freezdrizzle <- matrix(NA, ncol = 51, nrow = length(MOD_man_freezdrizzle0_list))
  for (i in 1:length(MOD_man_freezdrizzle0_list)) {
    #print(i)
    MOD_man_freezdrizzle0_list_YES <- round((MOD_man_freezdrizzle0_list[i]*51)/100)
    list_MODyes0 <- rep(1, MOD_man_freezdrizzle0_list_YES)
    MOD_man_freezdrizzle0_list_NO <- round(((100-MOD_man_freezdrizzle0_list[i])*51)/100)
    list_MODno0 <- rep(0, MOD_man_freezdrizzle0_list_NO)
    list_MODyesno0 <- append(list_MODyes0,list_MODno0)
    mat0_freezdrizzle[i,] <- list_MODyesno0
  }
  mat0_freezdrizzle_vect <- as.vector(t(mat0_freezdrizzle))
  
  mat_SYN_freezdrizzle0 <- matrix(NA, ncol = 51, nrow = length(SYN_man_freezdrizzle0_list))
  for (i in 1:length(SYN_man_freezdrizzle0_list)) {
    list_SYN0 <- rep(SYN_man_freezdrizzle0_list[i], 51)
    mat_SYN_freezdrizzle0[i,] <- list_SYN0
  }
  mat_SYN_freezdrizzle0_vect <- as.vector(t(mat_SYN_freezdrizzle0))
  
  matSYN_MOD0_vec <- data.frame("Syn" = mat_SYN_freezdrizzle0_vect, "Mod" = mat0_freezdrizzle_vect, 
                                "a" = ifelse(mat_SYN_freezdrizzle0_vect == 1 & mat0_freezdrizzle_vect == 1, 1, 0),
                                "b" = ifelse(mat_SYN_freezdrizzle0_vect == 0 & mat0_freezdrizzle_vect == 1, 1, 0),
                                "c" = ifelse(mat_SYN_freezdrizzle0_vect == 1 & mat0_freezdrizzle_vect == 0, 1, 0),
                                "d" = ifelse(mat_SYN_freezdrizzle0_vect == 0 & mat0_freezdrizzle_vect == 0, 1, 0))
  
  a0_vec <- sum(matSYN_MOD0_vec$a)
  b0_vec <- sum(matSYN_MOD0_vec$b)
  c0_vec <- sum(matSYN_MOD0_vec$c)
  d0_vec <- sum(matSYN_MOD0_vec$d)
  
  write.table(c(a0_vec,b0_vec,c0_vec,d0_vec), file=paste0(PATH_model_mannual,'indexes_freezdrizzle0_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_freezdrizzle0[pi] <-  (a0_vec+b0_vec)/(a0_vec+c0_vec)
  names(bias_freezdrizzle0)[pi] <- paste0("BIAS0_probs_freezdrizzle",val)
  
  #  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_freezdrizzle24_list","SYN_man_freezdrizzle24_list","MOD_man_freezdrizzle96_list","SYN_man_freezdrizzle96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  mat24_freezdrizzle <- matrix(NA, ncol = 51, nrow = length(MOD_man_freezdrizzle24_list))
  for (i in 1:length(MOD_man_freezdrizzle24_list)) {
    # print(i)
    MOD_man_freezdrizzle24_list_YES <- round((MOD_man_freezdrizzle24_list[i]*51)/100)
    list_MODyes24 <- rep(1, MOD_man_freezdrizzle24_list_YES)
    MOD_man_freezdrizzle24_list_NO <- round(((100-MOD_man_freezdrizzle24_list[i])*51)/100)
    list_MODno24 <- rep(0, MOD_man_freezdrizzle24_list_NO)
    list_MODyesno24 <- append(list_MODyes24,list_MODno24)
    mat24_freezdrizzle[i,] <- list_MODyesno24
  }
  mat24_freezdrizzle_vect <- as.vector(t(mat24_freezdrizzle))
  
  
  mat_SYN_freezdrizzle24 <- matrix(NA, ncol = 51, nrow = length(SYN_man_freezdrizzle24_list))
  for (i in 1:length(SYN_man_freezdrizzle24_list)) {
    list_SYN24 <- rep(SYN_man_freezdrizzle24_list[i], 51)
    mat_SYN_freezdrizzle24[i,] <- list_SYN24
  }
  mat_SYN_freezdrizzle24_vect <- as.vector(t(mat_SYN_freezdrizzle24))
  
  matSYN_MOD24_vec <- data.frame("Syn" = mat_SYN_freezdrizzle24_vect, "Mod" = mat24_freezdrizzle_vect, 
                                 "a" = ifelse(mat_SYN_freezdrizzle24_vect == 1 & mat24_freezdrizzle_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_freezdrizzle24_vect == 0 & mat24_freezdrizzle_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_freezdrizzle24_vect == 1 & mat24_freezdrizzle_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_freezdrizzle24_vect == 0 & mat24_freezdrizzle_vect == 0, 1, 0))
  
  a24_vec <- sum(matSYN_MOD24_vec$a)
  b24_vec <- sum(matSYN_MOD24_vec$b)
  c24_vec <- sum(matSYN_MOD24_vec$c)
  d24_vec <- sum(matSYN_MOD24_vec$d)
  
  write.table(c(a24_vec,b24_vec,c24_vec,d24_vec), file=paste0(PATH_model_mannual,'indexes_freezdrizzle24_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_freezdrizzle24[pi] <-  (a24_vec+b24_vec)/(a24_vec+c24_vec)
  names(bias_freezdrizzle24)[pi] <- paste0("BIAS24_probs_freezdrizzle",val)
  
  #  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_freezdrizzle96_list","SYN_man_freezdrizzle96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  
  mat96_freezdrizzle <- matrix(NA, ncol = 51, nrow = length(MOD_man_freezdrizzle96_list))
  for (i in 1:length(MOD_man_freezdrizzle96_list)) {
    # print(i)
    MOD_man_freezdrizzle96_list_YES <- round((MOD_man_freezdrizzle96_list[i]*51)/100)
    list_MODyes96 <- rep(1, MOD_man_freezdrizzle96_list_YES)
    MOD_man_freezdrizzle96_list_NO <- round(((100-MOD_man_freezdrizzle96_list[i])*51)/100)
    list_MODno96 <- rep(0, MOD_man_freezdrizzle96_list_NO)
    list_MODyesno96 <- append(list_MODyes96,list_MODno96)
    mat96_freezdrizzle[i,] <- list_MODyesno96
  }
  mat96_freezdrizzle_vect <- as.vector(t(mat96_freezdrizzle))
  
  mat_SYN_freezdrizzle96 <- matrix(NA, ncol = 51, nrow = length(SYN_man_freezdrizzle96_list))
  for (i in 1:length(SYN_man_freezdrizzle96_list)) {
    list_SYN96 <- rep(SYN_man_freezdrizzle96_list[i], 51)
    mat_SYN_freezdrizzle96[i,] <- list_SYN96
  }
  mat_SYN_freezdrizzle96_vect <- as.vector(t(mat_SYN_freezdrizzle96))
  
  
  matSYN_MOD96_vec <- data.frame("Syn" = mat_SYN_freezdrizzle96_vect, "Mod" = mat96_freezdrizzle_vect, 
                                 "a" = ifelse(mat_SYN_freezdrizzle96_vect == 1 & mat96_freezdrizzle_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_freezdrizzle96_vect == 0 & mat96_freezdrizzle_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_freezdrizzle96_vect == 1 & mat96_freezdrizzle_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_freezdrizzle96_vect == 0 & mat96_freezdrizzle_vect == 0, 1, 0))
  
  a96_vec <- sum(matSYN_MOD96_vec$a)
  b96_vec <- sum(matSYN_MOD96_vec$b)
  c96_vec <- sum(matSYN_MOD96_vec$c)
  d96_vec <- sum(matSYN_MOD96_vec$d)
  
  num0 <- table(SYN_man_freezdrizzle0_list)
  num0 = num0[names(num0)!=0]          # total observations with freezdrizzle
  total0 = length(SYN_man_freezdrizzle0_list)  # total observations 
  
  num24 <- table(SYN_man_freezdrizzle24_list)
  num24 = num24[names(num24)!=0]
  total24= length(SYN_man_freezdrizzle24_list)
  
  num96 <- table(SYN_man_freezdrizzle96_list)
  num96 = num96[names(num96)!=0]
  total96 = length(SYN_man_freezdrizzle96_list)
  
  
  write.table(c(a96_vec,b96_vec,c96_vec,d96_vec), file=paste0(PATH_model_mannual,'indexes_freezdrizzle96_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_freezdrizzle96[pi] <- (a96_vec+b96_vec)/(a96_vec+c96_vec)
  names(bias_freezdrizzle96)[pi] <- paste0("BIAS96_probs_freezdrizzle",val) 
  
  # rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
   
  
  #******************************************* SLEET 
  
  ############################## READ MODEL ####################################
  
  model_mannual_sleet0 <- list.files(path=PATH_model_mannual,pattern="^Loc_sleet_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  model_mannual_sleet24 <- list.files(path=PATH_model_mannual,pattern="^Loc_sleet_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  model_mannual_sleet96 <- list.files(path=PATH_model_mannual,pattern="^Loc_sleet_(.*)_(96|99|102|105|108|111|114|117).gpt$")
 
  #  model_mannual_sleet0 <- list.files(path=PATH_model_mannual,pattern="^Loc_sleet_(.*)_(0|12|24).gpt$")
  # model_mannual_sleet24 <- list.files(path=PATH_model_mannual,pattern="^Loc_sleet_(.*)_(24|36|48).gpt$")
  # model_mannual_sleet96 <- list.files(path=PATH_model_mannual,pattern="^Loc_sleet_(.*)_(96|108|120).gpt$")
  
  MODEL_mannual_sleet0 <- file.path(PATH_model_mannual, model_mannual_sleet0)
  MODEL_mannual_sleet24 <- file.path(PATH_model_mannual, model_mannual_sleet24)
  MODEL_mannual_sleet96 <- file.path(PATH_model_mannual, model_mannual_sleet96)
  
  
  lstmod_sleet_man0 <- lapply(MODEL_mannual_sleet0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_sleet_man0 <- lapply(lstmod_sleet_man0, function(x){x[, 6]})
  
  MOD_man_sleet0_list_pre <- NULL
  for (i in 1:length(lstmod_sleet_man0)) {
    MOD_man_sleet0_list_pre <- append(MOD_man_sleet0_list_pre, lstmod_sleet_man0[[i]])
  }
  MOD_man_sleet0_list <- MOD_man_sleet0_list_pre[(which(MOD_man_sleet0_list_pre <= 100))] 
  
  
  lstmod_sleet_man24 <- lapply(MODEL_mannual_sleet24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_sleet_man24 <- lapply(lstmod_sleet_man24, function(x){x[, 6]})
  
  MOD_man_sleet24_list_pre <- NULL
  for (i in 1:length(lstmod_sleet_man24)) {
    MOD_man_sleet24_list_pre <- append(MOD_man_sleet24_list_pre, lstmod_sleet_man24[[i]])
  }
  MOD_man_sleet24_list <- MOD_man_sleet24_list_pre[(which(MOD_man_sleet24_list_pre <= 100))] 
  
    
  lstmod_sleet_man96 <- lapply(MODEL_mannual_sleet96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_sleet_man96 <- lapply(lstmod_sleet_man96, function(x){x[, 6]})
  
  MOD_man_sleet96_list_pre <- NULL
  for (i in 1:length(lstmod_sleet_man96)) {
    MOD_man_sleet96_list_pre <- append(MOD_man_sleet96_list_pre, lstmod_sleet_man96[[i]])
  }
  MOD_man_sleet96_list <- MOD_man_sleet96_list_pre[(which(MOD_man_sleet96_list_pre <= 100))] 
  
  ############################## READ SYNOP ####################################
  
  synop_mannual_sleet0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_sleet_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  synop_mannual_sleet24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_sleet_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  synop_mannual_sleet96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_sleet_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  
  # synop_mannual_sleet0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_sleet_(.*)_(0|12|24).gpt$")
  #  synop_mannual_sleet24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_sleet_(.*)_(24|36|48).gpt$")
  #  synop_mannual_sleet96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_sleet_(.*)_(96|108|120).gpt$")
  
  SYNOP_mannual_sleet0 <- file.path(PATH_SYNOP_mannual, synop_mannual_sleet0)
  SYNOP_mannual_sleet24 <- file.path(PATH_SYNOP_mannual, synop_mannual_sleet24)
  SYNOP_mannual_sleet96 <- file.path(PATH_SYNOP_mannual, synop_mannual_sleet96)
  
  lstsyn_sleet_man0 <- lapply(SYNOP_mannual_sleet0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_sleet_man0 <- lapply(lstsyn_sleet_man0, function(x){x[, 6]})
  
  SYN_man_sleet0_list_pre <- NULL
  for (i in 1:length(lstsyn_sleet_man0)) {
    SYN_man_sleet0_list_pre <- append(SYN_man_sleet0_list_pre, lstsyn_sleet_man0[[i]])
  }
  SYN_man_sleet0_list <- SYN_man_sleet0_list_pre[(which(MOD_man_sleet0_list_pre <= 100))] 
  
  
  lstsyn_sleet_man24 <- lapply(SYNOP_mannual_sleet24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_sleet_man24 <- lapply(lstsyn_sleet_man24, function(x){x[, 6]})
  
  SYN_man_sleet24_list_pre <- NULL
  for (i in 1:length(lstsyn_sleet_man24)) {
    SYN_man_sleet24_list_pre <- append(SYN_man_sleet24_list_pre, lstsyn_sleet_man24[[i]])
  }
  SYN_man_sleet24_list <- SYN_man_sleet24_list_pre[(which(MOD_man_sleet24_list_pre <= 100))] 
  
  lstsyn_sleet_man96 <- lapply(SYNOP_mannual_sleet96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_sleet_man96 <- lapply(lstsyn_sleet_man96, function(x){x[, 6]})
  
  SYN_man_sleet96_list_pre <- NULL
  for (i in 1:length(lstsyn_sleet_man96)) {
    SYN_man_sleet96_list_pre <- append(SYN_man_sleet96_list_pre, lstsyn_sleet_man96[[i]])
  }
  SYN_man_sleet96_list <- SYN_man_sleet96_list_pre[(which(MOD_man_sleet96_list_pre <= 100))] 
  
  num0 <- table(SYN_man_sleet0_list)
  num0 = num0[names(num0)!=0]          # total observations with freezdrizzle
  total0 = length(SYN_man_sleet0_list)  # total observations 
  
  num24 <- table(SYN_man_sleet24_list)
  num24 = num24[names(num24)!=0]
  total24= length(SYN_man_sleet24_list)
  
  num96 <- table(SYN_man_sleet96_list)
  num96 = num96[names(num96)!=0]
  total96 = length(SYN_man_sleet96_list)
  
  ################ VERIFICATION ROC #################################################################
  library(verification)
  library(ROCR)
  
  mat0_sleet <- matrix(NA, ncol = 51, nrow = length(MOD_man_sleet0_list))
  for (i in 1:length(MOD_man_sleet0_list)) {
   # print(i)
    MOD_man_sleet0_list_YES <- round((MOD_man_sleet0_list[i]*51)/100)
    list_MODyes0 <- rep(1, MOD_man_sleet0_list_YES)
    MOD_man_sleet0_list_NO <- round(((100-MOD_man_sleet0_list[i])*51)/100)
    list_MODno0 <- rep(0, MOD_man_sleet0_list_NO)
    list_MODyesno0 <- append(list_MODyes0,list_MODno0)
    mat0_sleet[i,] <- list_MODyesno0
  }
  mat0_sleet_vect <- as.vector(t(mat0_sleet))
  
  mat_SYN_sleet0 <- matrix(NA, ncol = 51, nrow = length(SYN_man_sleet0_list))
  for (i in 1:length(SYN_man_sleet0_list)) {
    list_SYN0 <- rep(SYN_man_sleet0_list[i], 51)
    mat_SYN_sleet0[i,] <- list_SYN0
  }
  mat_SYN_sleet0_vect <- as.vector(t(mat_SYN_sleet0))
  
  matSYN_MOD0_vec <- data.frame("Syn" = mat_SYN_sleet0_vect, "Mod" = mat0_sleet_vect, 
                                "a" = ifelse(mat_SYN_sleet0_vect == 1 & mat0_sleet_vect == 1, 1, 0),
                                "b" = ifelse(mat_SYN_sleet0_vect == 0 & mat0_sleet_vect == 1, 1, 0),
                                "c" = ifelse(mat_SYN_sleet0_vect == 1 & mat0_sleet_vect == 0, 1, 0),
                                "d" = ifelse(mat_SYN_sleet0_vect == 0 & mat0_sleet_vect == 0, 1, 0))
  
  a0_vec <- sum(matSYN_MOD0_vec$a)
  b0_vec <- sum(matSYN_MOD0_vec$b)
  c0_vec <- sum(matSYN_MOD0_vec$c)
  d0_vec <- sum(matSYN_MOD0_vec$d)
  
  write.table(c(a0_vec,b0_vec,c0_vec,d0_vec), file=paste0(PATH_model_mannual,'indexes_sleet0_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_sleet0[pi] <-  (a0_vec+b0_vec)/(a0_vec+c0_vec)
  names(bias_sleet0)[pi] <- paste0("BIAS0_probs_sleet",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_sleet24_list","SYN_man_sleet24_list","MOD_man_sleet96_list","SYN_man_sleet96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  mat24_sleet <- matrix(NA, ncol = 51, nrow = length(MOD_man_sleet24_list))
  for (i in 1:length(MOD_man_sleet24_list)) {
   # print(i)
    MOD_man_sleet24_list_YES <- round((MOD_man_sleet24_list[i]*51)/100)
    list_MODyes24 <- rep(1, MOD_man_sleet24_list_YES)
    MOD_man_sleet24_list_NO <- round(((100-MOD_man_sleet24_list[i])*51)/100)
    list_MODno24 <- rep(0, MOD_man_sleet24_list_NO)
    list_MODyesno24 <- append(list_MODyes24,list_MODno24)
    mat24_sleet[i,] <- list_MODyesno24
  }
  mat24_sleet_vect <- as.vector(t(mat24_sleet))
  
  
  mat_SYN_sleet24 <- matrix(NA, ncol = 51, nrow = length(SYN_man_sleet24_list))
  for (i in 1:length(SYN_man_sleet24_list)) {
    list_SYN24 <- rep(SYN_man_sleet24_list[i], 51)
    mat_SYN_sleet24[i,] <- list_SYN24
  }
  mat_SYN_sleet24_vect <- as.vector(t(mat_SYN_sleet24))
  
  matSYN_MOD24_vec <- data.frame("Syn" = mat_SYN_sleet24_vect, "Mod" = mat24_sleet_vect, 
                                 "a" = ifelse(mat_SYN_sleet24_vect == 1 & mat24_sleet_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_sleet24_vect == 0 & mat24_sleet_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_sleet24_vect == 1 & mat24_sleet_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_sleet24_vect == 0 & mat24_sleet_vect == 0, 1, 0))
  
  a24_vec <- sum(matSYN_MOD24_vec$a)
  b24_vec <- sum(matSYN_MOD24_vec$b)
  c24_vec <- sum(matSYN_MOD24_vec$c)
  d24_vec <- sum(matSYN_MOD24_vec$d)
  
  write.table(c(a24_vec,b24_vec,c24_vec,d24_vec), file=paste0(PATH_model_mannual,'indexes_sleet24_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_sleet24[pi] <-  (a24_vec+b24_vec)/(a24_vec+c24_vec)
  names(bias_sleet24)[pi] <- paste0("BIAS24_probs_sleet",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_sleet96_list","SYN_man_sleet96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  
  mat96_sleet <- matrix(NA, ncol = 51, nrow = length(MOD_man_sleet96_list))
  for (i in 1:length(MOD_man_sleet96_list)) {
   # print(i)
    MOD_man_sleet96_list_YES <- round((MOD_man_sleet96_list[i]*51)/100)
    list_MODyes96 <- rep(1, MOD_man_sleet96_list_YES)
    MOD_man_sleet96_list_NO <- round(((100-MOD_man_sleet96_list[i])*51)/100)
    list_MODno96 <- rep(0, MOD_man_sleet96_list_NO)
    list_MODyesno96 <- append(list_MODyes96,list_MODno96)
    mat96_sleet[i,] <- list_MODyesno96
  }
  mat96_sleet_vect <- as.vector(t(mat96_sleet))
  
  mat_SYN_sleet96 <- matrix(NA, ncol = 51, nrow = length(SYN_man_sleet96_list))
  for (i in 1:length(SYN_man_sleet96_list)) {
    list_SYN96 <- rep(SYN_man_sleet96_list[i], 51)
    mat_SYN_sleet96[i,] <- list_SYN96
  }
  mat_SYN_sleet96_vect <- as.vector(t(mat_SYN_sleet96))
  
  
  matSYN_MOD96_vec <- data.frame("Syn" = mat_SYN_sleet96_vect, "Mod" = mat96_sleet_vect, 
                                 "a" = ifelse(mat_SYN_sleet96_vect == 1 & mat96_sleet_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_sleet96_vect == 0 & mat96_sleet_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_sleet96_vect == 1 & mat96_sleet_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_sleet96_vect == 0 & mat96_sleet_vect == 0, 1, 0))
  
  a96_vec <- sum(matSYN_MOD96_vec$a)
  b96_vec <- sum(matSYN_MOD96_vec$b)
  c96_vec <- sum(matSYN_MOD96_vec$c)
  d96_vec <- sum(matSYN_MOD96_vec$d)
  
  write.table(c(a96_vec,b96_vec,c96_vec,d96_vec), file=paste0(PATH_model_mannual,'indexes_sleet96_',val,'.txt'), row.names=F, col.names=F) 
  
  
  bias_sleet96[pi] <- (a96_vec+b96_vec)/(a96_vec+c96_vec)
  names(bias_sleet96)[pi] <- paste0("BIAS96_probs_sleet",val) 
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  #******************************************* ICEPELLETS
  
  ############################## READ MODEL ####################################
  
  model_mannual_icepellets0 <- list.files(path=PATH_model_mannual,pattern="^Loc_icepellets_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  model_mannual_icepellets24 <- list.files(path=PATH_model_mannual,pattern="^Loc_icepellets_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  model_mannual_icepellets96 <- list.files(path=PATH_model_mannual,pattern="^Loc_icepellets_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  
  #  model_mannual_icepellets0 <- list.files(path=PATH_model_mannual,pattern="^Loc_icepellets_(.*)_(0|12|24).gpt$")
  #  model_mannual_icepellets24 <- list.files(path=PATH_model_mannual,pattern="^Loc_icepellets_(.*)_(24|36|48).gpt$")
  # model_mannual_icepellets96 <- list.files(path=PATH_model_mannual,pattern="^Loc_icepellets_(.*)_(96|108|120).gpt$")

  MODEL_mannual_icepellets0 <- file.path(PATH_model_mannual, model_mannual_icepellets0)
  MODEL_mannual_icepellets24 <- file.path(PATH_model_mannual, model_mannual_icepellets24)
  MODEL_mannual_icepellets96 <- file.path(PATH_model_mannual, model_mannual_icepellets96)
  
  lstmod_icepellets_man0 <- lapply(MODEL_mannual_icepellets0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_icepellets_man0 <- lapply(lstmod_icepellets_man0, function(x){x[, 6]})
  
  MOD_man_icepellets0_list_pre <- NULL
  for (i in 1:length(lstmod_icepellets_man0)) {
    MOD_man_icepellets0_list_pre <- append(MOD_man_icepellets0_list_pre, lstmod_icepellets_man0[[i]])
  }
  MOD_man_icepellets0_list <- MOD_man_icepellets0_list_pre[(which(MOD_man_icepellets0_list_pre <= 100))] 
  
  lstmod_icepellets_man24 <- lapply(MODEL_mannual_icepellets24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_icepellets_man24 <- lapply(lstmod_icepellets_man24, function(x){x[, 6]})
  
  MOD_man_icepellets24_list_pre <- NULL
  for (i in 1:length(lstmod_icepellets_man24)) {
    MOD_man_icepellets24_list_pre <- append(MOD_man_icepellets24_list_pre, lstmod_icepellets_man24[[i]])
  }
  MOD_man_icepellets24_list <- MOD_man_icepellets24_list_pre[(which(MOD_man_icepellets24_list_pre <= 100))] 
  
  lstmod_icepellets_man96 <- lapply(MODEL_mannual_icepellets96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstmod_icepellets_man96 <- lapply(lstmod_icepellets_man96, function(x){x[, 6]})
  
  MOD_man_icepellets96_list_pre <- NULL
  for (i in 1:length(lstmod_icepellets_man96)) {
    MOD_man_icepellets96_list_pre <- append(MOD_man_icepellets96_list_pre, lstmod_icepellets_man96[[i]])
  }
  MOD_man_icepellets96_list <- MOD_man_icepellets96_list_pre[(which(MOD_man_icepellets96_list_pre <= 100))] 
  
  ############################## READ SYNOP ####################################
  
  synop_mannual_icepellets0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_icepellets_(.*)_(0|3|6|9|12|15|18|21).gpt$")
  synop_mannual_icepellets24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_icepellets_(.*)_(24|27|30|33|36|39|42|45).gpt$")
  synop_mannual_icepellets96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_icepellets_(.*)_(96|99|102|105|108|111|114|117).gpt$")
  
  #  synop_mannual_icepellets0 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_icepellets_(.*)_(0|12|24).gpt$")
  #  synop_mannual_icepellets24 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_icepellets_(.*)_(24|36|48).gpt$")
  #  synop_mannual_icepellets96 <- list.files(path=PATH_SYNOP_mannual,pattern="^SYNOP_icepellets_(.*)_(96|108|120).gpt$")
  
  SYNOP_mannual_icepellets0 <- file.path(PATH_SYNOP_mannual, synop_mannual_icepellets0)
  SYNOP_mannual_icepellets24 <- file.path(PATH_SYNOP_mannual, synop_mannual_icepellets24)
  SYNOP_mannual_icepellets96 <- file.path(PATH_SYNOP_mannual, synop_mannual_icepellets96)
  
  lstsyn_icepellets_man0 <- lapply(SYNOP_mannual_icepellets0, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_icepellets_man0 <- lapply(lstsyn_icepellets_man0, function(x){x[, 6]})
  
  SYN_man_icepellets0_list_pre <- NULL
  for (i in 1:length(lstsyn_icepellets_man0)) {
    SYN_man_icepellets0_list_pre <- append(SYN_man_icepellets0_list_pre, lstsyn_icepellets_man0[[i]])
  }
  SYN_man_icepellets0_list <- SYN_man_icepellets0_list_pre[(which(MOD_man_icepellets0_list_pre <= 100))] 
  
  lstsyn_icepellets_man24 <- lapply(SYNOP_mannual_icepellets24, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_icepellets_man24 <- lapply(lstsyn_icepellets_man24, function(x){x[, 6]})
  
  SYN_man_icepellets24_list_pre <- NULL
  for (i in 1:length(lstsyn_icepellets_man24)) {
    SYN_man_icepellets24_list_pre <- append(SYN_man_icepellets24_list_pre, lstsyn_icepellets_man24[[i]])
  }
  SYN_man_icepellets24_list <- SYN_man_icepellets24_list_pre[(which(MOD_man_icepellets24_list_pre <= 100))] 
  
  lstsyn_icepellets_man96 <- lapply(SYNOP_mannual_icepellets96, function(x) {
    tryCatch(read.table(x), error=function(e) NULL)
  })
  lstsyn_icepellets_man96 <- lapply(lstsyn_icepellets_man96, function(x){x[, 6]})
  
  SYN_man_icepellets96_list_pre <- NULL
  for (i in 1:length(lstsyn_icepellets_man96)) {
    SYN_man_icepellets96_list_pre <- append(SYN_man_icepellets96_list_pre, lstsyn_icepellets_man96[[i]])
  }
  SYN_man_icepellets96_list <- SYN_man_icepellets96_list_pre[(which(MOD_man_icepellets96_list_pre <= 100))] 
  
  num0 <- table(SYN_man_icepellets0_list)
  num0 = num0[names(num0)!=0]          # total observations with freezdrizzle
  total0 = length(SYN_man_icepellets0_list)  # total observations 
  
  num24 <- table(SYN_man_icepellets24_list)
  num24 = num24[names(num24)!=0]
  total24= length(SYN_man_icepellets24_list)
  
  num96 <- table(SYN_man_icepellets96_list)
  num96 = num96[names(num96)!=0]
  total96 = length(SYN_man_icepellets96_list)
  
  ################ VERIFICATION ROC #################################################################
  library(verification)
  library(ROCR)
  
  mat0_icepellets <- matrix(NA, ncol = 51, nrow = length(MOD_man_icepellets0_list))
  for (i in 1:length(MOD_man_icepellets0_list)) {
   # print(i)
    MOD_man_icepellets0_list_YES <- round((MOD_man_icepellets0_list[i]*51)/100)
    list_MODyes0 <- rep(1, MOD_man_icepellets0_list_YES)
    MOD_man_icepellets0_list_NO <- round(((100-MOD_man_icepellets0_list[i])*51)/100)
    list_MODno0 <- rep(0, MOD_man_icepellets0_list_NO)
    list_MODyesno0 <- append(list_MODyes0,list_MODno0)
    mat0_icepellets[i,] <- list_MODyesno0
  }
  mat0_icepellets_vect <- as.vector(t(mat0_icepellets))
  
  mat_SYN_icepellets0 <- matrix(NA, ncol = 51, nrow = length(SYN_man_icepellets0_list))
  for (i in 1:length(SYN_man_icepellets0_list)) {
    list_SYN0 <- rep(SYN_man_icepellets0_list[i], 51)
    mat_SYN_icepellets0[i,] <- list_SYN0
  }
  mat_SYN_icepellets0_vect <- as.vector(t(mat_SYN_icepellets0))
  
  matSYN_MOD0_vec <- data.frame("Syn" = mat_SYN_icepellets0_vect, "Mod" = mat0_icepellets_vect, 
                                "a" = ifelse(mat_SYN_icepellets0_vect == 1 & mat0_icepellets_vect == 1, 1, 0),
                                "b" = ifelse(mat_SYN_icepellets0_vect == 0 & mat0_icepellets_vect == 1, 1, 0),
                                "c" = ifelse(mat_SYN_icepellets0_vect == 1 & mat0_icepellets_vect == 0, 1, 0),
                                "d" = ifelse(mat_SYN_icepellets0_vect == 0 & mat0_icepellets_vect == 0, 1, 0))
  
  a0_vec <- sum(matSYN_MOD0_vec$a)
  b0_vec <- sum(matSYN_MOD0_vec$b)
  c0_vec <- sum(matSYN_MOD0_vec$c)
  d0_vec <- sum(matSYN_MOD0_vec$d)
  
  write.table(c(a0_vec,b0_vec,c0_vec,d0_vec), file=paste0(PATH_model_mannual,'indexes_icepellets0_',val,'.txt'), row.names=F, col.names=F)
  
  bias_icepellets0[pi] <-  (a0_vec+b0_vec)/(a0_vec+c0_vec)
  names(bias_icepellets0)[pi] <- paste0("BIAS0_probs_icepellets",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_icepellets24_list","SYN_man_icepellets24_list","MOD_man_icepellets96_list","SYN_man_icepellets96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  mat24_icepellets <- matrix(NA, ncol = 51, nrow = length(MOD_man_icepellets24_list))
  for (i in 1:length(MOD_man_icepellets24_list)) {
   # print(i)
    MOD_man_icepellets24_list_YES <- round((MOD_man_icepellets24_list[i]*51)/100)
    list_MODyes24 <- rep(1, MOD_man_icepellets24_list_YES)
    MOD_man_icepellets24_list_NO <- round(((100-MOD_man_icepellets24_list[i])*51)/100)
    list_MODno24 <- rep(0, MOD_man_icepellets24_list_NO)
    list_MODyesno24 <- append(list_MODyes24,list_MODno24)
    mat24_icepellets[i,] <- list_MODyesno24
  }
  mat24_icepellets_vect <- as.vector(t(mat24_icepellets))
  
  
  mat_SYN_icepellets24 <- matrix(NA, ncol = 51, nrow = length(SYN_man_icepellets24_list))
  for (i in 1:length(SYN_man_icepellets24_list)) {
    list_SYN24 <- rep(SYN_man_icepellets24_list[i], 51)
    mat_SYN_icepellets24[i,] <- list_SYN24
  }
  mat_SYN_icepellets24_vect <- as.vector(t(mat_SYN_icepellets24))
  
  matSYN_MOD24_vec <- data.frame("Syn" = mat_SYN_icepellets24_vect, "Mod" = mat24_icepellets_vect, 
                                 "a" = ifelse(mat_SYN_icepellets24_vect == 1 & mat24_icepellets_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_icepellets24_vect == 0 & mat24_icepellets_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_icepellets24_vect == 1 & mat24_icepellets_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_icepellets24_vect == 0 & mat24_icepellets_vect == 0, 1, 0))
  
  a24_vec <- sum(matSYN_MOD24_vec$a)
  b24_vec <- sum(matSYN_MOD24_vec$b)
  c24_vec <- sum(matSYN_MOD24_vec$c)
  d24_vec <- sum(matSYN_MOD24_vec$d)
  
  write.table(c(a24_vec,b24_vec,c24_vec,d24_vec), file=paste0(PATH_model_mannual,'indexes_icepellets24_',val,'.txt'), row.names=F, col.names=F)
  
  
  bias_icepellets24[pi] <-  (a24_vec+b24_vec)/(a24_vec+c24_vec)
  names(bias_icepellets24)[pi] <- paste0("BIAS24_probs_icepellets",val)
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","MOD_man_icepellets96_list","SYN_man_icepellets96_list","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
  
  mat96_icepellets <- matrix(NA, ncol = 51, nrow = length(MOD_man_icepellets96_list))
  for (i in 1:length(MOD_man_icepellets96_list)) {
   # print(i)
    MOD_man_icepellets96_list_YES <- round((MOD_man_icepellets96_list[i]*51)/100)
    list_MODyes96 <- rep(1, MOD_man_icepellets96_list_YES)
    MOD_man_icepellets96_list_NO <- round(((100-MOD_man_icepellets96_list[i])*51)/100)
    list_MODno96 <- rep(0, MOD_man_icepellets96_list_NO)
    list_MODyesno96 <- append(list_MODyes96,list_MODno96)
    mat96_icepellets[i,] <- list_MODyesno96
  }
  mat96_icepellets_vect <- as.vector(t(mat96_icepellets))
  
  mat_SYN_icepellets96 <- matrix(NA, ncol = 51, nrow = length(SYN_man_icepellets96_list))
  for (i in 1:length(SYN_man_icepellets96_list)) {
    list_SYN96 <- rep(SYN_man_icepellets96_list[i], 51)
    mat_SYN_icepellets96[i,] <- list_SYN96
  }
  mat_SYN_icepellets96_vect <- as.vector(t(mat_SYN_icepellets96))
  
  
  matSYN_MOD96_vec <- data.frame("Syn" = mat_SYN_icepellets96_vect, "Mod" = mat96_icepellets_vect, 
                                 "a" = ifelse(mat_SYN_icepellets96_vect == 1 & mat96_icepellets_vect == 1, 1, 0),
                                 "b" = ifelse(mat_SYN_icepellets96_vect == 0 & mat96_icepellets_vect == 1, 1, 0),
                                 "c" = ifelse(mat_SYN_icepellets96_vect == 1 & mat96_icepellets_vect == 0, 1, 0),
                                 "d" = ifelse(mat_SYN_icepellets96_vect == 0 & mat96_icepellets_vect == 0, 1, 0))
  
  a96_vec <- sum(matSYN_MOD96_vec$a)
  b96_vec <- sum(matSYN_MOD96_vec$b)
  c96_vec <- sum(matSYN_MOD96_vec$c)
  d96_vec <- sum(matSYN_MOD96_vec$d)
  
  write.table(c(a96_vec,b96_vec,c96_vec,d96_vec), file=paste0(PATH_model_mannual,'indexes_icepellets96_',val,'.txt'), row.names=F, col.names=F)
  
  
  bias_icepellets96[pi] <- (a96_vec+b96_vec)/(a96_vec+c96_vec)
  names(bias_icepellets96)[pi] <- paste0("BIAS96_probs_icepellets",val) 
  
  rm(list=setdiff(ls(), c("pi","val","PATH_model_mannual","PATH_SYNOP_mannual","bias_rain0","bias_rain24","bias_rain96","bias_snow0","bias_snow24","bias_snow96","bias_freezrain0","bias_freezrain24","bias_freezrain96","bias_freezdrizzle0","bias_freezdrizzle24","bias_freezdrizzle96","bias_icepellets0","bias_icepellets24","bias_icepellets96","bias_sleet0","bias_sleet24","bias_sleet96","PATH_plots","Prates","")))
  gc()
  
}

##### PLOT THE BIAS FOR ALL THE PRECIPITATION RATE THRESHOLDS #####

PLOT_0_24 <- file.path(PATH_plots, "MEAN_BIAS_precrate0_24_2023_48r1esuite.pdf")
PLOT_24_48 <- file.path(PATH_plots, "MEAN_BIAS_precrate24_48_2023_48r1esuite.pdf")
PLOT_96_120 <- file.path(PATH_plots, "MEAN_BIAS_precrate96_120_2023_48r1esuite.pdf")

Verif_Date<-Sys.Date()-9
format(Verif_Date, format="%Y%m%d")


#png(PLOT_0_24, width = 4, height = 4, units = 'in', res = 300)
pdf(PLOT_0_24)
x <- c(0.02,0.05,0.07,0.1,0.12)
plot(x,c(bias_rain0$BIAS0_probs_rain002,bias_rain0$BIAS0_probs_rain005,bias_rain0$BIAS0_probs_rain007,bias_rain0$BIAS0_probs_rain01,bias_rain0$BIAS0_probs_rain012),type="b", pch=21, col="green3",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2),main=paste("BIAS 0-24h lead time ENS (48r1)\n","Verification period 2023-02-16 - 2023-04-15"))
par(new=TRUE)

plot(x,c(bias_snow0$BIAS0_probs_snow002,bias_snow0$BIAS0_probs_snow005,bias_snow0$BIAS0_probs_snow007,bias_snow0$BIAS0_probs_snow01,bias_snow0$BIAS0_probs_snow012),type="b", pch=21, col="blue",lwd = 3, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS",ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_freezrain0$BIAS0_probs_freezrain002,bias_freezrain0$BIAS0_probs_freezrain005,bias_freezrain0$BIAS0_probs_freezrain007,bias_freezrain0$BIAS0_probs_freezrain01,bias_freezrain0$BIAS0_probs_freezrain012),type="b", pch=21, col="red",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_freezdrizzle0$BIAS0_probs_freezdrizzle002,bias_freezdrizzle0$BIAS0_probs_freezdrizzle005,bias_freezdrizzle0$BIAS0_probs_freezdrizzle007,bias_freezdrizzle0$BIAS0_probs_freezdrizzle01,bias_freezdrizzle0$BIAS0_probs_freezdrizzle012),type="b", pch=21, col="deeppink2",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_icepellets0$BIAS0_probs_icepellets002,bias_icepellets0$BIAS0_probs_icepellets005,bias_icepellets0$BIAS0_probs_icepellets007,bias_icepellets0$BIAS0_probs_icepellets01,bias_icepellets0$BIAS0_probs_icepellets012),type="b", pch=21, col="orange",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_sleet0$BIAS0_probs_sleet002,bias_sleet0$BIAS0_probs_sleet005,bias_sleet0$BIAS0_probs_sleet007,bias_sleet0$BIAS0_probs_sleet01,bias_sleet0$BIAS0_probs_sleet012),type="b", pch=21, col="turquoise3",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)
abline(1,0,lwd=4, lty=2)

legend(0.08,2.2, c("rain","snow","freezing rain","freezing drizzle","icepellets","sleet"), cex=0.8, lty = c(1,1,1,1,1,1),lwd = 3,
       col=c("green3","blue","red","pink","orange","turquoise3"))
dev.off()

#png(PLOT_24_48, width = 4, height = 4, units = 'in', res = 300)
pdf(PLOT_24_48)
x <- c(0.02,0.05,0.07,0.1,0.12)
plot(x,c(bias_rain24$BIAS24_probs_rain002,bias_rain24$BIAS24_probs_rain005,bias_rain24$BIAS24_probs_rain007,bias_rain24$BIAS24_probs_rain01,bias_rain24$BIAS24_probs_rain012),type="b", pch=21, col="green3",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2),main=paste("BIAS 24-48h lead time ENS (48r1)\n","Verification period 2023-02-16 - 2023-04-15"))
par(new=TRUE)

plot(x,c(bias_snow24$BIAS24_probs_snow002,bias_snow24$BIAS24_probs_snow005,bias_snow24$BIAS24_probs_snow007,bias_snow24$BIAS24_probs_snow01,bias_snow24$BIAS24_probs_snow012),type="b", pch=21, col="blue",lwd = 3, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS",ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_freezrain24$BIAS24_probs_freezrain002,bias_freezrain24$BIAS24_probs_freezrain005,bias_freezrain24$BIAS24_probs_freezrain007,bias_freezrain24$BIAS24_probs_freezrain01,bias_freezrain24$BIAS24_probs_freezrain012),type="b", pch=21, col="red",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_freezdrizzle24$BIAS24_probs_freezdrizzle002,bias_freezdrizzle24$BIAS24_probs_freezdrizzle005,bias_freezdrizzle24$BIAS24_probs_freezdrizzle007,bias_freezdrizzle24$BIAS24_probs_freezdrizzle01,bias_freezdrizzle24$BIAS24_probs_freezdrizzle012),type="b", pch=21, col="deeppink2",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_icepellets24$BIAS24_probs_icepellets002,bias_icepellets24$BIAS24_probs_icepellets005,bias_icepellets24$BIAS24_probs_icepellets007,bias_icepellets24$BIAS24_probs_icepellets01,bias_icepellets24$BIAS24_probs_icepellets012),type="b", pch=21, col="orange",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_sleet24$BIAS24_probs_sleet002,bias_sleet24$BIAS24_probs_sleet005,bias_sleet24$BIAS24_probs_sleet007,bias_sleet24$BIAS24_probs_sleet01,bias_sleet24$BIAS24_probs_sleet012),type="b", pch=21, col="turquoise3",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)
abline(1,0,lwd=4, lty=2)

legend(0.08,2.2, c("rain","snow","freezing rain","freezing drizzle","icepellets","sleet"), cex=0.8, lty = c(1,1,1,1,1,1),lwd = 3,
       col=c("green3","blue","red","pink","orange","turquoise3"))
dev.off()

#png(PLOT_96_120, width = 4, height = 4, units = 'in', res = 300)
pdf(PLOT_96_120)
x <- c(0.02,0.05,0.07,0.1,0.12)
plot(x,c(bias_rain96$BIAS96_probs_rain002,bias_rain96$BIAS96_probs_rain005,bias_rain96$BIAS96_probs_rain007,bias_rain96$BIAS96_probs_rain01,bias_rain96$BIAS96_probs_rain012),type="b", pch=21, col="green3",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2),main=paste("BIAS 96-120h lead time ENS (48r1)\n","Verification period 2023-02-16 - 2023-04-15"))
par(new=TRUE)

plot(x,c(bias_snow96$BIAS96_probs_snow002,bias_snow96$BIAS96_probs_snow005,bias_snow96$BIAS96_probs_snow007,bias_snow96$BIAS96_probs_snow01,bias_snow96$BIAS96_probs_snow012),type="b", pch=21, col="blue",lwd = 3, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS",ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_freezrain96$BIAS96_probs_freezrain002,bias_freezrain96$BIAS96_probs_freezrain005,bias_freezrain96$BIAS96_probs_freezrain007,bias_freezrain96$BIAS96_probs_freezrain01,bias_freezrain96$BIAS96_probs_freezrain012),type="b", pch=21, col="red",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_freezdrizzle96$BIAS96_probs_freezdrizzle002,bias_freezdrizzle96$BIAS96_probs_freezdrizzle005,bias_freezdrizzle96$BIAS96_probs_freezdrizzle007,bias_freezdrizzle96$BIAS96_probs_freezdrizzle01,bias_freezdrizzle96$BIAS96_probs_freezdrizzle012),type="b", pch=21, col="deeppink2",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_icepellets96$BIAS96_probs_icepellets002,bias_icepellets96$BIAS96_probs_icepellets005,bias_icepellets96$BIAS96_probs_icepellets007,bias_icepellets96$BIAS96_probs_icepellets01,bias_icepellets96$BIAS96_probs_icepellets012),type="b", pch=21, col="orange",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)

plot(x,c(bias_sleet96$BIAS96_probs_sleet002,bias_sleet96$BIAS96_probs_sleet005,bias_sleet96$BIAS96_probs_sleet007,bias_sleet96$BIAS96_probs_sleet01,bias_sleet96$BIAS96_probs_sleet012),type="b", pch=21, col="turquoise3",lwd = 3,
     lty=1, xlab="Precipitation rate threshold (mm/h)", ylab="BIAS", ylim=c(0,2.2))
par(new=TRUE)
abline(1,0,lwd=4, lty=2)

legend(0.08,2.2, c("rain","snow","freezing rain","freezing drizzle","icepellets","sleet"), cex=0.8, lty = c(1,1,1,1,1,1),lwd = 3,
       col=c("green3","blue","red","pink","orange","turquoise3"))
dev.off()


