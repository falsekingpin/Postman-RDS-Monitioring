import boto3
import pymysql
import logging
from datetime import datetime
from datetime import timedelta
from metrics_rds import RDSOps
from constants import Constants


class CloudWatchOps:
    """
    This class is used for retrieving,tranforming,publishing db metrics to cloudwatch
    """
    logging.basicConfig(filename="monitor_rds_metrics_cloudwatchops.log", 
                    format='%(asctime)s %(message)s', 
                    filemode='w') 

    #Creating an object 
    logger=logging.getLogger() 

    #Setting the threshold of logger to DEBUG 
    logger.setLevel(logging.DEBUG)

    cloudwatch_client = boto3.client('cloudwatch')

    def process_logic(self, db_username, db_password):
        """
        This function is the initiating point for retrieving,transforming,publishing functions

        @params:
        DB username
        DB password 
        """
        instance_details = RDSOps().get_instance_statistics()
        rds_metrics = self.process_for_rds_metrics(
            instance_details, db_username, db_password)
        metric_to_publish = self.prepare_metrics_to_publish(rds_metrics,source_type='RDS')
        self.publish_metrics(metric_to_publish,source_type='RDS_Percentage')

        self.get_write_throughput(instance_details)

    def get_write_throughput(self, dbinstanceidentifierlist):
        """
        This function retruns the stats about write throughput given an instance-identifier

        @params:
        Instance-identifier : unique udentifier for db instances
        """
        for instance_detail in dbinstanceidentifierlist:
            N = 1
            print("instance detail : {}".format(instance_detail))
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='WriteThroughput',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': '{}'.format(instance_detail[Constants.INSTANCE_NAME])
                    },
                ],
                StartTime=datetime.now() - timedelta(days=N),
                EndTime=datetime.now(),
                Period=3600,
                Statistics=[
                    'SampleCount'
                ]
            )
            self.prepare_write_throughput_to_publish(response['Datapoints'],instance_detail[Constants.INSTANCE_NAME],instance_detail[Constants.STORAGE])

    def process_for_rds_metrics(self, instance_details_list, db_username, db_password):
        """
        This function is used for processing RDS metrics from instance details

        @params:
        instance_details_list : List of details such as storage_capacity,name,endpoint
        DB_name
        DB_password
        """
        metrics_list = []
        for instance_detail in instance_details_list:
            if(instance_detail[Constants.INSTANCE_NAME] == 'athenasvideo'):
                self.logger.info("Does not have access to this DB")
            else:
                db_connection = self.db_connection(
                    instance_detail[Constants.DB_HOST], db_username, db_password)
                sql_query = Constants.AUTO_INCREMENT_QUERY
                results = self.db_operations(
                    db_connection, sql_query, operation='Select')
                metrics_list.append(results)
        return metrics_list

    def prepare_metrics_to_publish(self,metrics,source_type):
        """
        This metrics is used for preparing message for publishing metrics to cloudwatch

        @params:
        metrics : Acutal metrics data
        source_type : Service from where metrics was obtained

        """
        if(source_type == 'RDS'):
            total_auto_increment = 0
            auto_increment_consumed = 0
            for metrics_list in metrics:
                self.logger.info("Metrics List : {}".format(metrics_list))
                for db_host_metric in metrics_list:
                    self.logger.info("DB Host Metrics : {}".format(db_host_metric))
                    total_auto_increment = total_auto_increment + db_host_metric[6]
                    auto_increment_consumed = auto_increment_consumed + db_host_metric[7]
        return ((float(auto_increment_consumed)/float(total_auto_increment))*100)

    def prepare_write_throughput_to_publish(self,metrics,instance_name,storage):
        """
        This function is used for transforming throughput data and preparing it for
        publishing to cloudwatch

        @params:
        metrics : actual metrics obtained
        instance_name : db instance name
        storage : storage capacity of the instance
        """
        no_of_bytes_per_sec = 0
        total_hours = 0
        for metric in metrics:
            no_of_bytes_per_sec = no_of_bytes_per_sec + float(metric['SampleCount'])
            total_hours = total_hours + 1
            avg_bytes_per_sec_per_hour = no_of_bytes_per_sec / total_hours
            total_bytes_consumed_per_hour = avg_bytes_per_sec_per_hour * total_hours
            time_to_disk_full_in_hrs = float((float(storage) * 1000000000) / total_bytes_consumed_per_hour)
            time_to_disk_full_in_days = float(time_to_disk_full_in_hrs / 24)
        self.publish_time_metrics(instance_name,time_to_disk_full_in_days)

    def publish_metrics(self,metric_to_publish,source_type):
        """
        This function is used for publishing metrics by source type

        @params:
        metric_to_publish : metric obtained after transformation
        source_type : service from which metric was obtained
        """
        if(source_type == 'RDS_Percentage'):
            response = self.cloudwatch_client.put_metric_data(
                        MetricData=[
                            {
                                'MetricName': 'RDS Stats',
                                'Dimensions': [
                                    {
                                        'Name': 'RDS Auto-Increment Consumed',
                                        'Value': 'Consumption'
                                    }
                                ],
                                'Unit': 'Count',
                                'Value': metric_to_publish
                            },
                        ],
                        Namespace='RDS'
                    )
            print(response)

    def publish_time_metrics(self,instance_name,metrics):
        """
        This function is used for publishing time metrics        
        """
        response = self.cloudwatch_client.put_metric_data(
                        MetricData=[
                            {
                                'MetricName': 'RDS Stats',
                                'Dimensions': [
                                    {
                                        'Name': 'RDS Time-To-Disk-Full',
                                        'Value': instance_name
                                    }
                                ],
                                'Unit': 'Count',
                                'Value': metrics
                            },
                        ],
                        Namespace='RDS'
                    )
        print(response)


    def db_connection(self, db_host, db_username, db_password):
        return pymysql.connect(db_host, user=db_username, passwd=db_password, connect_timeout=5)

    def db_operations(self, db_connection, sql_query, operation):
        try:
            # prepare a cursor object using cursor() method
            cursor = db_connection.cursor()
            if(operation == 'Select'):
                cursor.execute(sql_query)
                db_connection.commit()
                return list(cursor)
            elif(operation == 'Execute'):
                cursor.execute(sql_query)
                db_connection.commit()
        except (Exception, AttributeError) as err:
            self.logger.error("Error : {}".format(err))
            # Rollback in case there is any error
            db_connection.rollback()
