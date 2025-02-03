import json
import boto3
import datetime

# Function to get cost report from AWS Cost Explorer
def get_cost_report(start_date, end_date, granularity='DAILY'):
    cost_explorer_client = boto3.client('ce')
    try:
        response = cost_explorer_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity=granularity,
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        return response['ResultsByTime']
    except Exception as e:
        print(f"Error retrieving cost report: {str(e)}")
        return {"Error": str(e)}

# Function to enforce security group rules
def enforce_security_group_rules(security_group_id, region, protocol, port, ip_range):
    ec2_client = boto3.client('ec2', region_name=region)
    
    response = ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': protocol,
                'FromPort': int(port),
                'ToPort': int(port),
                'IpRanges': [{'CidrIp': ip_range}]
            }
        ]
    )
    return {"Status": "Security group rules updated successfully", "SecurityGroupId": security_group_id}

# Function to start an AWS Backup job
def start_backup_job(region, tag_key, tag_value):
    backup_client = boto3.client('backup', region_name=region)

    response = backup_client.start_backup_job(
        ResourceArn=f'arn:aws:ec2:{region}::volume/*',
        IamRoleArn='arn:aws:iam::<account-id>:role/service-role/AWSBackupDefaultServiceRole',
        IdempotencyToken='backup-ec2-production',
        BackupVaultName='Default',
        RecoveryPointTags={
            tag_key: tag_value
        }
    )
    return {"Status": "Backup Job Initiated", "BackupJobId": response['BackupJobId']}

# Function to list EC2 instances in a given region
def list_ec2_instances(region):
    ec2_client = boto3.client('ec2', region_name=region)
    instances = []
    response = ec2_client.describe_instances()
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append({
                'InstanceId': instance['InstanceId'],
                'InstanceType': instance['InstanceType'],
                'State': instance['State']['Name'],
                'LaunchTime': str(instance['LaunchTime']),
                'Region': region
            })
    return {"Instances": instances}

# Function to create AMI backups for EC2 instances
def create_ec2_ami_backups(region, instance_id_list, ami_name_prefix):
    ec2_client = boto3.client('ec2', region_name=region)
    ami_ids = []
    
    if isinstance(instance_id_list, str):
        instance_id_list = instance_id_list.strip('[]').replace(' ', '').split(',')
    
    instance_id_list = [id.strip() for id in instance_id_list]
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    for instance_id in instance_id_list:
        try:
            ami_name = f"{ami_name_prefix}-{instance_id}-{timestamp}"
            response = ec2_client.create_image(
                InstanceId=instance_id,
                Name=ami_name,
                Description=f"Automated backup created on {timestamp}",
                NoReboot=True
            )
            ami_ids.append({
                'InstanceId': instance_id,
                'AmiId': response['ImageId'],
                'AmiName': ami_name
            })
        except Exception as e:
            print(f"Error creating AMI for instance {instance_id}: {str(e)}")
            ami_ids.append({
                'InstanceId': instance_id,
                'Error': str(e)
            })
    
    return {
        "Status": "AMI Creation Process Completed",
        "AMIs": ami_ids,
        "TimestampCreated": timestamp
    }

# Function to start EC2 instance
def start_ec2_instance(instance_id, region):
    ec2_client = boto3.client('ec2', region_name=region)
    response = ec2_client.start_instances(InstanceIds=[instance_id])
    return response

# Function to stop EC2 instance
def stop_ec2_instance(instance_id, region):
    ec2_client = boto3.client('ec2', region_name=region)
    response = ec2_client.stop_instances(InstanceIds=[instance_id])
    return response

# Function to create S3 lifecycle policy
def create_s3_lifecycle_policy(bucket_name, lifecycle_policy):
    s3_client = boto3.client('s3')
    response = s3_client.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration=lifecycle_policy
    )
    return response

# Function to enable RDS Multi-AZ
def enable_rds_multi_az(db_instance_id, region):
    rds_client = boto3.client('rds', region_name=region)
    response = rds_client.modify_db_instance(
        DBInstanceIdentifier=db_instance_id,
        MultiAZ=True,
        ApplyImmediately=True
    )
    return response

# Function to enable S3 versioning
def enable_s3_versioning(bucket_name):
    try:
        s3_client = boto3.client('s3')
        response = s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={
                'Status': 'Enabled'
            }
        )
        return {
            "Status": "S3 Versioning Enabled Successfully",
            "BucketName": bucket_name,
            "Timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Error enabling S3 versioning: {str(e)}")
        return {"Error": str(e)}
# Function to create RDS snapshot
def create_rds_snapshot(db_instance_id, region, snapshot_identifier=None):
    """
    Create a snapshot of an RDS instance or cluster
    """
    try:
        rds_client = boto3.client('rds', region_name=region)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        
        # First, try to determine if this is a cluster member
        try:
            instance_response = rds_client.describe_db_instances(
                DBInstanceIdentifier=db_instance_id
            )
            
            if 'DBClusterIdentifier' in instance_response['DBInstances'][0]:
                # This is a cluster member, get the cluster identifier
                cluster_id = instance_response['DBInstances'][0]['DBClusterIdentifier']
                
                # Create cluster snapshot
                snapshot_id = snapshot_identifier or f"{cluster_id}-snapshot-{timestamp}"
                response = rds_client.create_db_cluster_snapshot(
                    DBClusterSnapshotIdentifier=snapshot_id,
                    DBClusterIdentifier=cluster_id,
                    Tags=[
                        {
                            'Key': 'CreatedBy',
                            'Value': 'AutomatedBackup'
                        },
                        {
                            'Key': 'CreationDate',
                            'Value': datetime.datetime.now().strftime('%Y-%m-%d')
                        }
                    ]
                )
                
                return {
                    "Status": "RDS Cluster Snapshot Creation Initiated",
                    "DBClusterIdentifier": cluster_id,
                    "SnapshotIdentifier": snapshot_id,
                    "SnapshotType": "Cluster",
                    "SnapshotDetails": {
                        "ARN": response['DBClusterSnapshot']['DBClusterSnapshotArn'],
                        "Status": response['DBClusterSnapshot']['Status'],
                        "PercentProgress": response['DBClusterSnapshot'].get('PercentProgress', 0)
                    }
                }
                
            else:
                # This is a standalone instance
                snapshot_id = snapshot_identifier or f"{db_instance_id}-snapshot-{timestamp}"
                response = rds_client.create_db_snapshot(
                    DBSnapshotIdentifier=snapshot_id,
                    DBInstanceIdentifier=db_instance_id,
                    Tags=[
                        {
                            'Key': 'CreatedBy',
                            'Value': 'AutomatedBackup'
                        },
                        {
                            'Key': 'CreationDate',
                            'Value': datetime.datetime.now().strftime('%Y-%m-%d')
                        }
                    ]
                )
                
                return {
                    "Status": "RDS Instance Snapshot Creation Initiated",
                    "DBInstanceIdentifier": db_instance_id,
                    "SnapshotIdentifier": snapshot_id,
                    "SnapshotType": "Instance",
                    "SnapshotDetails": {
                        "ARN": response['DBSnapshot']['DBSnapshotArn'],
                        "Status": response['DBSnapshot']['Status'],
                        "PercentProgress": response['DBSnapshot'].get('PercentProgress', 0)
                    }
                }
                
        except rds_client.exceptions.DBInstanceNotFoundFault:
            # If instance not found, try checking if it's a direct cluster identifier
            try:
                cluster_response = rds_client.describe_db_clusters(
                    DBClusterIdentifier=db_instance_id
                )
                
                # Create cluster snapshot
                snapshot_id = snapshot_identifier or f"{db_instance_id}-snapshot-{timestamp}"
                response = rds_client.create_db_cluster_snapshot(
                    DBClusterSnapshotIdentifier=snapshot_id,
                    DBClusterIdentifier=db_instance_id,
                    Tags=[
                        {
                            'Key': 'CreatedBy',
                            'Value': 'AutomatedBackup'
                        },
                        {
                            'Key': 'CreationDate',
                            'Value': datetime.datetime.now().strftime('%Y-%m-%d')
                        }
                    ]
                )
                
                return {
                    "Status": "RDS Cluster Snapshot Creation Initiated",
                    "DBClusterIdentifier": db_instance_id,
                    "SnapshotIdentifier": snapshot_id,
                    "SnapshotType": "Cluster",
                    "SnapshotDetails": {
                        "ARN": response['DBClusterSnapshot']['DBClusterSnapshotArn'],
                        "Status": response['DBClusterSnapshot']['Status'],
                        "PercentProgress": response['DBClusterSnapshot'].get('PercentProgress', 0)
                    }
                }
                
            except rds_client.exceptions.DBClusterNotFoundFault:
                raise ValueError(f"Neither DB instance nor DB cluster found with identifier: {db_instance_id}")
                
    except Exception as e:
        print(f"Error creating RDS snapshot: {str(e)}")
        return {"Error": str(e)}

def lambda_handler(event, context):
    print("Received event: {}".format(json.dumps(event)))

    try:
        # Extracting necessary fields from the event
        api_path = event.get('apiPath', '')
        request_body = event.get('requestBody', {})
        parameters = request_body.get('content', {}).get('application/json', {}).get('properties', [])

        # Convert parameters list into a dictionary
        params = {param['name']: param['value'] for param in parameters}

        # Determine the action based on the API path
        if api_path == '/get-cost-report':
            result = get_cost_report(params['StartDate'], params['EndDate'], params.get('Granularity', 'DAILY'))
            response = {"ResultsByTime": result}
        elif api_path == '/start-ec2-instance':
            result = start_ec2_instance(params['InstanceId'], params['Region'])
        elif api_path == '/stop-ec2-instance':
            result = stop_ec2_instance(params['InstanceId'], params['Region'])
        elif api_path == '/create-s3-lifecycle-policy':
            result = create_s3_lifecycle_policy(params['BucketName'], params['LifecyclePolicy'])
        elif api_path == '/enable-rds-multi-az':
            result = enable_rds_multi_az(params['DBInstanceId'], params['Region'])
        elif api_path == '/create-ec2-ami-backups':
            required_params = ['Region', 'InstanceIdList', 'AmiNamePrefix']
            if not all(key in params for key in required_params):
                raise ValueError(f"Missing required parameters. Required: {required_params}")
            
            result = create_ec2_ami_backups(
                params['Region'],
                params['InstanceIdList'],
                params['AmiNamePrefix']
            )
        elif api_path == '/list-ec2-instances':
            result = list_ec2_instances(params['Region'])
        elif api_path == '/enforce-security-group-rules':
            result = enforce_security_group_rules(
                params['SecurityGroupId'],
                params['Region'],
                params['Protocol'],
                params['Port'],
                params['IpRange']
            )
        elif api_path == '/enable-s3-versioning':
            if 'BucketName' not in params:
                raise ValueError("Missing required parameter: BucketName")
            
            result = enable_s3_versioning(params['BucketName'])
            
        elif api_path == '/create-rds-snapshot':
            required_params = ['DBInstanceId', 'Region']
            if not all(key in params for key in required_params):
                raise ValueError(f"Missing required parameters. Required: {required_params}")
            
            result = create_rds_snapshot(
                params['DBInstanceId'],
                params['Region'],
                params.get('SnapshotIdentifier', None)
            )
        else:
            raise ValueError(f"Unknown API path: {api_path}")

        # Prepare a standardized response
        action_response = {
            'actionGroup': event['actionGroup'],
            'apiPath': api_path,
            'httpMethod': event['httpMethod'],
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': result
                }
            }
        }

        api_response = {'response': action_response, 'messageVersion': event['messageVersion']}
        print("Response: {}".format(json.dumps(api_response)))
        return api_response

    except Exception as e:
        print("Error: {}".format(str(e)))
        error_response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': "An error occurred during the process.",
                'error': str(e)
            })
        }
        return error_response