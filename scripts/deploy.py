#!/usr/bin/env python3
"""
AWS VPC Peering Deployer & Lifecycle Automation Engine
Automates creation, verification, and cleanup of the 2-VPC peering infrastructure
via AWS Boto3 SDK according to the EWB Cloud Labs specification.
"""

import sys
import time
import argparse
import json
import boto3
from botocore.exceptions import ClientError

DEFAULT_REGION = "ap-south-1"
STUDENT_NAME = "Intern"

def log(msg, level="INFO"):
    print(f"[{level}] {msg}")

def deploy_infrastructure(region_name=DEFAULT_REGION, student_name=STUDENT_NAME, key_name="ewb-lab"):
    ec2_client = boto3.client("ec2", region_name=region_name)
    ec2_resource = boto3.resource("ec2", region_name=region_name)
    inventory = {"Region": region_name, "Resources": {}}

    log(f"Initiating deployment in region {region_name} for student {student_name}...")

    # 1. VPC A (10.10.0.0/16)
    log("Creating VPC A (10.10.0.0/16)...")
    res_vpc_a = ec2_client.create_vpc(
        CidrBlock="10.10.0.0/16",
        TagSpecifications=[{"ResourceType": "vpc", "Tags": [
            {"Key": "Name", "Value": "ewb-vpc-a"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )
    vpc_a_id = res_vpc_a["Vpc"]["VpcId"]
    inventory["Resources"]["VpcA"] = vpc_a_id
    ec2_client.modify_vpc_attribute(VpcId=vpc_a_id, EnableDnsHostnames={"Value": True})
    ec2_client.modify_vpc_attribute(VpcId=vpc_a_id, EnableDnsSupport={"Value": True})
    log(f"VPC A created: {vpc_a_id}")

    # 2. VPC B (10.20.0.0/16)
    log("Creating VPC B (10.20.0.0/16)...")
    res_vpc_b = ec2_client.create_vpc(
        CidrBlock="10.20.0.0/16",
        TagSpecifications=[{"ResourceType": "vpc", "Tags": [
            {"Key": "Name", "Value": "ewb-vpc-b"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )
    vpc_b_id = res_vpc_b["Vpc"]["VpcId"]
    inventory["Resources"]["VpcB"] = vpc_b_id
    ec2_client.modify_vpc_attribute(VpcId=vpc_b_id, EnableDnsHostnames={"Value": True})
    ec2_client.modify_vpc_attribute(VpcId=vpc_b_id, EnableDnsSupport={"Value": True})
    log(f"VPC B created: {vpc_b_id}")

    # 3. Internet Gateway for VPC A
    log("Creating Internet Gateway for VPC A...")
    res_igw = ec2_client.create_internet_gateway(
        TagSpecifications=[{"ResourceType": "internet-gateway", "Tags": [
            {"Key": "Name", "Value": "ewb-igw-a"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )
    igw_id = res_igw["InternetGateway"]["InternetGatewayId"]
    inventory["Resources"]["InternetGatewayA"] = igw_id
    ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_a_id)
    log(f"Attached IGW {igw_id} to VPC A")

    # 4. Subnets
    # Subnet A Public (10.10.1.0/24)
    log("Creating ewb-a-public (10.10.1.0/24)...")
    res_sub_a_pub = ec2_client.create_subnet(
        VpcId=vpc_a_id,
        CidrBlock="10.10.1.0/24",
        TagSpecifications=[{"ResourceType": "subnet", "Tags": [
            {"Key": "Name", "Value": "ewb-a-public"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )
    sub_a_pub_id = res_sub_a_pub["Subnet"]["SubnetId"]
    inventory["Resources"]["SubnetAPublic"] = sub_a_pub_id
    ec2_client.modify_subnet_attribute(SubnetId=sub_a_pub_id, MapPublicIpOnLaunch={"Value": True})

    # Subnet A Private (10.10.2.0/24)
    log("Creating ewb-a-private (10.10.2.0/24)...")
    res_sub_a_priv = ec2_client.create_subnet(
        VpcId=vpc_a_id,
        CidrBlock="10.10.2.0/24",
        TagSpecifications=[{"ResourceType": "subnet", "Tags": [
            {"Key": "Name", "Value": "ewb-a-private"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )
    sub_a_priv_id = res_sub_a_priv["Subnet"]["SubnetId"]
    inventory["Resources"]["SubnetAPrivate"] = sub_a_priv_id

    # Subnet B Private (10.20.1.0/24)
    log("Creating ewb-b-private (10.20.1.0/24)...")
    res_sub_b_priv = ec2_client.create_subnet(
        VpcId=vpc_b_id,
        CidrBlock="10.20.1.0/24",
        TagSpecifications=[{"ResourceType": "subnet", "Tags": [
            {"Key": "Name", "Value": "ewb-b-private"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )
    sub_b_priv_id = res_sub_b_priv["Subnet"]["SubnetId"]
    inventory["Resources"]["SubnetBPrivate"] = sub_b_priv_id

    # 5. Peering Connection
    log("Creating VPC Peering Connection ewb-a-b-peer...")
    res_peer = ec2_client.create_vpc_peering_connection(
        VpcId=vpc_a_id,
        PeerVpcId=vpc_b_id,
        TagSpecifications=[{"ResourceType": "vpc-peering-connection", "Tags": [
            {"Key": "Name", "Value": "ewb-a-b-peer"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )
    pcx_id = res_peer["VpcPeeringConnection"]["VpcPeeringConnectionId"]
    inventory["Resources"]["PeeringConnection"] = pcx_id
    log(f"Accepting peering connection {pcx_id}...")
    ec2_client.accept_vpc_peering_connection(VpcPeeringConnectionId=pcx_id)

    # 6. Route Tables
    log("Configuring Route Tables...")
    # RT A Public
    rt_a_pub = ec2_client.create_route_table(
        VpcId=vpc_a_id,
        TagSpecifications=[{"ResourceType": "route-table", "Tags": [
            {"Key": "Name", "Value": "ewb-rt-a-public"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )["RouteTable"]["RouteTableId"]
    inventory["Resources"]["RouteTableAPublic"] = rt_a_pub
    ec2_client.create_route(RouteTableId=rt_a_pub, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)
    ec2_client.create_route(RouteTableId=rt_a_pub, DestinationCidrBlock="10.20.0.0/16", VpcPeeringConnectionId=pcx_id)
    ec2_client.associate_route_table(RouteTableId=rt_a_pub, SubnetId=sub_a_pub_id)

    # RT A Private
    rt_a_priv = ec2_client.create_route_table(
        VpcId=vpc_a_id,
        TagSpecifications=[{"ResourceType": "route-table", "Tags": [
            {"Key": "Name", "Value": "ewb-rt-a-private"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )["RouteTable"]["RouteTableId"]
    inventory["Resources"]["RouteTableAPrivate"] = rt_a_priv
    ec2_client.create_route(RouteTableId=rt_a_priv, DestinationCidrBlock="10.20.0.0/16", VpcPeeringConnectionId=pcx_id)
    ec2_client.associate_route_table(RouteTableId=rt_a_priv, SubnetId=sub_a_priv_id)

    # RT B Private
    rt_b_priv = ec2_client.create_route_table(
        VpcId=vpc_b_id,
        TagSpecifications=[{"ResourceType": "route-table", "Tags": [
            {"Key": "Name", "Value": "ewb-rt-b-private"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"},
            {"Key": "Student", "Value": student_name}
        ]}]
    )["RouteTable"]["RouteTableId"]
    inventory["Resources"]["RouteTableBPrivate"] = rt_b_priv
    ec2_client.create_route(RouteTableId=rt_b_priv, DestinationCidrBlock="10.10.0.0/16", VpcPeeringConnectionId=pcx_id)
    ec2_client.associate_route_table(RouteTableId=rt_b_priv, SubnetId=sub_b_priv_id)

    # 7. Security Groups
    log("Creating Security Groups...")
    # SG Bastion
    sg_bastion = ec2_client.create_security_group(
        GroupName="ewb-sg-bastion",
        Description="Inbound SSH to Bastion from admin IP",
        VpcId=vpc_a_id,
        TagSpecifications=[{"ResourceType": "security-group", "Tags": [
            {"Key": "Name", "Value": "ewb-sg-bastion"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"}
        ]}]
    )["GroupId"]
    inventory["Resources"]["SgBastion"] = sg_bastion
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_bastion,
        IpPermissions=[{
            "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH from Admin"}]
        }]
    )

    # SG App-A
    sg_app_a = ec2_client.create_security_group(
        GroupName="ewb-sg-app-a",
        Description="SSH from Bastion and ICMP from App-B",
        VpcId=vpc_a_id,
        TagSpecifications=[{"ResourceType": "security-group", "Tags": [
            {"Key": "Name", "Value": "ewb-sg-app-a"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"}
        ]}]
    )["GroupId"]
    inventory["Resources"]["SgAppA"] = sg_app_a
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_app_a,
        IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "10.10.1.10/32", "Description": "SSH from Bastion"}]},
            {"IpProtocol": "icmp", "FromPort": 8, "ToPort": 0, "IpRanges": [{"CidrIp": "10.20.1.10/32", "Description": "ICMP Echo from App-B"}]}
        ]
    )

    # SG App-B
    sg_app_b = ec2_client.create_security_group(
        GroupName="ewb-sg-app-b",
        Description="SSH from Bastion and ICMP from App-A",
        VpcId=vpc_b_id,
        TagSpecifications=[{"ResourceType": "security-group", "Tags": [
            {"Key": "Name", "Value": "ewb-sg-app-b"},
            {"Key": "Project", "Value": "EWB-VPC-Peering"}
        ]}]
    )["GroupId"]
    inventory["Resources"]["SgAppB"] = sg_app_b
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_app_b,
        IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "10.10.1.10/32", "Description": "SSH from Bastion"}]},
            {"IpProtocol": "icmp", "FromPort": 8, "ToPort": 0, "IpRanges": [{"CidrIp": "10.10.2.10/32", "Description": "ICMP Echo from App-A"}]}
        ]
    )

    # Save inventory
    with open("docs/aws_inventory.json", "w") as f:
        json.dump(inventory, f, indent=2)

    log("Deployment completed successfully. Saved inventory to docs/aws_inventory.json")
    return inventory

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy AWS VPC Peering Infrastructure")
    parser.add_argument("--region", default=DEFAULT_REGION, help="AWS Region")
    parser.add_argument("--student", default=STUDENT_NAME, help="Student Name")
    args = parser.parse_args()

    try:
        deploy_infrastructure(region_name=args.region, student_name=args.student)
    except ClientError as e:
        log(f"AWS Error: {e}", "ERROR")
        sys.exit(1)
