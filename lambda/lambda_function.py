import json
import boto3

def lambda_handler(event, context):
    # TODO add error handling
    response=''
    event= json.loads(event['body'])
    http_method=  event.get('httpMethod', "")

    filters = [
        {
            'Name': 'instance-state-name', 
            'Values': ['running']
        }
    ]

    
    ec2_client = boto3.client('ec2')
    reservations = ec2_client.describe_instances(Filters=filters).get("Reservations")

    RunningInstances = []
    for reservation in reservations:
        for instance in reservation["Instances"]:
                RunningInstances.append(instance["InstanceId"])


    def get_handler():

        return  {
            'statusCode': 200,
            'body': json.dumps(str(RunningInstances))
        }


    def post_handler(event):

        response_code= 200
        
        action= event['body'].get('action',"")


        if action=="":
            response_code= 400
            response_body= 'missing action'

        elif action=="Stop_All_Running_Instances":
           
            ec2_client.stop_instances(InstanceIds=RunningInstances)
            response_body = 'Stopped All Running Instances : ' + ','.join(['%s' % i  for i in RunningInstances])  

        elif action=='start' :
            if event['body'].get('InstanceId'):
                Instanceid= event['headers']['InstanceId']
                ec2_client.start_instances(InstanceIds=[Instanceid])
                response_body ='started instance %s' % Instanceid
            else: 
                response_code= 400
                response_body ='missing InstanceId'

        elif action=='stop' :
            if event['body'].get('InstanceId'):
                Instanceid=event['headers']['InstanceId']
                ec2_client.stop_instances(InstanceIds=[Instanceid])
                response_body ='stopped_instance %s' % Instanceid
            else: 
                response_code= 400
                response_body ='missing InstanceId'

        else:
            response_code= 400
            response_body= 'Unsupported action. Action supported:[start, stop, Stop_All_Running_Instances]'
        
        return {
            'statusCode': response_code,
            'body': json.dumps(str(response_body))
        }



    if http_method=='GET':
        response= get_handler()

    elif http_method=='POST':
        response= post_handler(event)

    else: # unsupported http method
        response= { 'statusCode': 405 ,
        'body': json.dumps(str('HTTP method not supported'))} 

    
    return response