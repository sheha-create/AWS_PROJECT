# Technical Requirements Document (TRD)

**Project Title**: AWS VPC Peering: Connect Two VPCs and Prove Private Connectivity  
**Course / Track**: EWB Cloud Labs — Cloud Networking Internship  
**Version**: 1.0 · Technical Implementation Specification  
**Status**: Verified & Implemented  

---

## 1. Network Topology & System Architecture

The system deploys a direct, non-transitive VPC Peering architecture between two non-overlapping VPC networks in the AWS Cloud.

```text
[ Admin Workstation ]
        │  SSH (TCP:22) via ProxyJump
        ▼
[ VPC A: 10.10.0.0/16 ]
   ├── Internet Gateway (ewb-igw-a)
   ├── ewb-a-public (10.10.1.0/24)
   │     └── ewb-bastion (10.10.1.10) [Public IP: 13.232.45.89]
   └── ewb-a-private (10.10.2.0/24)
         └── ewb-app-a (10.10.2.10)   [Public IP: None]
                    │
            ┌───────┴────────────────────────┐
            │  VPC Peering (ewb-a-b-peer)     │
            │  pcx-0a44b55c66d77e88f (Active)│
            └───────┬────────────────────────┘
                    │
[ VPC B: 10.20.0.0/16 ]  (Zero Internet Gateway)
   └── ewb-b-private (10.20.1.0/24)
         └── ewb-app-b (10.20.1.10)   [Public IP: None]
```

---

## 2. IP Addressing Plan & Resource Inventory

| Resource Name | Logical Resource Type | CIDR / IP Assignment | Route Table Association | Attached Security Group |
|---|---|---|---|---|
| `ewb-vpc-a` | AWS VPC | `10.10.0.0/16` | Default | - |
| `ewb-vpc-b` | AWS VPC | `10.20.0.0/16` | Default | - |
| `ewb-igw-a` | Internet Gateway | Attaches to `ewb-vpc-a` | - | - |
| `ewb-a-public` | Public Subnet | `10.10.1.0/24` | `ewb-rt-a-public` | - |
| `ewb-a-private`| Private Subnet A | `10.10.2.0/24` | `ewb-rt-a-private`| - |
| `ewb-b-private`| Private Subnet B | `10.20.1.0/24` | `ewb-rt-b-private`| - |
| `ewb-bastion`  | EC2 (t2.micro / AL2023) | `10.10.1.10` (+ Elastic/Public IP) | In `ewb-a-public` | `ewb-sg-bastion` |
| `ewb-app-a`    | EC2 (t2.micro / AL2023) | `10.10.2.10` (No Public IP) | In `ewb-a-private` | `ewb-sg-app-a` |
| `ewb-app-b`    | EC2 (t2.micro / AL2023) | `10.20.1.10` (No Public IP) | In `ewb-b-private` | `ewb-sg-app-b` |
| `ewb-a-b-peer` | VPC Peering Connection | Cross-VPC `vpc-a` ↔ `vpc-b` | Target: `pcx-xxxx` | - |

---

## 3. Detailed Routing Specification

Three distinct custom route tables govern traffic flow:

### Route Table 1: `ewb-rt-a-public` (VPC A Public Subnet)
- **Subnet Association**: `ewb-a-public` (`10.10.1.0/24`)
- **Entries**:
  - `10.10.0.0/16` → `local` (VPC A internal communication)
  - `0.0.0.0/0` → `ewb-igw-a` (Outbound internet egress for Bastion)
  - `10.20.0.0/16` → `pcx-xxxx` (Enables Bastion to administer App-B directly across peering)

### Route Table 2: `ewb-rt-a-private` (VPC A Private Subnet)
- **Subnet Association**: `ewb-a-private` (`10.10.2.0/24`)
- **Entries**:
  - `10.10.0.0/16` → `local` (VPC A internal communication)
  - `10.20.0.0/16` → `pcx-xxxx` (Forward path from App-A to App-B across peering)
  *(Notice: No default 0.0.0.0/0 route exists, guaranteeing isolation from the public internet).*

### Route Table 3: `ewb-rt-b-private` (VPC B Private Subnet)
- **Subnet Association**: `ewb-b-private` (`10.20.1.0/24`)
- **Entries**:
  - `10.20.0.0/16` → `local` (VPC B internal communication)
  - `10.10.0.0/16` → `pcx-xxxx` (Critical return path from App-B back to VPC A)
  *(Notice: VPC B contains zero internet gateways; all ingress/egress is strictly intra-peering).*

---

## 4. Security Group Configuration Matrix

All security groups implement the principle of least privilege:

```text
+--------------------+--------------+-----------------+------------------------------------------+
| Security Group     | Protocol/Port| Source CIDR     | Functional Purpose                       |
+--------------------+--------------+-----------------+------------------------------------------+
| ewb-sg-bastion     | TCP 22       | Admin IP /32    | Inbound SSH management only from admin   |
| ewb-sg-bastion     | All Outbound | 0.0.0.0/0       | Stateful return and package lookups      |
+--------------------+--------------+-----------------+------------------------------------------+
| ewb-sg-app-a       | TCP 22       | 10.10.1.10/32   | Inbound SSH strictly from Bastion host   |
| ewb-sg-app-a       | ICMP Echo(8) | 10.20.1.10/32   | ICMP Ping response strictly from App-B   |
| ewb-sg-app-a       | All Outbound | 0.0.0.0/0       | Stateful egress across local & peering   |
+--------------------+--------------+-----------------+------------------------------------------+
| ewb-sg-app-b       | TCP 22       | 10.10.1.10/32   | Inbound SSH strictly from Bastion host   |
| ewb-sg-app-b       | ICMP Echo(8) | 10.10.2.10/32   | ICMP Ping response strictly from App-A   |
| ewb-sg-app-b       | All Outbound | 0.0.0.0/0       | Stateful egress across peering           |
+--------------------+--------------+-----------------+------------------------------------------+
```

---

## 5. Bastion Host & SSH ProxyJump Design

Rather than copying sensitive private keys (`.pem`) to the intermediate bastion server (which exposes keys if the bastion is compromised), OpenSSH **`ProxyJump`** is configured on the local admin machine.

### `~/.ssh/config` Architecture
```ssh-config
Host ewb-bastion
    HostName 13.232.45.89
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes

Host ewb-app-a
    HostName 10.10.2.10
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    ProxyJump ewb-bastion

Host ewb-app-b
    HostName 10.20.1.10
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    ProxyJump ewb-bastion
```

### Security Benefits:
1. Private key remains solely on the administrator's local machine (`chmod 400`).
2. Bastion acts strictly as an encrypted L4 TCP forwarding proxy.
3. If the bastion is probed or compromised, the adversary obtains zero private credentials for `ewb-app-a` or `ewb-app-b`.
