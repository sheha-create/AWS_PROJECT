# Product Requirements Document (PRD)

**Project Title**: AWS VPC Peering: Connect Two VPCs and Prove Private Connectivity  
**Course / Track**: EWB Cloud Labs — Cloud Networking Internship  
**Version**: 1.0 · Final Submission  
**Author**: Engineering Intern  
**Status**: Verified & Implemented  

---

## 1. Executive Summary & Purpose

The purpose of this project is to implement, test, and document an enterprise-grade private interconnect between two isolated Amazon Web Services (AWS) Virtual Private Clouds (VPCs) using **AWS VPC Peering**. 

In modern cloud architecture, default network boundaries isolate VPCs from each other. If an application workload in one VPC needs to communicate with databases, analytics clusters, or microservices in another VPC, exposing these workloads over the public internet introduces severe security risks and egress bandwidth costs. This project establishes direct, private IPv4 routing between non-overlapping VPC networks while keeping sensitive application workloads strictly air-gapped from the public internet.

---

## 2. Problem Statement

By default, AWS VPCs have zero communication pathways with other VPCs or external networks without explicit gateways or peering connections:
1. Workloads deployed inside **VPC A** (`10.10.0.0/16`) cannot resolve or reach IP addresses inside **VPC B** (`10.20.0.0/16`).
2. Directly assigning public IPv4 addresses to backend application instances violates cloud security baselines (OWASP/CIS AWS Foundations Benchmark).
3. Establishing private connectivity requires careful alignment of non-overlapping CIDRs, bidirectional route table targets, hypervisor-level security groups, and secure jump-host administration.

---

## 3. Goals & Acceptance Criteria

| Requirement ID | Requirement Title | Technical Acceptance Criteria | Status |
|---|---|---|---|
| **PR-01** | Non-Overlapping VPCs | VPC A (`10.10.0.0/16`) and VPC B (`10.20.0.0/16`) created with zero CIDR collision. | :white_check_mark: Complete |
| **PR-02** | Subnet Architecture | Public and Private subnets provisioned with explicit Route Table associations. | :white_check_mark: Complete |
| **PR-03** | Active Peering Connection | AWS VPC Peering connection (`ewb-a-b-peer`) accepted and transitioning to `Active`. | :white_check_mark: Complete |
| **PR-04** | Bidirectional Route Insertion | Explicit route table entries routing cross-VPC traffic to `pcx-xxxx` target. | :white_check_mark: Complete |
| **PR-05** | Principle of Least Privilege | Security groups permit only specific source IPs for SSH (TCP:22) and ICMP Echo. | :white_check_mark: Complete |
| **PR-06** | Zero Public Workload Exposure | Workload instances (`ewb-app-a` & `ewb-app-b`) have `Public IP: None`. | :white_check_mark: Complete |
| **PR-07** | Two-Way Connectivity Validation | Bidirectional ICMP Ping achieves 4/4 replies with 0% packet loss. | :white_check_mark: Complete |
| **PR-08** | Isolation & Failure Injection | Revoking App-B ICMP rule immediately drops traffic (100% loss); restoring recovers link. | :white_check_mark: Complete |
| **PR-09** | Secure Remote Administration | Admin connects to private instances using SSH `ProxyJump` without keys on bastion. | :white_check_mark: Complete |
| **PR-10** | Resource Lifecycle & Cost Control | Full teardown automation script destroys all resources to prevent billing leakage. | :white_check_mark: Complete |

---

## 4. Scope of the Project

### In-Scope
- Deployment of VPC A (`10.10.0.0/16`) with an attached Internet Gateway and 2 subnets (`10.10.1.0/24` public, `10.10.2.0/24` private).
- Deployment of VPC B (`10.20.0.0/16`) with 1 private subnet (`10.20.1.0/24`) and zero internet gateway.
- Launching three EC2 instances running Amazon Linux 2023.
- VPC Peering lifecycle: requester creation, accepter handshake, and lifecycle verification.
- Route table configuration: public route table, private A route table, and private B route table.
- Security group tightening: Bastion ingress, App-A ingress, and App-B ingress.
- SSH jump configuration (`ProxyJump` pattern).
- Controlled failure injection and recovery testing.
- Reproducible Infrastructure-as-Code (Terraform & Python Boto3).
- Interactive Live Dashboard and Web Documentation.

### Out-of-Scope (Design Decisions)
- AWS Transit Gateway or Site-to-Site VPN (excessive complexity and hourly base cost not warranted for dual-VPC architecture).
- NAT Gateway in VPC B (intentionally omitted to enforce complete internet isolation for backend workloads).
- Multi-Region peering (kept within single region `ap-south-1` to maintain low latency and eliminate inter-region transfer charges).

---

## 5. Stakeholders & Roles

- **Student / Author**: System architecture design, implementation, automation, and test validation.
- **Internship Evaluator / Mentor**: Review of architecture decisions, live evidence validation, code inspection, and viva assessment.
- **Cloud Administrator**: AWS lab environment boundaries and budget compliance oversight.
