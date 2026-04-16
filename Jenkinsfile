pipeline {
    // The pipeline gets auto-triggered on any merges to feature/develop/release/main branch
    agent any

    environment {
        AWS_REGION         = 'us-east-1'
        AWS_ACCOUNT_ID     = credentials('aws-account-id')
        ECR_REPO           = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/sync-service"
        S3_STATE_BUCKET    = 'sync-service-deploy-state' // needed to store the stable image tags
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.SHORT_SHA   = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.BRANCH_NAME = env.GIT_BRANCH?.replaceAll('origin/', '') ?: 'unknown'

                    // Determine target environment from branch
                    if (env.BRANCH_NAME == 'develop') {
                        env.DEPLOY_ENV = 'qa'
                    } else if (env.BRANCH_NAME.startsWith('release/')) {
                        env.DEPLOY_ENV = 'staging'
                    } else if (env.BRANCH_NAME == 'main') {
                        env.DEPLOY_ENV = 'prod'
                    } else {
                        // feature branches are not deployed
                        env.DEPLOY_ENV = 'none'  
                    }

                    env.IMAGE_TAG = "${ECR_REPO}:${env.DEPLOY_ENV}-${env.SHORT_SHA}"
                    echo "Branch: ${env.BRANCH_NAME} | Env: ${env.DEPLOY_ENV} | Tag: ${env.IMAGE_TAG}"
                }
            }
        }

        // STAGE 2: Build & Test
        stage('Build & Test') {
            steps {
                // maven to run integration and unit tests for the Java app
                sh './mvnw clean verify -Dspring.profiles.active=test'
            }
            post {
                always {
                    // store test results and display it later in the Jenkins UI
                    junit 'target/surefire-reports/**/*.xml'
                    // store code coverage results and display it later in the Jenkins UI
                    jacoco(
                        execPattern:   'target/jacoco.exec',
                        classPattern:  'target/classes',
                        sourcePattern: 'src/main/java'
                    )
                }
            }
        }

        // STAGE 3: Docker Build
        // Only runs on deployable branches

        stage('Docker Build') {
            when {
                expression { env.DEPLOY_ENV != 'none' }
            }
            steps {
                sh "docker build -t ${env.IMAGE_TAG} ."
            }
        }

        // STAGE 4: Push Image to ECR
        stage('Push Image') {
            when {
                expression { env.DEPLOY_ENV != 'none' }
            }
            steps {
                sh """
                    aws ecr get-login-password --region ${AWS_REGION} \
                        | docker login --username AWS --password-stdin ${ECR_REPO}
                    docker push ${env.IMAGE_TAG}
                """
            }
        }

        // STAGE 5: Approval Gate
        // Need approval only for staging, prod envs
        stage('Approval') {
            when {
                expression { env.DEPLOY_ENV in ['staging', 'prod'] }
            }
            steps {
                input message: "Deploy ${env.IMAGE_TAG} to *${env.DEPLOY_ENV.toUpperCase()}*?"
            }
        }

        // STAGE 6: Deploy
        // Calls deploy.py script to deploy the new image
        // qa, staging: Rolling Deployments
        // prod: Blue/Green
        stage('Deploy') {
            when {
                expression { env.DEPLOY_ENV != 'none' }
            }
            steps {
                script {
                    // Fetch target EC2 host from SSM
                    env.TARGET_HOST = sh(
                        script: "aws ssm get-parameter --name /sync-service/${env.DEPLOY_ENV}/ec2-host --query Parameter.Value --output text --region ${AWS_REGION}",
                        returnStdout: true
                    ).trim()

                    // Save current stable tag before deploying (for rollback)
                    sh """
                        CURRENT_TAG=\$(aws s3 cp s3://${S3_STATE_BUCKET}/sync-service/${env.DEPLOY_ENV}/last-stable-tag - 2>/dev/null || echo "none")
                        echo "Previous stable tag: \$CURRENT_TAG"
                        echo "\$CURRENT_TAG" > previous-tag.txt
                    """
                }
                // SSH EC2 host to run deploy.py
                sshagent(credentials: ["ec2-ssh-key-${env.DEPLOY_ENV}"]) {
                    // Copies and runs deploy.py on EC2 host
                    sh """
                        scp -o StrictHostKeyChecking=no \
                            scripts/deploy.py \
                            ec2-user@${env.TARGET_HOST}:/tmp/deploy.py

                        ssh -o StrictHostKeyChecking=no ec2-user@${env.TARGET_HOST} \
                            "python3 /tmp/deploy.py \
                                --image ${env.IMAGE_TAG} \
                                --env ${env.DEPLOY_ENV} \
                                --region ${AWS_REGION}  "
                    """
                }
            }
        }

        // STAGE 7: Smoke Test
        // If it fails, auto-rollback to previous tag
            // qa, staging: rolling rollback
            // prod: blue/green rollback
        // If succeeds, update last-stable-tag in S3
            // qa, staging: rolling deployment
            // prod: blue/green deployment
        stage('Smoke Test') {
            when {
                expression { env.DEPLOY_ENV != 'none' }
            }
            steps {
                script {
                    def result = sh(
                        script: "python3 scripts/smoke_test.py --host ${env.TARGET_HOST} --retries 10 --interval 6",
                        returnStatus: true
                    )

                    if (result != 0) {
                        echo "Smoke test FAILED — initiating rollback"
                        def previousTag = readFile('previous-tag.txt').trim()

                        if (previousTag == 'none') {
                            error("Smoke test failed and no previous tag found — manual intervention required")
                        }

                        sshagent(credentials: ["ec2-ssh-key-${env.DEPLOY_ENV}"]) {
                            sh """
                                scp -o StrictHostKeyChecking=no \
                                    scripts/rollback.py \
                                    ec2-user@${env.TARGET_HOST}:/tmp/rollback.py

                                ssh -o StrictHostKeyChecking=no ec2-user@${env.TARGET_HOST} \
                                    "python3 /tmp/rollback.py \
                                        --image ${previousTag} \
                                        --env ${env.DEPLOY_ENV} \
                                        --region ${AWS_REGION}"
                            """
                        }
                        error("Deployment rolled back to ${previousTag}")
                    }

                    // Smoke test passed, persist new stable tag
                    sh "aws s3 cp - s3://${S3_STATE_BUCKET}/sync-service/${env.DEPLOY_ENV}/last-stable-tag <<< '${env.IMAGE_TAG}'"
                }
            }
        }
    }

}
