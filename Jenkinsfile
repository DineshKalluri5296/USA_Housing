pipeline {
    agent any

    environment {
        AWS_REGION = "us-east-1"
        ECR_REPO = "usa-ml-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        ACCOUNT_ID = "440977420038"
        ECR_URI = "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        FULL_IMAGE_NAME = "${ECR_URI}/${ECR_REPO}:${IMAGE_TAG}"
    }

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-credentials',
                    url: 'https://github.com/DineshKalluri5296/USA_Housing.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                python3 -m pip install --upgrade pip
                python3 -m pip install -r requirements.txt
                python3 -m pip install pytest pytest-cov
                '''
            }
        }

        stage('Run Tests & Coverage') {
            steps {
                sh '''
                python3 -m pytest --cov=. --cov-report=xml
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh """
                    ${tool 'SonarScanner'}/bin/sonar-scanner \
                    -Dsonar.projectKey=usa \
                    -Dsonar.sources=. \
                    -Dsonar.python.version=3 \
                    -Dsonar.python.coverage.reportPaths=coverage.xml
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 2, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Train Model + Upload to S3 (Only First Run)') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                credentialsId: 'aws-credentials']]) {

                    sh '''
                    set +e

                    MODEL_PATH="s3://usa-ml-app1/models/latest/model.pkl"

                    echo "🔍 Checking if model exists in S3..."

                    aws s3 ls ${MODEL_PATH} >/dev/null 2>&1

                    if [ $? -eq 0 ]; then
                        echo "✅ Model already exists. Skipping training."
                    else
                        echo "🚀 Training model..."

                        python3 train.py

                        echo "📦 Uploading model to S3..."

                        aws s3 cp model.pkl ${MODEL_PATH}

                        echo "✅ Model uploaded successfully."
                    fi
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${FULL_IMAGE_NAME} .'
            }
        }

        stage('Login to AWS ECR') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                credentialsId: 'aws-credentials']]) {

                    sh '''
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_URI}
                    '''
                }
            }
        }

        stage('Push Image to ECR') {
            steps {
                sh 'docker push ${FULL_IMAGE_NAME}'
            }
        }

        stage('Create Monitoring Network') {
            steps {
                sh '''
                docker network inspect monitoring-network >/dev/null 2>&1 || \
                docker network create monitoring-network
                '''
            }
        }

        stage('Deploy FastAPI Container') {
            steps {
                sh '''
                docker rm -f usa-container || true
                docker run -d \
                  --name usa-container \
                  --network monitoring-network \
                  -p 8000:8000 \
                  ${FULL_IMAGE_NAME}
                '''
            }
        }

        stage('Deploy Node Exporter') {
            steps {
                sh '''
                docker rm -f node-exporter || true
                docker run -d \
                  --name node-exporter \
                  --network monitoring-network \
                  -p 9100:9100 \
                  prom/node-exporter
                '''
            }
        }

        stage('Deploy Prometheus') {
            steps {
                sh '''
                docker rm -f prometheus || true
                docker run -d \
                  --name prometheus \
                  --network monitoring-network \
                  -p 9090:9090 \
                  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
                  prom/prometheus
                '''
            }
        }

        stage('Deploy Grafana') {
            steps {
                sh '''
                docker rm -f grafana || true
                docker run -d \
                  --name grafana \
                  --network monitoring-network \
                  -p 3000:3000 \
                  grafana/grafana
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Deployment Successful 🚀"
        }
        failure {
            echo "❌ Pipeline Failed"
        }
    }
}
