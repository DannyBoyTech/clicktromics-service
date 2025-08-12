from src.logger import Logger
import os
import boto3
from src.config import ENV, AWS_ACCESS_KEY as SERVICES_AWS_ECS_USER_ACCESS_KEY_ID, AWS_SECRET_KEY as SERVICES_AWS_ECS_USER_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION as SERVICES_AWS_ECS_USER_DEFAULT_REGION

log = Logger.get_logger()

def get_session():
    # Use non-default for non-prod
    if ENV in ["STAGE", "LOCAL_DOCKER", "LOCAL"]:
        return boto3.Session(aws_access_key_id=SERVICES_AWS_ECS_USER_ACCESS_KEY_ID,
                                aws_secret_access_key=SERVICES_AWS_ECS_USER_SECRET_ACCESS_KEY,
                                region_name=SERVICES_AWS_ECS_USER_DEFAULT_REGION)

    return boto3.Session()

def get_session_assumed_role(role_arn: str):
    session = get_session()

    sts_client = session.client('sts')

    identity = sts_client.get_caller_identity()

    log.debug(f"services:aws:assumed_role_session::caller identity {identity}")

    response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName='auth_to_notifications')

    session = boto3.Session(aws_access_key_id=response['Credentials']['AccessKeyId'],
                            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                            aws_session_token=response['Credentials']['SessionToken'])
    
    return session
