from src.logger import Logger

from src.helper.aws.iam import get_session as aws_iam_get_session
from botocore.exceptions import ClientError

log = Logger.get_logger()

def submit_job(job_queue_arn, job_definition_arn, environments, workflow_job_type, workflow_job_id):
    client = aws_iam_get_session().client('batch')

    try:
        log.info(f"clicktromics_{workflow_job_type}_{workflow_job_id}")
        response = client.submit_job(
            jobName=f"clicktromics_{workflow_job_type}_{workflow_job_id}",
            jobQueue=job_queue_arn,
            jobDefinition=job_definition_arn,
            containerOverrides={
                "environment": environments
            },
            propagateTags=True
        )
    except ClientError as e:
        log.error("Unexpected error: %s" % e)
        return None

    return response

def terminate_job(job_id, reason="Client Request"):
    client = aws_iam_get_session().client('batch')

    try:
        response = client.terminate_job(
            jobId=job_id,
            reason=reason
        )
    except ClientError as e:
        log.error("Unexpected error: %s" % e)
        return None

    return response


def poll_job(job_id):
    client = aws_iam_get_session().client('batch')

    try:
        response = client.describe_jobs(jobs=[job_id])
        job = response['jobs'][0]
    except ClientError as e:
        log.error("Unexpected error: %s" % e)
        return None

    return job  
        
        

