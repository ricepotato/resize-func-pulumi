import pulumi
import pulumi_aws as aws



# Existing buckets
source_bucket_name = "my-bucket"

# Source and destination buckets
source_bucket = aws.s3.Bucket(source_bucket_name)

aws.s3.BucketNotification("bucket_notification", bucket=source_bucket.id)

# Lambda IAM Role
lambda_role = aws.iam.Role("lambdaRole",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }"""
)



# IAM Policy for Lambda
lambda_policy = aws.iam.RolePolicy("lambdaPolicy",
    role=lambda_role.id,
    policy={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:*"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": [
                    f"arn:aws:s3:::{source_bucket_name}/*",
                ]
            }
        ]
    }
)

# Lambda function for image resizing
resize_function = aws.lambda_.Function("resizeFunction",
    role=lambda_role.arn,
    runtime="python3.11",
    handler="handler.resize_image",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./lambda")
    })
)

# S3 Bucket notification to trigger the Lambda function
bucket_notification = aws.s3.BucketNotification("bucketNotification",
    bucket=source_bucket.id,
    lambda_functions=[aws.s3.BucketNotificationLambdaFunctionArgs(
        lambda_function_arn=resize_function.arn,
        events=["s3:ObjectCreated:*"],
        filter_prefix="/images/"
    )]
)

# Permission for S3 to invoke the Lambda function
lambda_permission = aws.lambda_.Permission("lambdaPermission",
    action="lambda:InvokeFunction",
    function=resize_function.arn,
    principal="s3.amazonaws.com",
    source_arn=source_bucket.arn
)

# Export the names of the buckets
pulumi.export("source_bucket", source_bucket.id)
pulumi.export("resize_function", resize_function.arn)
pulumi.export("lambda_role", lambda_role.arn)
pulumi.export("bucket_notification", bucket_notification.id)
