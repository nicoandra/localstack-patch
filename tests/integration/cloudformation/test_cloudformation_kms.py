from localstack.utils.common import short_uid
from localstack.utils.generic.wait_utils import wait_until
from localstack.utils.testing.aws.cloudformation_utils import load_template_raw


def test_kms_key_disabled(
    cfn_client,
    sqs_client,
    kms_client,
    cleanup_stacks,
    cleanup_changesets,
    is_change_set_created_and_available,
    is_stack_created,
):
    stack_name = f"stack-{short_uid()}"
    change_set_name = f"change-set-{short_uid()}"

    template_rendered = load_template_raw("kms_key_disabled.yaml")
    response = cfn_client.create_change_set(
        StackName=stack_name,
        ChangeSetName=change_set_name,
        TemplateBody=template_rendered,
        ChangeSetType="CREATE",
    )
    change_set_id = response["Id"]
    stack_id = response["StackId"]

    try:
        wait_until(is_change_set_created_and_available(change_set_id))
        cfn_client.execute_change_set(ChangeSetName=change_set_id)
        wait_until(is_stack_created(stack_id))
        outputs = cfn_client.describe_stacks(StackName=stack_id)["Stacks"][0]["Outputs"]
        assert len(outputs) == 1
        key_id = outputs[0]["OutputValue"]
        assert key_id
        my_key = kms_client.describe_key(KeyId=key_id)
        assert not my_key["KeyMetadata"]["Enabled"]

    finally:
        cleanup_changesets([change_set_id])
        cleanup_stacks([stack_id])
