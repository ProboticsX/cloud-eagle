# Deployment script here

# Rolling Deployment:
# - If the environment is qa/staging then the script would perform a rolling deployment.
# - It would first stop the current container, then start the new container.
# - It would then wait for the new container to be healthy, and then start the next container.
# - It would repeat this process until all containers are deployed.

# Blue/Green Deployment:
# - If the environment is prod then the script would perform a blue/green deployment. 
# - Let's say the current traffic is being served by "Blue" env.
# - It would first stop the current container in the "Green" environment, then start the new container.