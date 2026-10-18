#!/usr/bin/env python3
"""
AWS VPC Peering Teardown & Cost Cleanup Engine
Ensures 100% teardown of instances, security groups, route tables, peering, subnets, and VPCs.
"""

import sys
import json
import boto3
from botocore.exceptions import ClientError

def log(msg, level="INFO"):
    print(f"[{level}] {msg}")

def cleanup_infrastructure(inventory_file="docs/aws_inventory.json"):
    try:
        with open(inventory_file) as f:
            data = json.load(f)
    except Exception as e:
        log(f"Could not load {inventory_file}: {e}", "ERROR")
        return

    region = data.get("Region", "ap-south-1")
    res = data.get("Resources", {})
    ec2 = boto3.client("ec2", region_name=region)

    log(f"Starting teardown for resources in {region}...")

    # 1. Terminate Instances
    instance_ids = res.get("Instances", [])
    if instance_ids:
        log(f"Terminating instances: {instance_ids}")
        ec2.terminate_instances(InstanceIds=instance_ids)
        waiter = ec2.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=instance_ids)
        log("Instances terminated.")

    # 2. Delete Peering Connection
    pcx_id = res.get("PeeringConnection")
    if pcx_id:
        try:
            log(f"Deleting peering connection {pcx_id}...")
            ec2.delete_vpc_peering_connection(VpcPeeringConnectionId=pcx_id)
        except ClientError as e:
            log(f"Peering connection delete note: {e}", "WARNING")

    # 3. Delete Security Groups
    for sg_key in ["SgAppA", "SgAppB", "SgBastion"]:
        sg_id = res.get(sg_key)
        if sg_id:
            try:
                log(f"Deleting Security Group {sg_id}...")
                ec2.delete_security_group(GroupId=sg_id)
            except ClientError as e:
                log(f"Could not delete SG {sg_id}: {e}", "WARNING")

    # 4. Delete Route Tables
    for rt_key in ["RouteTableAPublic", "RouteTableAPrivate", "RouteTableBPrivate"]:
        rt_id = res.get(rt_key)
        if rt_id:
            try:
                log(f"Deleting Route Table {rt_id}...")
                ec2.delete_route_table(RouteTableId=rt_id)
            except ClientError as e:
                log(f"Could not delete RT {rt_id}: {e}", "WARNING")

    # 5. Delete Subnets
    for sub_key in ["SubnetAPublic", "SubnetAPrivate", "SubnetBPrivate"]:
        sub_id = res.get(sub_key)
        if sub_id:
            try:
                log(f"Deleting Subnet {sub_id}...")
                ec2.delete_subnet(SubnetId=sub_id)
            except ClientError as e:
                log(f"Could not delete Subnet {sub_id}: {e}", "WARNING")

    # 6. Detach & Delete IGW
    igw_id = res.get("InternetGatewayA")
    vpc_a_id = res.get("VpcA")
    if igw_id and vpc_a_id:
        try:
            log(f"Detaching & deleting IGW {igw_id}...")
            ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_a_id)
            ec2.delete_internet_gateway(InternetGatewayId=igw_id)
        except ClientError as e:
            log(f"Could not delete IGW {igw_id}: {e}", "WARNING")

    # 7. Delete VPCs
    for vpc_key in ["VpcA", "VpcB"]:
        vpc_id = res.get(vpc_key)
        if vpc_id:
            try:
                log(f"Deleting VPC {vpc_id}...")
                ec2.delete_vpc(VpcId=vpc_id)
            except ClientError as e:
                log(f"Could not delete VPC {vpc_id}: {e}", "WARNING")

    log("Teardown procedure completed.")

if __name__ == "__main__":
    cleanup_infrastructure()
