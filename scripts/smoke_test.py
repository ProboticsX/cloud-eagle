# Smoke Tests here

# Tests fail:
# - If the env is qa, staging: then the script would perform a rolling rollback.
# - If the env is prod: then the script would perform a blue/green rollback.
# - Refer rollback.py

# Tests Pass:
# - If the env is qa, staging: do nothing, the pipeline updates the latest image tag in S3.
# - If the env is prod: then the script would switch traffic to the environment running the new image in a full or partial rollout strategy using the ALB switch.