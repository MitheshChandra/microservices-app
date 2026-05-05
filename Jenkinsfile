pipeline {
    agent any
    
    environment {
        DOCKER_HUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKER_HUB_USERNAME = 'kmithesh'
        GIT_MANIFEST_REPO = 'https://github.com/MitheshChandra/microservices-k8s-manifests.git'
        GIT_CREDENTIALS_ID = 'github-credentials'
        ARGOCD_SERVER = '44.220.144.81:32438'  
        IMAGE_TAG = "${BUILD_NUMBER}"
        SERVICES = 'api-gateway,user-service,order-service,payment-service'
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo 'Installing Python dependencies...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                    pip install -r api-gateway/requirements.txt
                    pip install -r payment-service/requirements.txt
                '''
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                echo 'Running unit tests with pytest...'
                sh '''
                    . venv/bin/activate
                    pytest --verbose --junit-xml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }
        
        stage('Code Quality Check') {
            steps {
                echo 'Running flake8 code quality checks...'
                sh '''
                    . venv/bin/activate
                    flake8 . --count --statistics
                '''
            }
        }
        
        stage('Build Docker Images') {
            steps {
                echo 'Building Docker images for all microservices...'
                script {
                    def services = env.SERVICES.split(',')
                    services.each { service ->
                        sh """
                            docker build -t ${DOCKER_HUB_USERNAME}/${service}:${IMAGE_TAG} \
                                         -t ${DOCKER_HUB_USERNAME}/${service}:latest \
                                         ./${service}/
                        """
                    }
                }
            }
        }
        
        stage('Security Scan with Trivy') {
            steps {
                echo 'Scanning Docker images for vulnerabilities...'
                script {
                    def services = env.SERVICES.split(',')
                    services.each { service ->
                        sh """
                            trivy image --severity HIGH,CRITICAL \
                                --exit-code 0 \
                                ${DOCKER_HUB_USERNAME}/${service}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                echo 'Pushing Docker images to Docker Hub...'
                script {
                    sh """
                        echo ${DOCKER_HUB_CREDENTIALS_PSW} | docker login -u ${DOCKER_HUB_CREDENTIALS_USR} --password-stdin
                    """
                    
                    def services = env.SERVICES.split(',')
                    services.each { service ->
                        sh """
                            docker push ${DOCKER_HUB_USERNAME}/${service}:${IMAGE_TAG}
                            docker push ${DOCKER_HUB_USERNAME}/${service}:latest
                        """
                    }
                }
            }
        }
        
        stage('Update Kubernetes Manifests') {
            steps {
                echo 'Updating Kubernetes manifests with new image tags...'
                script {
                    withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS_ID}", 
                                                       usernameVariable: 'GIT_USERNAME', 
                                                       passwordVariable: 'GIT_PASSWORD')]) {
                        sh """
                            rm -rf k8s-manifests-temp
                            git clone https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/MitheshChandra/microservices-k8s-manifests.git k8s-manifests-temp
                            cd k8s-manifests-temp
                            
                            # Update dev environment
                            sed -i 's|image: ${DOCKER_HUB_USERNAME}/api-gateway:.*|image: ${DOCKER_HUB_USERNAME}/api-gateway:${IMAGE_TAG}|g' Dev/api-gateway.yaml
                            sed -i 's|image: ${DOCKER_HUB_USERNAME}/user-service:.*|image: ${DOCKER_HUB_USERNAME}/user-service:${IMAGE_TAG}|g' Dev/user-service.yaml
                            sed -i 's|image: ${DOCKER_HUB_USERNAME}/order-service:.*|image: ${DOCKER_HUB_USERNAME}/order-service:${IMAGE_TAG}|g' Dev/order-service.yaml
                            sed -i 's|image: ${DOCKER_HUB_USERNAME}/payment-service:.*|image: ${DOCKER_HUB_USERNAME}/payment-service:${IMAGE_TAG}|g' Dev/payment-service.yaml
                            
                            git config user.email "jenkins@cicd.local"
                            git config user.name "Jenkins CI"
                            git add .
                            git commit -m "Jenkins Build ${BUILD_NUMBER}: Update dev images to tag ${IMAGE_TAG}" || true
                            git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/MitheshChandra/microservices-k8s-manifests.git main
                            
                            cd ..
                            rm -rf k8s-manifests-temp
                        """
                    }
                }
            }
        }
        
        stage('Deploy to DEV (Auto)') {
            steps {
                echo 'Triggering Argo CD sync for DEV environment...'
                script {
                    withCredentials([usernamePassword(credentialsId: 'argocd-credentials', 
                                                       usernameVariable: 'ARGOCD_USERNAME', 
                                                       passwordVariable: 'ARGOCD_PASSWORD')]) {
                        sh """
                            argocd login ${ARGOCD_SERVER} --insecure --username ${ARGOCD_USERNAME} --password ${ARGOCD_PASSWORD}
                            argocd app sync microservices-dev --force
                            argocd app wait microservices-dev --timeout 300
                        """
                    }
                }
            }
        }
        
        stage('Approval for PROD') {
            steps {
                echo 'Waiting for manual approval to deploy to PROD...'
                input message: 'Deploy to Production?', 
                      ok: 'Deploy', 
                      submitter: 'devops-manager,sde-manager'
            }
        }
        
        stage('Update PROD Manifests') {
            steps {
                echo 'Updating PROD Kubernetes manifests...'
                script {
                    withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS_ID}", 
                                                       usernameVariable: 'GIT_USERNAME', 
                                                       passwordVariable: 'GIT_PASSWORD')]) {
                        sh """
                            rm -rf k8s-manifests-temp
                            git clone https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/MitheshChandra/microservices-k8s-manifests.git k8s-manifests-temp
                            cd k8s-manifests-temp
                            
                            # Update prod environment
                            sed -i 's|image: ${DOCKER_HUB_USERNAME}/api-gateway:.*|image: ${DOCKER_HUB_USERNAME}/api-gateway:${IMAGE_TAG}|g' Prod/api-gateway.yaml
                            sed -i 's|image: ${DOCKER_HUB_USERNAME}/user-service:.*|image: ${DOCKER_HUB_USERNAME}/user-service:${IMAGE_TAG}|g' Prod/user-service.yaml
                            sed -i 's|image: ${DOCKER_HUB_USERNAME}/order-service:.*|image: ${DOCKER_HUB_USERNAME}/order-service:${IMAGE_TAG}|g' Prod/order-service.yaml
                            sed -i 's|image: ${DOCKER_HUB_USERNAME}/payment-service:.*|image: ${DOCKER_HUB_USERNAME}/payment-service:${IMAGE_TAG}|g' Prod/payment-service.yaml
                            
                            git config user.email "jenkins@cicd.local"
                            git config user.name "Jenkins CI"
                            git add .
                            git commit -m "Jenkins Build ${BUILD_NUMBER}: Update prod images to tag ${IMAGE_TAG}" || true
                            git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/MitheshChandra/microservices-k8s-manifests.git main
                            
                            cd ..
                            rm -rf k8s-manifests-temp
                        """
                    }
                }
            }
        }
        
        stage('Deploy to PROD (Manual)') {
            steps {
                echo 'Triggering Argo CD sync for PROD environment...'
                script {
                    withCredentials([usernamePassword(credentialsId: 'argocd-credentials', 
                                                       usernameVariable: 'ARGOCD_USERNAME', 
                                                       passwordVariable: 'ARGOCD_PASSWORD')]) {
                        sh """
                            argocd login ${ARGOCD_SERVER} --insecure --username ${ARGOCD_USERNAME} --password ${ARGOCD_PASSWORD}
                            argocd app sync microservices-prod --force
                            argocd app wait microservices-prod --timeout 300
                        """
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check logs for details.'
        }
        always {
            echo 'Cleaning up...'
            sh 'docker system prune -f || true'
            cleanWs()
        }
    }
}
