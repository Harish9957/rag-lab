variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile (SSO)"
  type        = string
  default     = "lab"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "rag-lab"
}

variable "cluster_version" {
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.34"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.200.0.0/16"
}

variable "node_instance_types" {
  description = "EC2 instance types for the node group"
  type        = list(string)
  default     = ["t3.large"]
}

variable "node_desired" {
  description = "Desired number of nodes"
  type        = number
  default     = 2
}

variable "node_min" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "node_max" {
  description = "Maximum number of nodes"
  type        = number
  default     = 3
}
