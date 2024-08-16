import pulumi
import pulumi_aws as aws
import json

# 만들어질 함수 이름
function_name = "resize_function"
# 이미 존재하는 s3 버킷 이름 (버킷이 존재 해야 함)
existing_bucket_name = "pulumi-resize-bucket"

assume_role = aws.iam.get_policy_document(
    statements=[
        {
            "effect": "Allow",
            "principals": [
                {
                    "type": "Service",
                    "identifiers": ["lambda.amazonaws.com"],
                }
            ],
            "actions": ["sts:AssumeRole"],
        }
    ]
)

resize_function_role = aws.iam.Role(
    "resize_function_role",
    name="resize_function_role",
    assume_role_policy=assume_role.json,
)

cloudwatch_policy = aws.iam.RolePolicy(
    "cloudwatch_policy",
    role=resize_function_role.name,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "logs:CreateLogGroup",
                    "Resource": "arn:aws:logs:ap-northeast-2:632854243364:*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                    "Resource": [
                        f"arn:aws:logs:ap-northeast-2:632854243364:log-group:/aws/lambda/{function_name}:*"
                    ],
                },
            ],
        }
    ),
)

func = aws.lambda_.Function(
    "func",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
    name=function_name,
    role=resize_function_role.arn,
    runtime="python3.11",
    handler="handler.resize_image",
)

# 존재하는 s3 bucket 에 접근함
bucket = aws.s3.Bucket.get("bucket", id=existing_bucket_name)
allow_bucket = aws.lambda_.Permission(
    "allow_bucket",
    statement_id="AllowExecutionFromS3Bucket",
    action="lambda:InvokeFunction",
    function=func.arn,
    principal="s3.amazonaws.com",
    source_arn=bucket.arn,
)

bucket_notification = aws.s3.BucketNotification(
    "bucket_notification",
    bucket=bucket.id,
    lambda_functions=[
        {
            "lambda_function_arn": func.arn,
            "events": ["s3:ObjectCreated:*"],
            "filter_prefix": "images/",
        }
    ],
    opts=pulumi.ResourceOptions(depends_on=[allow_bucket]),
)
