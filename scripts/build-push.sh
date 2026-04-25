#!/bin/bash
set -euo pipefail

# Configuration
AWS_PROFILE="XXXXX"
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="123456789107"
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/rag-lab-rag-app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="${SCRIPT_DIR}/../demo-app"
K8S_MANIFEST="${SCRIPT_DIR}/../k8s/demo-app/deployment.yaml"

# Get version tag (use argument or generate from git/timestamp)
TAG="${1:-$(date +%Y%m%d-%H%M%S)}"

echo "=== Building image: ${ECR_REPO}:${TAG} ==="
docker build -t "${ECR_REPO}:${TAG}" "${APP_DIR}"

echo "=== Logging into ECR ==="
aws ecr get-login-password --region "${AWS_REGION}" --profile "${AWS_PROFILE}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "=== Pushing image ==="
docker push "${ECR_REPO}:${TAG}"

echo "=== Updating K8s manifest with new tag ==="
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s|image: ${ECR_REPO}:.*|image: ${ECR_REPO}:${TAG}|" "${K8S_MANIFEST}"
else
  sed -i "s|image: ${ECR_REPO}:.*|image: ${ECR_REPO}:${TAG}|" "${K8S_MANIFEST}"
fi

echo ""
echo "=== Done! ==="
echo "Image: ${ECR_REPO}:${TAG}"
echo "Manifest updated: ${K8S_MANIFEST}"
echo ""
echo "Next: commit and push the manifest change to Git."
echo "ArgoCD will detect the change and deploy the new version."
echo ""
echo "  git add ${K8S_MANIFEST}"
echo "  git commit -m 'deploy: demo-app ${TAG}'"
echo "  git push"
