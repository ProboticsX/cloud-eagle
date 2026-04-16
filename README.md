# Cloud Eagle

The CI/CD pipeline automates the entire deployment lifecycle from code commit to production release, ensuring reliability through automated testing, approval gates, and rollback mechanisms.

## Pipeline Stages

The pipeline consists of the following stages:

1.  **Checkout**: Clones the repository and determines the deployment environment based on the branch name.
    - `develop` : `qa`
    - `release/*` : `staging`
    - `main` : `prod`

2.  **Build & Test**: Compiles the Java code and runs automated tests.
    - Uses `./mvnw clean verify` for testing.
    - Generates JUnit and JaCoCo reports.

3.  **Docker Build**: Builds a Docker image with the new version.

4.  **Push Image**: Pushes the Docker image to Amazon ECR.

5.  **Approval**: Pauses the pipeline for manual approval before deploying to Staging or Production.

6.  **Deploy**: Deploys the new image to the target environment.
    - Fetches the target EC2 host from AWS SSM.
    - Runs the `deploy.py` script on the EC2 instance.

7.  **Smoke Test**: Runs automated smoke tests to validate the deployment.
    - If tests fail, it triggers an automatic rollback.
    - If tests pass, it updates the `last-stable-tag` in S3.

## Deployment Scripts

The pipeline relies on two Python scripts located in the `scripts/` directory:

- **`deploy.py`**: Handles the actual deployment logic for both Rolling and Blue/Green strategies.
- **`smoke_test.py`**: Executes health checks and basic validation after deployment.