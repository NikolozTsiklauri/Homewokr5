import boto3
from pathlib import Path
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
client = boto3.client('lambda')
iam = boto3.client('iam')


file_extensions = ['.jpg', '.jpeg', '.png']

def convert_bytes(zip_file):
    with open(zip_file, 'rb') as file_data:
        bytes_content = file_data.read()
    return bytes_content


def function(function_name, iam_role, function_handler, zip_file):
    try:
        client.create_function(
            FunctionName=function_name,
            Runtime='python3.8',
            Role=iam.get_role(RoleName=iam_role)['Role']['Arn'],
            Handler=f'{Path(zip_file).stem}.{function_handler}',
            Code={
                'ZipFile': convert_bytes(zip_file)
            },
        )
        print(f'function {function_name} has been created')
    except ClientError as ex:
        print(ex)


def permision(function_name, name_of_bucket):
    client.add_permission(
        FunctionName=function_name,
        StatementId='1',
        Action='lambda:InvokeFunction',
        Principal='s3.amazonaws.com',
        SourceArn=f'arn:aws:s3:::{name_of_bucket}',
    )


def s3_trigger(name_of_bucket, function_name):
    lambda_foreach = []
    for extension in file_extensions:
        lambda_foreach.append({
            'LambdaFunctionArn': client.get_function(
                FunctionName=function_name)['Configuration']['FunctionArn'],
            'Events': [
                's3:ObjectCreated:*'
            ],
            'Filter': {
                'Key': {
                    'FilterRules': [
                        {
                            'Name': 'suffix',
                            'Value': extension
                        },
                    ]
                }
            }
        },)
    try:
        permision(function_name, name_of_bucket)
        s3.put_bucket_notification_configuration(
            Bucket=name_of_bucket,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': lambda_foreach,
            }
        )
        print(f'{function_name} has been added to {name_of_bucket}')
    except ClientError as ex:
        print(ex)



def main(function_name, iam_role, function_handler, zip_file, name_of_bucket):
    function(function_name, iam_role, function_handler, zip_file)
    s3_trigger(name_of_bucket, function_name)


if __name__ == '__main__':
    main('lambda', 'LabRole',
                    'lambda_handler', './lambda.zip', 'btu-test-lab')