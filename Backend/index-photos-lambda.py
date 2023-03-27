import json
import boto3
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
import inflect

ALLOWED_EXTENSIONS = ['.jpg', '.png']
CUSTOM_LABELS_TAG = 'customlabels'


def get_labels(s3_bucket, s3_key):
    
    rekognition = boto3.client('rekognition')
    response = rekognition.detect_labels(
        Image={
            'S3Object': {
                'Bucket': s3_bucket,
                'Name': s3_key,
            },
        },
    )

    labels = [label['Name'] for label in response['Labels']]
    return labels
    
def get_custom_labels(s3_bucket, s3_key):
    """
    Gets custom labels from S3 image
    """
    
    s3 = boto3.client('s3')
    response = s3.head_object(Bucket=s3_bucket, Key=s3_key)
    print("ding\n\n\n")
    print(response)
    if CUSTOM_LABELS_TAG in response['Metadata']:
        custom_labels = response['Metadata'][CUSTOM_LABELS_TAG]
        labels_array = custom_labels.split(',')
        
    else:
        labels_array = []
        print("No custom labels found in the object metadata.")
    return labels_array
    

def create_opensearch_client():
    host = 'https://search-photos-i2pm6nlhd5qlkcigtklk7qchk4.us-east-1.es.amazonaws.com'
    port = 443
    auth = ('admin', 'Admin1230!')

    client = OpenSearch(
        hosts = [host],
        http_auth = auth,
        use_ssl = True,
        verify_certs = True,
        ssl_assert_hostname = False,
        ssl_show_warn = False,
        connection_class = RequestsHttpConnection
    )
    return client

def insert_into_opensearch(s3_bucket, s3_key, all_labels):
    client = create_opensearch_client()
    json_object = {
        "objectKey": s3_key,
        "bucket": s3_bucket,
        "createdTimestamp": datetime.now().isoformat(),
        "labels": all_labels
    }
    response = client.index(
            index = 'photos',
            body = json_object,
            refresh = True
        )
    print("Successfully inserted into OpenSearch ", response)
    
    

def lambda_handler(event, context):
    
    print(event)
    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_key = event['Records'][0]['s3']['object']['key']
    
    # s3_bucket = 'gb2642-images-for-tag'
    # s3_key = 'pre-tag/Honeycrisp-Apple.jpg'
    
    if list(filter(s3_key.endswith, ALLOWED_EXTENSIONS)) == []:
        error = 'We accept only .jpg or .png' + s3_key
        print(error)
        return {'statusCode': 400,'body': json.dumps(error)}
    
    # Rekognition
    labels = []
    labels = get_labels(s3_bucket, s3_key)
    print(s3_bucket, s3_key)
    print(f'Labels detected: {", ".join(labels)}')
    
    
    # S3 related:
    custom_labels = get_custom_labels(s3_bucket, s3_key)
    print(f'Custom Labels detected: {", ".join(custom_labels)}')
        
    # Open Search
    p = inflect.engine()
    all_labels = []
    for each_label in custom_labels + labels:
        singular = p.singular_noun(each_label)
        print(type(singular), singular)
        if p.singular_noun(each_label):
            each_label = p.singular_noun(each_label)
        all_labels.append(each_label.lower())
    print(all_labels)
    
    insert_into_opensearch(s3_bucket, s3_key, all_labels)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
