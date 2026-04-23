output "cluster_name" {
  value = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "cluster_ca" {
  value     = aws_eks_cluster.main.certificate_authority[0].data
  sensitive = true
}

output "node_group_name" {
  value = aws_eks_node_group.main.node_group_name
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.region} --profile ${var.aws_profile}"
}

output "bedrock_role_arn" {
  value       = aws_iam_role.bedrock_rag.arn
  description = "Replace this in k8s/rag-app.yaml ServiceAccount annotation"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.rag_app.repository_url
}

output "ecr_login_command" {
  value = "aws ecr get-login-password --region ${var.region} --profile ${var.aws_profile} | docker login --username AWS --password-stdin ${aws_ecr_repository.rag_app.repository_url}"
}

output "karpenter_controller_role_arn" {
  value = aws_iam_role.karpenter_controller.arn
}

output "karpenter_node_role_name" {
  value = aws_iam_role.karpenter_node.name
}

output "karpenter_instance_profile_name" {
  value = aws_iam_instance_profile.karpenter_node.name
}
