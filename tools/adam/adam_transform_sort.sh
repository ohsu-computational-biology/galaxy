#!/bin/bash

#SET Argument variables
#HDFS_INPUT_PATH_FILE=/user/vijaym/adam/NA12878.bam
#HDFS_OUTPUT_PATH_FILE=/user/vijaym/adam/NA12878_CCC_TEST.adam
HDFS_INPUT_PATH_FILE=$1
HDFS_OUTPUT_PATH_FILE=$2
SEARCH='//'
HDFS_INPUT_PATH_FILE=${HDFS_INPUT_PATH_FILE/'//'/'/'}
HDFS_OUTPUT_PATH_FILE=${HDFS_OUTPUT_PATH_FILE/'//'/'/'}

#BEGIN Debugging the status of variables
NEW_LINE=`printf "\n\r"`
echo "===============START DEBUG===============" $NEW_LINE
echo "START DATE & TIME:$(date +"%m-%d-%Y %T")" $NEW_LINE
echo "HDFS_INPUT_PATH:"$HDFS_INPUT_PATH_FILE $NEW_LINE
echo "HDFS_OUTPUT_PATH:"$HDFS_OUTPUT_PATH_FILE $NEW_LINE
#END Debugging the status of variables

#--executor-cores 24 --executor-memory 125g
# --conf spark.shuffle.service.enable=true --master spark://g1.spark0.intel.com:7077 
####################################################################################################
# This function checks for success failure errors and captures the errors into the log file
# It accepts two parameters. 
#    Parm1:  always $? becuase the last command executed needs to be captured
#    Parm2:  string. sucess message
#    Parm3:  string. stderror message unsucessful message
#    Parm4:  0 or non 0 integer. if 0 the program exits if not it continues
# Author: Vijay Ranjan mungara
# Version: 1.0   5/8/2013
# Eample usage: iferr=$(ls $1 2>&1) 
#               fnc_check_error $? "ls was successful" "$iferr" 0
####################################################################################################
fnc_check_error() {
ret_cd=$1
NEWER_LINE=`printf "\n\r"`
if [ $ret_cd -ne 0 ]; then
   echo `date` ":-EXECUTION-FAILED-WITH-RETURN-CODE:-'$ret_cd': AND-WITH-FAILURE-MESSAGE: $NEWER_LINE$3"
   if [ $4 -eq 0 ]; then
	exit $ret_cd
   fi
else
   echo `date` ":-Execution succeeded With: $2"
fi
}

#hadoop fs -rm -r $HDFS_OUTPUT_PATH_FILE
iferr=$(hadoop fs -rm -r $HDFS_OUTPUT_PATH_FILE 2>&1)
fnc_check_error $? "DELETED the Ouput File In case it exists" "$iferr" 1
iferr=$(adam-submit --conf spark.shuffle.service.enable=true --master yarn-client transform $HDFS_INPUT_PATH_FILE $HDFS_OUTPUT_PATH_FILE  -sort_reads 2>&1)
fnc_check_error $? "Transform Sorting Function Succeeded on Hadoop/Spark/Adam" "$iferr" 0
echo "END DATE & TIME:$(date +"%m-%d-%Y %T")" $NEW_LINE
echo "===============END DEBUG==============="