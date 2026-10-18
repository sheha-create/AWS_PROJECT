# Technical Troubleshooting & Viva Examination Defense Guide

## 1. Deep-Dive Troubleshooting Playbook

### Scenario A: Bastion SSH Connection Times Out (`Connection timed out`)
- **Root Cause 1**: The administrator's ISP public IPv4 address has changed (DHCP dynamic IP rotation).
  - *Fix*: Check current IP using `curl https://checkip.amazonaws.com` and update the `ewb-sg-bastion` inbound rule to `YOUR_NEW_IP/32`.
- **Root Cause 2**: VPC A Public Subnet route table is missing the `0.0.0.0/0 -> igw-xxxx` default route, or the IGW is detached.
  - *Fix*: Verify route table association for `ewb-a-public` and ensure Internet Gateway state is `Attached`.

### Scenario B: `Permission denied (publickey)` when connecting to App-A or App-B
- **Diagnostic Insight**: Network routing and security groups are working properly because the SSH handshake reached the target server. The issue is purely cryptographic authentication.
- **Root Cause**: Wrong user specified (e.g. using `ubuntu` instead of `ec2-user`), or private key file permissions are too open.
  - *Fix*: Ensure user is `ec2-user` and key has strict permissions: `chmod 400 ~/.ssh/ewb-lab.pem`.

### Scenario C: Ping Times Out Between App-A and App-B After Peering Connection is Active
- **Diagnostic Step 1**: Check VPC Peering status — must be `Active` (not `Pending-acceptance`).
- **Diagnostic Step 2**: Check Route Tables. Even with peering active, AWS does NOT automatically populate routing entries. Both `ewb-rt-a-private` and `ewb-rt-b-private` must have reciprocal entries pointing to `pcx-xxxx`.
- **Diagnostic Step 3**: Check Security Group Ingress. AWS Security Groups are stateful, but inbound rules must explicitly permit ICMP Echo Request (Type 8, Code 0) from the opposing instance's `/32` IP.

### Scenario D: `yum install` / `dnf install` fails on App-B
- **Design Fact**: VPC B has no Internet Gateway and no NAT Gateway. This is intentional per the security design. Lack of external internet egress does not indicate broken VPC peering.

---

## 2. Viva Examination Questions & High-Scoring Technical Answers

### Q1: What is AWS VPC Peering and at what layer does it operate?
**Answer**: VPC Peering is a direct network connection between two VPCs that routes traffic privately using AWS internal backbone infrastructure. It operates at Layer 3 (Network Layer) using private IPv4/IPv6 addresses. It has no single point of failure or bandwidth bottleneck, as it does not rely on a physical appliance or gateway.

### Q2: Why is it mathematically impossible to peer two VPCs with overlapping CIDRs?
**Answer**: IP routing requires unambiguous destination addressing. If VPC A (`10.0.0.0/16`) and VPC B (`10.0.0.0/16`) were peered, routers could not determine whether an IP like `10.0.1.15` belongs to the local VPC or the peer VPC. AWS prevents creation of peering connections with identical or overlapping CIDR blocks to eliminate routing loops and blackholes.

### Q3: Why are return routes strictly required in both VPC route tables?
**Answer**: Packet transmission is bidirectional. Even if App-A's route table sends a packet to VPC B, when App-B generates an ICMP Echo Reply or TCP ACK, its local operating system looks up the destination (`10.10.2.10`) in VPC B's route table. If VPC B lacks an entry for `10.10.0.0/16 -> pcx-xxxx`, the packet is dropped, resulting in a 100% timeout.

### Q4: Does VPC Peering support Transitive Routing?
**Answer**: **No.** VPC Peering is strictly non-transitive. If VPC A is peered with VPC B, and VPC B is peered with VPC C, VPC A cannot communicate with VPC C through VPC B. To achieve transitive routing across multiple VPCs, an **AWS Transit Gateway** must be implemented.

### Q5: Can VPC B access the public internet through VPC A's Internet Gateway via VPC Peering (Edge Routing)?
**Answer**: No. VPC Peering does not support edge routing to an Internet Gateway or Direct Connect gateway attached to a peered VPC.

### Q6: Why perform a controlled failure test (TC-06 & TC-07) in addition to positive tests?
**Answer**: Positive tests alone (showing a green ping) only prove reachability exists, but do not prove which security control is governing that reachability. By revoking the specific ICMP rule and observing immediate packet loss, followed by immediate recovery upon reinstatement, we empirically demonstrate that the hypervisor-level stateful firewall is enforcing access control.
