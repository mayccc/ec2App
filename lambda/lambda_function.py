import json
import boto3


def lambda_handler(event, context):
    # TODO add error handling
   
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

    def response(code, body ):
        return {
            'statusCode': code,
            'body': json.dumps(str(body))
        }


    def get_handler():

        return  response(200, RunningInstances)

    def post_handler(event):
        
        body= json.loads(event['body'])
        action= body.get('action',"")

        if action=="":
            result= response(400, 'missing action')

        elif action=="Stop_All_Running_Instances":
            if len(RunningInstances)> 0:
                ec2_client.stop_instances(InstanceIds=RunningInstances)

            result= response(200, 'Stopped All Running Instances : ' + ','.join(['%s' % i  for i in RunningInstances]) )
        
        elif action=='start' :
            if body.get('InstanceId'):
                Instanceid= body['InstanceId']
                ec2_client.start_instances(InstanceIds=[Instanceid])
                result= response(200, 'started instance %s' % Instanceid) 
            else: 
                result=  response(400,'missing InstanceId')

        elif action=='stop' :
            if body.get('InstanceId'):
                Instanceid=body['InstanceId']
                ec2_client.stop_instances(InstanceIds=[Instanceid])
                result= response(200, 'stopped instance %s' % Instanceid) 
            else: 
                result= response(400, 'missing InstanceId') 

        else:
            result= response(400, 'Unsupported action. Action supported:[start, stop, Stop_All_Running_Instances]') 
        
        return result 

    if http_method=='GET':
        result = get_handler()

    elif http_method=='POST':
        result = post_handler(event)

    else: # unsupported http method
        result = response (405 ,'HTTP method not supported') 

    
    return result 