import boto3
import time
import json
import uuid

cf = boto3.client('cloudformation')

def get_template(stack_name):
    response = cf.get_template(StackName=stack_name)
    return response['TemplateBody']

def create_changeset(stack_name, template_body):
    changeset_name = f"ChangeSet-{uuid.uuid4()}"

    template_body_json = json.dumps(template_body)

    response = cf.create_change_set(
        StackName=stack_name,
        TemplateBody=template_body_json,
        ChangeSetName=changeset_name,
        ChangeSetType='UPDATE',
        Capabilities=['CAPABILITY_NAMED_IAM']
    )

    changeset_id = response['Id']

    while True:
        time.sleep(5)
        result = cf.describe_change_set(ChangeSetName=changeset_id)
        status = result['Status']
        if status in ['CREATE_COMPLETE', 'FAILED']:
            break

    return {
        "change_set_id": changeset_id,
        "status": status,
        "reason": result.get("StatusReason", "")
    }