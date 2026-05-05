pipeline {
    agent any
    
    environment {
        DOCKER_HUB_REPO = 'kmithesh'
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        GIT_MANIFEST_REPO = 'https://github.com/MitheshChandra/microservices-k8s-manifests.git'
        GIT_CREDENTIALS_ID = 'github-credentials'
        ARGOCD_SERVER = credentials('argocd-server')
        ARGOCD_AUTH_TOKEN = credentials('argocd-auth-token')
    }
    
    parameters {
        choice(name: 'DEPLOY_ENV', choices: ['dev', 'prod'], description: 'Target deployment environment')
        choice(name: 'SERVICE', choices: ['all', 'api-gateway', 'user-service', 'order-service', 'payment-service'], description: 'Service to build and deploy')
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                script {
                    echo "Checking out source code..."
                    checkout scm
                    env.GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                    env.BUILD_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"
                    echo "Build tag: ${env.BUILD_TAG}"
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script {
                    echo "Installing Python dependencies..."
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements-dev.txt
                    '''
                }
            }
        }
        
        stage('Code Quality Check') {
            steps {
                script {
                    echo "Running Flake8 code quality checks..."
                    sh '''
                        . venv/bin/activate
                        flake8 . --count --show-source --statistics || true
                    '''
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                script {
                    echo "Running unit tests..."
                    sh '''
                        . venv/bin/activate
                        pip install -r api-gateway/requirements.txt
                        pip install -r payment-service/requirements.txt
                        pytest tests/ -v --junitxml=test-results.xml --cov=. --cov-report=xml --cov-report=html
                    '''
                }
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishHTML(target: [
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Build Docker Images') {
            steps {
                script {
                    def services = params.SERVICE == 'all' ? 
                        ['api-gateway', 'user-service', 'order-service', 'payment-service'] : 
                        [params.SERVICE]
                    
                    services.each { service ->
                        echo "Building Docker image for ${service}..."
                        sh """
                            cd ${service}
                            docker build -t ${DOCKER_HUB_REPO}/${service}:${BUILD_TAG} .
                            docker tag ${DOCKER_HUB_REPO}/${service}:${BUILD_TAG} ${DOCKER_HUB_REPO}/${service}:latest
                        """
                    }
                }
            }
        }
        
        stage('Security Scan with Trivy') {
            steps {
                script {
                    def services = params.SERVICE == 'all' ? 
                        ['api-gateway', 'user-service', 'order-service', 'payment-service'] : 
                        [params.SERVICE]
                    
                    services.each { service ->
                        echo "Scanning ${service} for vulnerabilities..."
                        sh """
                            trivy image --severity HIGH,CRITICAL --exit-code 0 ${DOCKER_HUB_REPO}/${service}:${BUILD_TAG}
                        """
                    }
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                script {
                    def services = params.SERVICE == 'all' ? 
                        ['api-gateway', 'user-service', 'order-service', 'payment-service'] : 
                        [params.SERVICE]
                    
                    docker.withRegistry('https://index.docker.io/v1/', "${DOCKER_CREDENTIALS_ID}") {
                        services.each { service ->
                            echo "Pushing ${service} to Docker Hub..."
                            sh """
                                docker push ${DOCKER_HUB_REPO}/${service}:${BUILD_TAG}
                                docker push ${DOCKER_HUB_REPO}/${service}:latest
                            """
                        }
                    }
                }
            }
        }
        
        stage('Update Kubernetes Manifests') {
            steps {
                script {
                    def services = params.SERVICE == 'all' ? 
                        ['api-gateway', 'user-service', 'order-service', 'payment-service'] : 
                        [params.SERVICE]
                    
                    echo "Cloning manifest repository..."
                    
                    withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS_ID}", 
                                                      usernameVariable: 'GIT_USERNAME', 
                                                      passwordVariable: 'GIT_PASSWORD')]) {
                        sh '''
                            rm -rf microservices-k8s-manifests
                            git clone https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/MitheshChandra/microservices-k8s-manifests.git
                            cd microservices-k8s-manifests
                            git config user.email "jenkins@ci.com"
                            git config user.name "Jenkins CI"
                        '''
                        
                        services.each { service ->
                            echo "Updating ${service} manifest for ${params.DEPLOY_ENV} environment..."
                            sh """
                                cd microservices-k8s-manifests/${params.DEPLOY_ENV}
                                sed -i 's|image: ${DOCKER_HUB_REPO}/${service}:.*|image: ${DOCKER_HUB_REPO}/${service}:${BUILD_TAG}|' ${service}.yaml
                            """
                        }
                        
                        sh '''
                            cd microservices-k8s-manifests
                            git add .
                            git commit -m "Jenkins CI: Update image tags to ${BUILD_TAG} for ${DEPLOY_ENV}" || echo "No changes to commit"
                            git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/MitheshChandra/microservices-k8s-manifests.git main
                        '''
                    }
                }
            }
        }
        
        stage('Deploy to Dev (Auto)') {
            when {
                expression { params.DEPLOY_ENV == 'dev' }
            }
            steps {
                script {
                    echo "Auto-deploying to Dev environment via Argo CD..."
                    sh """
                        argocd login ${ARGOCD_SERVER} --auth-token ${ARGOCD_AUTH_TOKEN} --insecure
                        argocd app sync microservices-dev --force
                        argocd app wait microservices-dev --timeout 300
                    """
                }
            }
        }
        
        stage('Approval for Prod') {
            when {
                expression { params.DEPLOY_ENV == 'prod' }
            }
            steps {
                script {
                    echo "Waiting for manual approval to deploy to Production..."
                    input message: 'Deploy to Production?', 
                          ok: 'Deploy',
                          submitter: 'devops-manager,sde-manager'
                }
            }
        }
        
        stage('Deploy to Prod (Manual)') {
            when {
                expression { params.DEPLOY_ENV == 'prod' }
            }
            steps {
                script {
                    echo "Deploying to Production environment via Argo CD..."
                    sh """
                        argocd login ${ARGOCD_SERVER} --auth-token ${ARGOCD_AUTH_TOKEN} --insecure
                        argocd app sync microservices-prod --force
                        argocd app wait microservices-prod --timeout 300
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo "Pipeline completed successfully!"
            echo "Services deployed to ${params.DEPLOY_ENV} environment"
        }
        failure {
            echo "Pipeline failed. Check logs for details."
        }
        always {
            cleanWs()
        }
    }
}