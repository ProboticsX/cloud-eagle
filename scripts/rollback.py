# Rollback script Overview

# Rolling Rollback:
# - If the environment is qa/staging then the script would perform a rolling rollback.
# - It would first stop the current container, then start the previous stable container by checking the latest-stable-tag from S3.
# - It would then wait for the previous stable container to be healthy, and then start the next container.
# - It would repeat this process until all containers are rolled back.

# Blue/Green Rollback:
# - If the environment is prod then the script would perform a blue/green rollback. 
# - Let's say the new deployment was made in "Green" env.
# - It would first stop the current container in the "Green" environment, then start the previous stable container by checking the latest-stable-tag from S3. 
# - Since no deployment was ever made to "Blue" envs then it there's no need for ALB switch.