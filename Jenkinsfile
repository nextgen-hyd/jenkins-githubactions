pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials') // Add Docker Hub credentials in Jenkins
        KUBERNETES_CREDENTIALS = credentials('k8s-credentials')     // Add Kubernetes credentials in Jenkins
        SONARQUBE_ENV = 'SonarQube'                                // Name of the SonarQube instance in Jenkins
    }

    stages {
        stage('Clone Code') {
            steps {
                git branch: 'main', url: 'https://github.com/your-repo/your-project.git'
            }
        }

        stage('Build with Maven') {
            steps {
                withMaven(maven: 'Maven3') {  
                    sh 'mvn clean package'   
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') { 
                    sh 'mvn sonar:sonar'       
                }
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-credentials') {
                        def app = docker.build("your-dockerhub-username/your-app-name:${env.BUILD_NUMBER}")
                        app.push()
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                kubernetesDeploy(
                    configs: 'k8s-deployment.yaml',   
                    kubeconfigId: 'k8s-credentials', 
                    enableConfigSubstitution: true
                )
            }
        }
    }

}

