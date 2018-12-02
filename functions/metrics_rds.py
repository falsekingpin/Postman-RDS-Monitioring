# -*- coding: utf-8 -*-
__author__ = "Akshay Nar"

#Importing dependencies
import boto3
import logging
from constants import Constants

class RDSOps:
    """
    This class is used for RDS related operations
    """
    logging.basicConfig(filename="monitor_rds_metrics_rdsops.log", 
                    format='%(asctime)s %(message)s', 
                    filemode='w') 

    #Creating an object 
    logger=logging.getLogger() 

    #Setting the threshold of logger to DEBUG 
    logger.setLevel(logging.DEBUG)

    rds_client = boto3.client('rds')

    def get_instance_statistics(self):
        """
        This function returns details about RDS DB instances in your project

        @param : None
        @returns:
        List of details about the instances
        """
        database_metrics_list = []
        responses = self.rds_client.describe_db_instances()
        self.logger.info("Response : {}".format(responses))
        for response in responses[Constants.DB_INSTANCES]:
            metrics = {}
            metrics[Constants.STORAGE] = response[Constants.ALLOCATED_STORAGE]
            metrics[Constants.INSTANCE_NAME] = response[Constants.DB_INSTANCE_IDENTIFIER]
            metrics[Constants.DB_HOST] = response[Constants.ENDPOINT][Constants.ADDRESS]
            database_metrics_list.append(metrics)
        
        self.logger.info("Metrics List : {}".format(database_metrics_list))
        return database_metrics_list