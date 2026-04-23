# Runbook: Common Kubernetes Issues

## OOMKilled Pod
- **Symptom:** Pod status shows OOMKilled, restarts increasing
- **Cause:** Container memory usage exceeds the memory limit set in the deployment
- **Fix:** Increase `resources.limits.memory` in the deployment spec. Example: change 256Mi to 512Mi
- **Command:** `kubectl describe pod <pod-name> -n <namespace>` — look for "OOMKilled" in Last State
- **Simulate:** Deploy a pod with 64Mi memory limit running a memory stress tool

## CrashLoopBackOff
- **Symptom:** Pod keeps restarting, status shows CrashLoopBackOff
- **Cause:** Application crashes on startup — missing config, bad image, or dependency unavailable
- **Fix:** Check logs with `kubectl logs <pod-name> -n <namespace> --previous`. Fix the root cause (config, image tag, etc.)
- **Command:** `kubectl get events -n <namespace> --sort-by=.lastTimestamp`
- **Simulate:** Deploy a pod with a non-existent command or missing env var

## ImagePullBackOff
- **Symptom:** Pod stuck in ImagePullBackOff or ErrImagePull
- **Cause:** Image doesn't exist, wrong tag, or no pull credentials
- **Fix:** Verify image name and tag. Check if image exists: `docker manifest inspect <image>:<tag>`. For private repos, ensure imagePullSecrets is configured.
- **Command:** `kubectl describe pod <pod-name> -n <namespace>` — check Events section
- **Simulate:** Deploy a pod with image `nginx:nonexistent-tag`

## Pending Pod (Insufficient Resources)
- **Symptom:** Pod stuck in Pending state
- **Cause:** Not enough CPU or memory on any node to schedule the pod
- **Fix:** Reduce resource requests, or scale up the node group. Check node capacity with `kubectl describe nodes | grep -A 5 "Allocated resources"`
- **Command:** `kubectl get events -n <namespace>` — look for "FailedScheduling"
- **Simulate:** Deploy a pod requesting 100Gi memory
