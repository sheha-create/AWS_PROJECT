variable "aws_region" {
  description = "Target AWS Region"
  type        = string
  default     = "ap-south-1"
}

variable "student_name" {
  description = "Student Name for resource tagging"
  type        = string
  default     = "Intern"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "admin_ip" {
  description = "Admin workstation public IPv4 CIDR for Bastion SSH access"
  type        = string
  default     = "0.0.0.0/0" # Restricted in practice to your public IP /32
}

variable "key_name" {
  description = "EC2 Key Pair Name"
  type        = string
  default     = "ewb-lab"
}
