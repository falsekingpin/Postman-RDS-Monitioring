# Postman-RDS-Monitioring
This repo contains answers to assignment from Postman

## Configurations/Deployment
1. Environment variables to setup :
- DB_USERNAME = usernamne for db access
- DB_PASSWORD = password for db access
- Set function.handler : monitor_rds_metrics.monitor_rds

2. Upload the zip to lambda console or through command-line
```sh
aws lambda update-function-code --function-name monitor_rds_metrics --zip-file fileb://path-to-file/monitor_rds_metrics.zip
```
3. Test with creating sample input

4. Function Parameters
- execution environment : python
- service permissions : aws cloudwatch, rds, lambda
- memory : 2048mb
- function_name : monitor_rds_metrics
- handler_name : monitor_rds

## Process Logic
1. The function is written to test manually, and can be modified to work in conjuction with other aws services.

2. Metrics Published to CloudWatch :
- Percentage of auto-increment capacity consumed
- Time left for RDS instance's disk to full

3. Calculation of auto-increment capacity consumed
- Have used a query which uses perfomance schema, information schema from where we retieve values for max auto-increment capacity and consumed capacity
- After having consumed and max capacity for all tables in a database, we calculate the percentage of auto-increment capacity consumed.
- The metric in cloudwatch can be found under namespace = RDS, dimensions as name = RDS Auto-Increment Consumed and value = Consumption.
- This metric is calculated on per RDS DB instance wise.

4. Calculation of time-to-disk full
- With the help of cloudwatch, we take help of write-throughput to calculate it.
- Write-Throughput is number of bytes written per sec, in such manner we get total number of bytes written per hour for a given timeframe.
- As we also know the storage of the RDS DB, we calculate the time left for disk to full.
- This metric is calculated on per RDS DB instance wise.