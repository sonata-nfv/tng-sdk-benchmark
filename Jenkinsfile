#!groovy

pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                echo 'Stage: Checkout...'
                checkout scm
            }
        }
        stage('Container build') {
            steps {
                echo 'Stage: Building...'
                sh "pipeline/build/build.sh"
            }
        }
        stage('Unittests') {
            steps {
                echo 'Stage: Testing...'
                sh "pipeline/unittest/test.sh"
            }
        }
        stage('Style check') {
            steps {
                echo 'Stage: Style check...'
                sh "pipeline/checkstyle/check.sh"
            }
        }
		stage('Promoting release v5.0') {
			when {
				branch 'v5.0'
			}
			stages {
				stage('Generating release') {
					steps {
						sh 'docker tag registry.sonata-nfv.eu:5000/tng-sdk-benchmark:latest registry.sonata-nfv.eu:5000/tng-sdk-benchmark:v5.0'
						sh 'docker tag registry.sonata-nfv.eu:5000/tng-sdk-benchmark:latest sonatanfv/tng-sdk-benchmark:v5.0'
						sh 'docker push registry.sonata-nfv.eu:5000/tng-sdk-benchmark:v5.0'
						sh 'docker push sonatanfv/tng-sdk-benchmark:v5.0'
					}
				}
				stage('Deploying in v5.0 servers') {
					steps {
						sh 'rm -rf tng-devops || true'
						sh 'git clone https://github.com/sonata-nfv/tng-devops.git'
						dir(path: 'tng-devops') {
						sh 'ansible-playbook roles/sp.yml -i environments -e "target=sta-sp-v5-0 component=gatekeeper"'
						sh 'ansible-playbook roles/vnv.yml -i environments -e "target=sta-vnv-v5-0 component=gatekeeper"'
						}
					}
				}
			}
		}
    }
    post {
         success {
                 emailext(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "SUCCESS: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
         failure {
                 emailext(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "FAILURE: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
    }
}
