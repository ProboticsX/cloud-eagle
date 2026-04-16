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
- **`rollback.py`**: Executes rollback logic for both Rolling and Blue/Green strategies.

## Answers to a Few Questions as shared in the Google Doc:

1.  **What's the branching strategy?**

    a. How am I mapping branches to environments?
    - **`develop`**: For development work. Triggers QA deployments.
    - **`release/*`**: For release candidates. Triggers Staging deployments.
    - **`main`**: For production releases. Triggers Production deployments.
    - **Other branches** (e.g., feature branches): Are not deployed.

    b. How am I avoiding accidental prod deployments?
    - Every staging, prod env specific deployments need a manual approval gate. Without the manual approval, no deployment can happen in these environments hence avoiding accidental deployments.


1.  **What's the Jenkins Pipeline?**

    a. High Level stages
    - Already shared above in the "Pipeline Stages" section.

    b. What happens on PR vs Merge?
    - Whenever a PR is raised, nothing happens. I believe there's no need to fire Jenkins pipeline whenever a PR is raised but if we wish to do so, then we could using Jenkinsfile triggers and adding Github webhook.
    - Whenever a PR is merged to develop/release/main/feature branch, Jenkins pipeline gets triggered.
        - **`feature/*`**: Only the Build & Test stage gets triggered.
        - **`develop`**: Build & Test -> Docker Build -> Push Image -> Deploy -> Smoke Test stages get triggered. The deployment is a Rolling one.
        - **`release`**: Build & Test -> Docker Build -> Push Image -> Approval -> Deploy -> Smoke Test stages get triggered. The deployment is a Rolling one.
        - **`main`**: Build & Test -> Docker Build -> Push Image -> Approval -> Deploy -> Smoke Test stages get triggered. The deployment is a Blue/Green one.

    c. How am I handling rollbacks?
        - **`feature`**: No rollbacks since no deployment happens in this branch.
        - **`develop, release`**: If smoke test fails, it triggers an automatic rolling rollback to the previous stable tag.
        - **`main`**: If smoke test fails, it triggers an automatic blue/green rollback to the previous stable tag.
        - Please refer `scripts/rollback.py` for more details.
        
        
    