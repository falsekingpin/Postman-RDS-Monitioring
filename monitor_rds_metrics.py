# -*- coding: utf-8 -*-
__author__ = "Akshay Nar"

#Importing dependencies
import sys
import json
import logging
import pymysql
import os
import boto3
import metrics_cloudwatch

logging.basicConfig(filename="monitor_rds_metrics.log", 
                    format='%(asctime)s %(message)s', 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 

#Setting the threshold of logger to DEBUG 
logger.setLevel(logging.DEBUG)


def monitor_rds(event, context):
    """
    This function is used for initiating the process logic for monitoring RDS

    @params:
    event = It can take events from different aws services
    context = It uses this paramter to provide runtime information

    @returns:
    Status Code = numeric code
    Status Message = message if function executed successfully
    """

    #initializing db credentials
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')

    #Initating the process logic for monitoring
    try:
        logger.info("Initiating Process for monitoring")
        metrics_cloudwatch.CloudWatchOps().process_logic(db_username,db_password)
        logger.info("Completed the process successfully")
    except Exception as e:
        #Logging exceptions
        logger.error("ERROR: {}".format(e))
        sys.exit()
        return {
            'statusCode': 400,
            'body': json.dumps('Function encountered some error')
        }
        
    logger.info("Published metrics to cloudwatch successfully")

    return {
        'statusCode': 200,
        'body': json.dumps('Function Exceuted Successfully')
    }
