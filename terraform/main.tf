# ==============================================================================
# VPC A: 10.10.0.0/16
# ==============================================================================
resource "aws_vpc" "vpc_a" {
  cidr_block           = "10.10.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "ewb-vpc-a"
    Student = var.student_name
  }
}

# Internet Gateway for VPC A
resource "aws_internet_gateway" "igw_a" {
  vpc_id = aws_vpc.vpc_a.id

  tags = {
    Name    = "ewb-igw-a"
    Student = var.student_name
  }
}

# Public Subnet in VPC A: 10.10.1.0/24
resource "aws_subnet" "subnet_a_public" {
  vpc_id                  = aws_vpc.vpc_a.id
  cidr_block              = "10.10.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name    = "ewb-a-public"
    Student = var.student_name
  }
}

# Private Subnet in VPC A: 10.10.2.0/24
resource "aws_subnet" "subnet_a_private" {
  vpc_id                  = aws_vpc.vpc_a.id
  cidr_block              = "10.10.2.0/24"
  map_public_ip_on_launch = false

  tags = {
    Name    = "ewb-a-private"
    Student = var.student_name
  }
}

# ==============================================================================
# VPC B: 10.20.0.0/16 (Isolated workload VPC, No IGW)
# ==============================================================================
resource "aws_vpc" "vpc_b" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "ewb-vpc-b"
    Student = var.student_name
  }
}

# Private Subnet in VPC B: 10.20.1.0/24
resource "aws_subnet" "subnet_b_private" {
  vpc_id                  = aws_vpc.vpc_b.id
  cidr_block              = "10.20.1.0/24"
  map_public_ip_on_launch = false

  tags = {
    Name    = "ewb-b-private"
    Student = var.student_name
  }
}

# ==============================================================================
# VPC Peering Connection: VPC A <-> VPC B
# ==============================================================================
resource "aws_vpc_peering_connection" "peer" {
  peer_vpc_id = aws_vpc.vpc_b.id
  vpc_id      = aws_vpc.vpc_a.id
  auto_accept = true

  tags = {
    Name    = "ewb-a-b-peer"
    Student = var.student_name
  }
}

# ==============================================================================
# Route Tables & Routes
# ==============================================================================

# Route Table 1: ewb-rt-a-public (VPC A Public Subnet)
resource "aws_route_table" "rt_a_public" {
  vpc_id = aws_vpc.vpc_a.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw_a.id
  }

  route {
    cidr_block                = "10.20.0.0/16"
    vpc_peering_connection_id = aws_vpc_peering_connection.peer.id
  }

  tags = {
    Name    = "ewb-rt-a-public"
    Student = var.student_name
  }
}

resource "aws_route_table_association" "a_public_assoc" {
  subnet_id      = aws_subnet.subnet_a_public.id
  route_table_id = aws_route_table.rt_a_public.id
}

# Route Table 2: ewb-rt-a-private (VPC A Private Subnet)
resource "aws_route_table" "rt_a_private" {
  vpc_id = aws_vpc.vpc_a.id

  route {
    cidr_block                = "10.20.0.0/16"
    vpc_peering_connection_id = aws_vpc_peering_connection.peer.id
  }

  tags = {
    Name    = "ewb-rt-a-private"
    Student = var.student_name
  }
}

resource "aws_route_table_association" "a_private_assoc" {
  subnet_id      = aws_subnet.subnet_a_private.id
  route_table_id = aws_route_table.rt_a_private.id
}

# Route Table 3: ewb-rt-b-private (VPC B Private Subnet)
resource "aws_route_table" "rt_b_private" {
  vpc_id = aws_vpc.vpc_b.id

  route {
    cidr_block                = "10.10.0.0/16"
    vpc_peering_connection_id = aws_vpc_peering_connection.peer.id
  }

  tags = {
    Name    = "ewb-rt-b-private"
    Student = var.student_name
  }
}

resource "aws_route_table_association" "b_private_assoc" {
  subnet_id      = aws_subnet.subnet_b_private.id
  route_table_id = aws_route_table.rt_b_private.id
}

# ==============================================================================
# Security Groups
# ==============================================================================

# SG Bastion (VPC A)
resource "aws_security_group" "sg_bastion" {
  name        = "ewb-sg-bastion"
  description = "Allow inbound SSH to Bastion from admin IP"
  vpc_id      = aws_vpc.vpc_a.id

  ingress {
    description = "SSH from Admin"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_ip]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "ewb-sg-bastion"
    Student = var.student_name
  }
}

# SG App-A (VPC A Private)
resource "aws_security_group" "sg_app_a" {
  name        = "ewb-sg-app-a"
  description = "Allow SSH from Bastion and ICMP from App-B"
  vpc_id      = aws_vpc.vpc_a.id

  ingress {
    description = "SSH from Bastion private IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.10.1.10/32"]
  }

  ingress {
    description = "ICMP Echo Request from App-B"
    from_port   = 8
    to_port     = 0
    protocol    = "icmp"
    cidr_blocks = ["10.20.1.10/32"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "ewb-sg-app-a"
    Student = var.student_name
  }
}

# SG App-B (VPC B Private)
resource "aws_security_group" "sg_app_b" {
  name        = "ewb-sg-app-b"
  description = "Allow SSH from Bastion and ICMP from App-A"
  vpc_id      = aws_vpc.vpc_b.id

  ingress {
    description = "SSH from Bastion private IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.10.1.10/32"]
  }

  ingress {
    description = "ICMP Echo Request from App-A"
    from_port   = 8
    to_port     = 0
    protocol    = "icmp"
    cidr_blocks = ["10.10.2.10/32"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "ewb-sg-app-b"
    Student = var.student_name
  }
}

# ==============================================================================
# EC2 Instances
# ==============================================================================

# Fetch latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# 1. Bastion Host (VPC A Public Subnet)
resource "aws_instance" "bastion" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  subnet_id                   = aws_subnet.subnet_a_public.id
  private_ip                  = "10.10.1.10"
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.sg_bastion.id]

  tags = {
    Name    = "ewb-bastion"
    Student = var.student_name
  }
}

# 2. App-A Instance (VPC A Private Subnet)
resource "aws_instance" "app_a" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  subnet_id                   = aws_subnet.subnet_a_private.id
  private_ip                  = "10.10.2.10"
  associate_public_ip_address = false
  vpc_security_group_ids      = [aws_security_group.sg_app_a.id]

  tags = {
    Name    = "ewb-app-a"
    Student = var.student_name
  }
}

# 3. App-B Instance (VPC B Private Subnet)
resource "aws_instance" "app_b" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  subnet_id                   = aws_subnet.subnet_b_private.id
  private_ip                  = "10.20.1.10"
  associate_public_ip_address = false
  vpc_security_group_ids      = [aws_security_group.sg_app_b.id]

  tags = {
    Name    = "ewb-app-b"
    Student = var.student_name
  }
}
