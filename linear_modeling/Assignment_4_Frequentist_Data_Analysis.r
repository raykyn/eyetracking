# Solution by Ismail Prada & Andreas Säuberli

# Lena Jäger
# Eyetracking: From experiment design to statistical and machine learning-based data analysis
# Assignment 4: Frequentist statistical analysis of a psycholinguistic eye-tracking-while-reading experiment

# Data set:
#    For a detailed description of the data set used in this assignment, please refer to: 
#    Jäger, Mertzen, Van Dyke, & Vasishth: 'Interference patterns for subject-verb 
#        agreement and reflexives revisited:  A large-sample study', 
#        Journal of Memory and Language, 2020

# Experimental design: 
#   2x2x2 fully crossed factorial desing:
#     Factor I: Dependency type: {subject-verb agreement; reflexive-antecedent binding}
#     Factor II: Grammaticality: {grammatical; ungrammatical}
#     Factor III: Similarity-based interference: {interference; no-intererence}

# Condition labels:   
#   a  Agreement; grammatical; interference
#   b. Agreement; grammatical; no interference
#   c. Agreement; ungrammatical; no interference
#   d. Agreement; ungrammatical; interference
#   e. Reflexive; grammatical; interference
#   f. Reflexive; grammatical; no interference
#   g. Reflexive; ungrammatical; no interference
#   h. Reflexive; ungrammatical; interference

# Column names:
#   subj: subject id
#   item: item id
#   cond: condition id
#   acc: comprehension question response accuracy
#   roi: region of interest 
#   FPRT: first-pass reading times in ms
#   TFT: total fixation times in ms
#   FPR: first-pass regression (binary)

library(coda)
library(plyr)
library(ggplot2)
library(xtable)
library(dplyr)
require(tidyr)
library(tidyverse)
extrafont::loadfonts()
library(reshape2)
require(lme4)


### RESEARCH QUESTIONS:
# 1. Are fixation times different in subject-verb agreement versus reflexive-antecedent dependencies?
# --> main effect of dependency type
# 2. Are fixation times different in ungrammatical versus grammatical conditions?
# --> main effect of grammaticality
# 3. Are fixation times affected by interference?
# --> main effect of interference
# 4. Does the grammaticality effect differ between the two dependency types?
# --> interaction between grammaticality and dependency type
# 5. Does the interference effect differ between grammatical and ungrammatical conditions?
# --> interaction between interference and grammaticality
# 6. Does the interference effect differ between dependency types?
# --> interaction between interference and dependency type
# 7. Does the (possible) difference in the sensitivity to the interference manipulation of 
#     grammatical versus ungrammatical conditions differ between subject-verb agreement and reflexive-antecedent dependencies?
# --> 3-way interaction between interference, grammaticality and dependency type


# Critical region: were/was/himself/themselves (= roi 12)
# Dependent variable: total fixation times


#### Load and format the data
d <- read.table(file='dataJMVV.txt', sep = '\t')

#### Inspect the data and answer the following questions: 
# How many conditions are there? How many instances of each condition?
# 8 conditions (+filler), counts:
# a      b      c      d      e      f  filler      g      h 
# 22659  22659  22659  22596  22680  22638 482412  22680  22617
# How many subjects and items are there?
# 181 subjects
# 176 items
# NOTE: This could also be answered by converting these columns to factors first and then use str()
# How many times did each subject see each item? Hint: use xtabs() )
# 21 times
# What was the average response accuracy for each of the conditions? Hint: use tapply()
# a           b           c           d           e           f 
# -0.05560704 -0.05838740 -0.05004634 -0.06133829 -0.07129630 -0.05751391 
# filler           g           h 
# -0.04718788 -0.05185185 -0.05292479
########################################################
head(d, 3)
d$cond <- factor(d$cond)
summary(d$cond)
length(unique(d$subj))
length(unique(d$item))
xtabs(~subj+item, d)
tapply(d$acc, d$cond, mean)
########################################################


### Convert the subj, item and cond columns to factors
########################################################
d$subj <- factor(d$subj)
d$item <- factor(d$item)
d$cond <- factor(d$cond)
str(d)
########################################################

# Exlcude filler trials and remove all rows from other than the critical region (roi 12)
########################################################
d_crit <- d[d$cond != "filler" & d$roi == 12, ]
########################################################

# Note: when removing all rows with a certain level of a factor, this level still exists, it simply has 0 instances:
summary(d$cond) # before removing the fillers
summary(d_crit$cond) # after removing the fillers
# We can fix this by simply conveting cond to a factor again: 
########################################################
d_crit$cond <- factor(d_crit$cond)
########################################################


#### Define contrasts 
# Create hypothesis matrix from the given research questions
# main effects of dependency and grammaticality and their interaction (applied in Model 1 and 2)
X_H <- matrix(c( 1/8,  1/8,  1/8,  1/8,  1/8,  1/8,  1/8,  1/8, # Intercept
                 1/4,  1/4,  1/4,  1/4, -1/4, -1/4, -1/4, -1/4, # Main effect dependency type
                -1/4, -1/4,  1/4,  1/4, -1/4, -1/4,  1/4,  1/4, # Main effect grammaticality
                 1/4, -1/4, -1/4,  1/4,  1/4, -1/4, -1/4,  1/4, # Main effect of interference
                -1/4, -1/4,  1/4,  1/4,  1/4,  1/4, -1/4, -1/4, # Grammaticality x Dependency
                -1/4,  1/4, -1/4,  1/4, -1/4,  1/4, -1/4,  1/4, # Interference x Grammaticality
                 1/4, -1/4, -1/4,  1/4, -1/4,  1/4,  1/4, -1/4, # Interference x Dependency type
                -1/4,  1/4, -1/4,  1/4,  1/4, -1/4,  1/4, -1/4  # Interference x Grammaticality x Dependency
), byrow=TRUE, nrow = 8)

# Compute the inverse of X_H
########################################################
library(MASS)  # need this for ginv()
X_C <- ginv(X_H)
########################################################

# For better readibility add column and row names: 
rownames(X_C) <- c('a','b','c','d','e','f','g','h')
colnames(X_C) <- c('Intercept','Dep','Gram','Int','Gram_x_Dep','Int_x_Gram','Int_x_Dep','Int_x_Gram_x_Dep')

# Remove intercept column
########################################################
X_C_bar <- X_C[,2:ncol(X_C)]
########################################################

# Apply the contrasts to the cond column
########################################################
contrasts(d_crit$cond) <- X_C_bar
########################################################


#--------------------------------------------------------
#--------------------------------------------------------
# OR: 
# Alternative: code contrasts as numerical columns in the dataframe and use these as predictors in the model

# NOTE: Why did they use d and not d_crit here?
d_crit$Dep <- ifelse(d_crit$cond %in% c('a', 'b', 'c', 'd'), .5, -.5) # main effect of dependency type: agr=0.5, refl=-0.5
d_crit$Gram <- ifelse(d_crit$cond %in% c('a', 'b', 'e', 'f'), -.5, .5) # main effect of grammaticality: gram=-.5, ungram=.5
# ... add the other contrasts
########################################################
d_crit$Int <- ifelse(d_crit$cond %in% c('a', 'd', 'e', 'h'), .5, -.5)
d_crit$Gram_x_Dep <- ifelse(d_crit$cond %in% c('c', 'd', 'e', 'f'), .5, -.5)
d_crit$Int_x_Gram <- ifelse(d_crit$cond %in% c('b', 'd', 'f', 'h'), .5, -.5)
d_crit$Int_x_Dep <- ifelse(d_crit$cond %in% c('a', 'd', 'f', 'g'), .5, -.5)
d_crit$Int_x_Gram_x_Dep <- ifelse(d_crit$cond %in% c('b', 'd', 'e', 'g'), .5, -.5)
########################################################

#--------------------------------------------------------
#--------------------------------------------------------

# Remove trials in which the dependent variable (TFT) is zero (i.e., trials in which the critical region was never fixated)
########################################################
d_crit_tft <- d_crit[d_crit$TFT != 0, ]
########################################################
# How many trials (=rows) in % are removed by selecting only the ones with TFT larger than 0? 
# 0.07765415 => 7.77% of all trials were removed
########################################################
1 - nrow(d_crit_tft) / nrow(d_crit)
########################################################

# Fit a linear mixed model with log transformed total fixation times as dependent variable and the above defined contrasts as predictor variables (independent variables)
library(lme4)
########################################################
# With contrasts coded as columns:
m <- lmer(log(TFT)~
            Dep+
            Gram+
            Int+
            Gram_x_Dep+
            Int_x_Gram+
            Int_x_Dep+
            Int_x_Gram_x_Dep+
            (1|subj)+
            (1|item),
            data=d_crit_tft)
########################################################
# With contrasts coded using contrasts():
m <- lmer(log(TFT)~cond+(1|subj)+(1|item), data=d_crit_tft)
summary(m)

# Interpret the model output verbally.
########################################################
# t values for Dep and Gram are large enough to be significant,
# i.e. dependency type and grammaticality have a significant
# effect on logarithmic total fixation time.
# The estimated betas for these contrasts are positive, which means:
# - Subject-verb agreement has larger TFT than reflexive-antecedent binding
# - Ungrammatical items have larger TFT than grammatical ones
# The other contrasts do not show significant effects.
########################################################

# We have modeled log(TFT). However, for the conceptual interpretation, it is often easier to express the effect sizes on the ms-scale rather than the log-ms scale
# Compute the effect sizes of the predictors to the ms-scale. H

# Effect of dependency type on the ms scale              
########################################################
# NOTE: Not sure if this is really what they mean...

# A change from "reflexive" to "agreement" dependency type increases log(TFT) by 0.2775904
# This corresponds to multiplying TFT by e^0.2775904 = 1.319945
ms_effects <- exp(fixef(m))
ms_effects["condDep"]

# For example, the average TFT for the "reflexive" dependency type is 553.5267 ms:
average_reflexive_tft <-
    d_crit_tft %>%
    filter(cond %in% c("e", "f", "g", "h")) %>%
    summarize(mean(TFT))

# Applying a factor of 1.319945 would mean an expected increase by 177.0983 ms
# when changing the dependency type to "agreement":
ms_increase <- average_reflexive_tft * ms_effects["condDep"] - average_reflexive_tft
########################################################
