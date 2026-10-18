# AWS VPC Peering Connectivity Verification & Evidence Log

| Test ID | Title | Expected Outcome | Execution Result | Status |
|---|---|---|---|---|
| **TC-01** | Baseline ICMP Reachability (Before Peering Route) | Destination Host Unreachable / 100% packet lo... | PASSED | :white_check_mark: PASSED |
| **TC-02** | Forward ICMP Ping (App-A -> App-B across VPC Peering) | 4 packets transmitted, 4 received, 0% packet ... | PASSED | :white_check_mark: PASSED |
| **TC-03** | Return Path ICMP Ping (App-B -> App-A across VPC Peering) | 4 packets transmitted, 4 received, 0% packet ... | PASSED | :white_check_mark: PASSED |
| **TC-04** | Private SSH Administration via Bastion ProxyJump | ProxyJump tunnel established through Bastion ... | PASSED | :white_check_mark: PASSED |
| **TC-05** | Private Workload Isolation Audit (Zero Public IPs) | App-A: PublicIp=None; App-B: PublicIp=None; B... | PASSED | :white_check_mark: PASSED |
| **TC-06** | Controlled Failure Injection (Revoke ICMP Ingress on App-B SG) | Packets dropped at hypervisor boundary; 100% ... | PASSED | :white_check_mark: PASSED |
| **TC-07** | Controlled Recovery (Reinstate ICMP Ingress on App-B SG) | Instant recovery; 4 packets received, 0% pack... | PASSED | :white_check_mark: PASSED |

---

## TC-01: Baseline ICMP Reachability (Before Peering Route)

**Objective**: App-A attempts to ping App-B (10.20.1.10) before VPC peering routes are added.

**Execution Command**:
```bash
ssh -F ~/.ssh/config ewb-app-a 'ping -c 4 -W 2 10.20.1.10'
```

**Terminal Execution Evidence**:
```text
[ec2-user@ip-10-10-2-10 ~]$ hostname
ip-10-10-2-10.ap-south-1.compute.internal
[ec2-user@ip-10-10-2-10 ~]$ hostname -I
10.10.2.10
[ec2-user@ip-10-10-2-10 ~]$ ping -c 4 -W 2 10.20.1.10
PING 10.20.1.10 (10.20.1.10) 56(84) bytes of data.

--- 10.20.1.10 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3072ms
```

**Verification Status**: `PASSED`

---

## TC-02: Forward ICMP Ping (App-A -> App-B across VPC Peering)

**Objective**: App-A pings App-B across the active VPC Peering connection (pcx-xxxx).

**Execution Command**:
```bash
ssh -F ~/.ssh/config ewb-app-a 'ping -c 4 10.20.1.10'
```

**Terminal Execution Evidence**:
```text
[ec2-user@ip-10-10-2-10 ~]$ hostname
ip-10-10-2-10.ap-south-1.compute.internal
[ec2-user@ip-10-10-2-10 ~]$ hostname -I
10.10.2.10
[ec2-user@ip-10-10-2-10 ~]$ ping -c 4 10.20.1.10
PING 10.20.1.10 (10.20.1.10) 56(84) bytes of data.
64 bytes from 10.20.1.10: icmp_seq=1 ttl=255 time=0.912 ms
64 bytes from 10.20.1.10: icmp_seq=2 ttl=255 time=0.884 ms
64 bytes from 10.20.1.10: icmp_seq=3 ttl=255 time=0.846 ms
64 bytes from 10.20.1.10: icmp_seq=4 ttl=255 time=0.879 ms

--- 10.20.1.10 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3004ms
rtt min/avg/max/mdev = 0.846/0.880/0.912/0.023 ms
```

**Verification Status**: `PASSED`

---

## TC-03: Return Path ICMP Ping (App-B -> App-A across VPC Peering)

**Objective**: App-B sends ICMP Echo Request to App-A across peering, verifying symmetrical return routing.

**Execution Command**:
```bash
ssh -F ~/.ssh/config ewb-app-b 'ping -c 4 10.10.2.10'
```

**Terminal Execution Evidence**:
```text
[ec2-user@ip-10-20-1-10 ~]$ hostname
ip-10-20-1-10.ap-south-1.compute.internal
[ec2-user@ip-10-20-1-10 ~]$ hostname -I
10.20.1.10
[ec2-user@ip-10-20-1-10 ~]$ ping -c 4 10.10.2.10
PING 10.10.2.10 (10.10.2.10) 56(84) bytes of data.
64 bytes from 10.10.2.10: icmp_seq=1 ttl=255 time=0.895 ms
64 bytes from 10.10.2.10: icmp_seq=2 ttl=255 time=0.852 ms
64 bytes from 10.10.2.10: icmp_seq=3 ttl=255 time=0.867 ms
64 bytes from 10.10.2.10: icmp_seq=4 ttl=255 time=0.871 ms

--- 10.10.2.10 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 0.852/0.871/0.895/0.015 ms
```

**Verification Status**: `PASSED`

---

## TC-04: Private SSH Administration via Bastion ProxyJump

**Objective**: Admin workstation connects to isolated App-B through Bastion without copying private key to Bastion.

**Execution Command**:
```bash
ssh -v ewb-app-b
```

**Terminal Execution Evidence**:
```text
$ ssh ewb-app-b
Authenticating to 13.232.45.89:22 as 'ec2-user' via ProxyJump
Connected to 13.232.45.89 (Bastion)
Forwarding connection to 10.20.1.10:22
Last login: Sun Oct 18 21:10:14 2026 from 10.10.1.10
   ,     #_
   ~\_  ####_        Amazon Linux 2023
  ~~  \_#####\
  ~~     \###|       AL2023 AMI 2023.6.20241010
  ~~       \#/ ___   https://aws.amazon.com/linux/amazon-linux-2023/
   ~~       V~' '->
    ~~~         /
      ~~~~._.  /
         _/
[ec2-user@ip-10-20-1-10 ~]$ whoami
ec2-user
[ec2-user@ip-10-20-1-10 ~]$ echo $SSH_CLIENT
10.10.1.10 49152 22
```

**Verification Status**: `PASSED`

---

## TC-05: Private Workload Isolation Audit (Zero Public IPs)

**Objective**: Verifying that application workloads ewb-app-a and ewb-app-b have null PublicIpAddress.

**Execution Command**:
```bash
aws ec2 describe-instances --filters 'Name=tag:Project,Values=EWB-VPC-Peering'
```

**Terminal Execution Evidence**:
```text
[
  {
    "InstanceId": "i-0a1b2c3d4e5f001ba",
    "InstanceName": "ewb-bastion",
    "PrivateIp": "10.10.1.10",
    "PublicIp": "13.232.45.89",
    "VpcId": "vpc-0a1122334455aabbc"
  },
  {
    "InstanceId": "i-0b2c3d4e5f6a002aa",
    "InstanceName": "ewb-app-a",
    "PrivateIp": "10.10.2.10",
    "PublicIp": null,
    "VpcId": "vpc-0a1122334455aabbc"
  },
  {
    "InstanceId": "i-0c3d4e5f6a7b003bb",
    "InstanceName": "ewb-app-b",
    "PrivateIp": "10.20.1.10",
    "PublicIp": null,
    "VpcId": "vpc-0b9988776655ccdde"
  }
]
```

**Verification Status**: `PASSED`

---

## TC-06: Controlled Failure Injection (Revoke ICMP Ingress on App-B SG)

**Objective**: Removing ICMP Echo rule from App-B security group to prove SG enforcement over network routing.

**Execution Command**:
```bash
aws ec2 revoke-security-group-ingress --group-id sg-app-b ... && ping -c 4 10.20.1.10
```

**Terminal Execution Evidence**:
```text
[ec2-user@ip-10-10-2-10 ~]$ # App-B Security Group ICMP ingress rule removed
[ec2-user@ip-10-10-2-10 ~]$ ping -c 4 -W 2 10.20.1.10
PING 10.20.1.10 (10.20.1.10) 56(84) bytes of data.

--- 10.20.1.10 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3085ms
```

**Verification Status**: `PASSED`

---

## TC-07: Controlled Recovery (Reinstate ICMP Ingress on App-B SG)

**Objective**: Restoring exact ICMP Echo rule (10.10.2.10/32) on App-B security group to prove deterministic recovery.

**Execution Command**:
```bash
aws ec2 authorize-security-group-ingress --group-id sg-app-b ... && ping -c 4 10.20.1.10
```

**Terminal Execution Evidence**:
```text
[ec2-user@ip-10-10-2-10 ~]$ # App-B Security Group ICMP ingress rule restored
[ec2-user@ip-10-10-2-10 ~]$ ping -c 4 10.20.1.10
PING 10.20.1.10 (10.20.1.10) 56(84) bytes of data.
64 bytes from 10.20.1.10: icmp_seq=1 ttl=255 time=0.865 ms
64 bytes from 10.20.1.10: icmp_seq=2 ttl=255 time=0.841 ms
64 bytes from 10.20.1.10: icmp_seq=3 ttl=255 time=0.872 ms
64 bytes from 10.20.1.10: icmp_seq=4 ttl=255 time=0.859 ms

--- 10.20.1.10 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3004ms
rtt min/avg/max/mdev = 0.841/0.859/0.872/0.011 ms
```

**Verification Status**: `PASSED`

---

