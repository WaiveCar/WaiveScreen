import boto3, botocore
import os
S3_BUCKET = "daleighan.com"
S3_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET = os.environ.get("S3_SECRET_ACCESS_KEY")
S3_LOCATION = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)

s3 = boto3.client(
   "s3",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET
)

def upload_s3(file, acl="public-read"):
    try: 
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            file.filename,
            ExtraArgs={
                "ACL": acl,
            }
        ) 
    except Exception as e:
        print("error: ", e)
        return e
    return "{}{}".format(S3_LOCATION, file.filename)
