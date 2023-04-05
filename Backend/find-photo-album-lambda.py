import json
import boto3
import inflect
from opensearchpy import OpenSearch, RequestsHttpConnection

def get_parsed_data(query):
    client = boto3.client('lexv2-runtime')
    bot_name = 'Photo-search-bot'
    bot_alias = 'TestBotAlias'
    user_id = 'admin'
    input_text = query
    response = client.recognize_text(
        botId='KC165FERXS',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId="test_session",
        text=query)
    print(response['messages'][0]['content'])
    
    # response = client.post_text(
    #     botName=bot_name,
    #     botAlias=bot_alias,
    #     userId=user_id,
    #     inputText=input_text
    # )
    # New Line
    # One more new line
    parsed_data = response['messages'][0]['content']
    return parsed_data

def create_client():
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
    
def query_elastic_search(query_list, client):
    result = []
    index_name = "photos"
    for each_query in query_list:
        resp = client.search(
            index=index_name,
            size=5,
            
            body = {
                "query": {
                    "term": {
                        "labels": {"value": each_query.lower()}
                    }
                }
            }
        )
        result.extend(resp['hits']['hits'])
    return result
    
def get_pictures(query):
    query_list = query.split(",")
    
    # Query open search and get data
    client = create_client()
    data = query_elastic_search(query_list, client)
    print("Data", data)
    return data

def format_result(pic_dict):
    print(pic_dict)
    result = []
    for each_pic in pic_dict:
        # https://gb2642-images-for-tag.s3.amazonaws.com/pre-tag/Banana-Single.jpg
        pic_url = 'https://' + each_pic['_source']['bucket'] + '.s3.amazonaws.com/' + each_pic['_source']['objectKey']
        result.append(pic_url)
    result = list(set(result))
    data = {
        'status': 'Valid',
        'pictures': result
    }
    return data
    
def lambda_handler(event, context):
    # TODO implement
    print(event)
    query = event['q']
    parsed_data = get_parsed_data(query)
    print("Parsed Input: ", parsed_data)
    if parsed_data == "Invalid":
        return_dict = {
            "status": "Invalid",
            "message": "Oops, cannot process this request"
        }
    else:
        pic_dict = get_pictures(parsed_data)
        return_dict = format_result(pic_dict)

    return {
        'statusCode': 200,
        'body': json.dumps(return_dict)
    }
