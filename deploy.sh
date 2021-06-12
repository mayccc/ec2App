# docker build . -t mayccc/insurance-quote

# docker push mayccc/insurance-quote

# check if instance exists 
instance_id=`aws ec2 describe-instances \
    --filters "Name=instance-state-name,Values=running" "Name=tag-value,Values=ec2app" --query 'Reservations[*].Instances[*].{Instance:InstanceId}' --output text`

echo $instance_id
if [ -z "$instance_id" ]
then 

	echo "instance does not exist"
else 
	echo "instance exists, terminate $instance_id"
	aws ec2 terminate-instances --instance-ids $instance_id

fi

echo "create instance $instance_id"
instance_id=$(aws ec2 run-instances --image-id ami-0186908e2fdeea8f3 --instance-type t2.micro --region ap-southeast-2   \
--key-name ec2_id_rsa  --user-data file://ud.txt --count 1 --tag-specifications 'ResourceType=instance,Tags=[{Key=task,Value=ec2app}]' 'ResourceType=volume,Tags=[{Key=task,Value=ec2app}]'  --output text  --query 'Instances[*].InstanceId') 

echo "get elastic ip from paramter store"


# check if ip exists in parameter store
ip=$(aws ssm get-parameters --names public-ip --query "Parameters[*].{Value:Value}" --output text)


if [ -z "$ip" ]
then 
	# allocate elastic ip 
	ip=$( aws ec2 allocate-address --tag-specifications 'ResourceType=elastic-ip ,Tags=[{Key=task,Value=ec2app}]' --output text  --query 'PublicIp' )
	# save to parameter store 
	aws ssm put-parameter --name "public-ip" --value $ip --type String --tags "Key=task,Value=ec2app"
# associate ip 
fi 

while STATE=$(aws ec2 describe-instances --instance-ids $instance_id --output text --query 'Reservations[*].Instances[*].State.Name'); test "$STATE" != "running"; do
    sleep 5;
done;

echo "associate ip to instance"
aws ec2 associate-address --instance-id $instance_id --public-ip $ip 


echo "ip $ip"

security_group=$( aws ec2 describe-security-groups --filters Name=group-name,Values=ec2appSecurityGroup --query "SecurityGroups[*].{ID:GroupId}" --output text)

if [ -z "$ip" ]
then 
	security_group=$(aws ec2 create-security-group --group-name ec2appSecurityGroup --description "ec2appSecurityGroup"  --output text  ) 
	myIp=`curl -s checkip.dyndns.org | sed -e 's/.*Current IP Address: //' -e 's/<.*$//'`

    aws ec2 authorize-security-group-ingress --group-name "ec2appSecurityGroup" --protocol tcp --port 3000   --cidr $myIp/32 

fi 


aws ec2 modify-instance-attribute --instance-id $instance_id --groups $security_group



