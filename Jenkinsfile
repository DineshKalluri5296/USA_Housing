// pipeline {
//     agent any

//     environment {
//         AWS_REGION = "us-east-1"
//         ECR_REPO = "usa-ml-app"
//         IMAGE_TAG = "${BUILD_NUMBER}"
//         ACCOUNT_ID = "440977420038"
//         ECR_URI = "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
//         FULL_IMAGE_NAME = "${ECR_URI}/${ECR_REPO}:${IMAGE_TAG}"
//     }

//     stages {

//         stage('Checkout Code') {
//             steps {
//                 git branch: 'main',
//                     credentialsId: 'github-credentials',
//                     url: 'https://github.com/DineshKalluri5296/USA_Housing.git'
//             }
//         }

//         stage('Install Dependencies') {
//             steps {
//                 sh '''
//                 python3 -m pip install --upgrade pip
//                 python3 -m pip install -r requirements.txt
//                 python3 -m pip install pytest pytest-cov
//                 '''
//             }
//         }

//         // stage('Run Tests & Coverage') {
//         //     steps {
//         //         sh '''
//         //         python3 -m pytest --cov=. --cov-report=xml
//         //         '''
//         //     }
//         // }

//         stage('SonarQube Analysis') {
//             steps {
//                 withSonarQubeEnv('SonarQube') {
//                     sh """
//                     ${tool 'SonarScanner'}/bin/sonar-scanner \
//                     -Dsonar.projectKey=usa \
//                     -Dsonar.sources=. \
//                     -Dsonar.python.version=3 \
//                     """
//                 }
//             }
//         }

//         // stage('Quality Gate') {
//         //     steps {
//         //         timeout(time: 2, unit: 'MINUTES') {
//         //             waitForQualityGate abortPipeline: true
//         //         }
//         //     }
//         // }

//         stage('Train Model + Upload to S3 (Only First Run)') {
//             steps {
//                 withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
//                 credentialsId: 'aws-credentials']]) {

//                     sh '''
//                     set +e

//                     MODEL_PATH="s3://usa-ml-app1/models/latest/model.pkl"

//                     echo "🔍 Checking if model exists in S3..."

//                     aws s3 ls ${MODEL_PATH} >/dev/null 2>&1

//                     if [ $? -eq 0 ]; then
//                         echo "✅ Model already exists. Skipping training."
//                     else
//                         echo "🚀 Training model..."

//                         python3 train.py

//                         echo "📦 Uploading model to S3..."

//                         aws s3 cp model.pkl ${MODEL_PATH}

//                         echo "✅ Model uploaded successfully."
//                     fi
//                     '''
//                 }
//             }
//         }

//         stage('Build Docker Image') {
//             steps {
//                 sh 'docker build -t ${FULL_IMAGE_NAME} .'
//             }
//         }

//         stage('Login to AWS ECR') {
//             steps {
//                 withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
//                 credentialsId: 'aws-credentials']]) {

//                     sh '''
//                     aws ecr get-login-password --region ${AWS_REGION} | \
//                     docker login --username AWS --password-stdin ${ECR_URI}
//                     '''
//                 }
//             }
//         }

//         stage('Push Image to ECR') {
//             steps {
//                 sh 'docker push ${FULL_IMAGE_NAME}'
//             }
//         }

//         stage('Create Monitoring Network') {
//             steps {
//                 sh '''
//                 docker network inspect monitoring-network >/dev/null 2>&1 || \
//                 docker network create monitoring-network
//                 '''
//             }
//         }

//         stage('Deploy FastAPI Container') {
//             steps {
//                 sh '''
//                 docker rm -f usa-container || true
//                 docker run -d \
//                   --name usa-container \
//                   --network monitoring-network \
//                   -p 8000:8000 \
//                   ${FULL_IMAGE_NAME}
//                 '''
//             }
//         }

//         stage('Deploy Node Exporter') {
//             steps {
//                 sh '''
//                 docker rm -f node-exporter || true
//                 docker run -d \
//                   --name node-exporter \
//                   --network monitoring-network \
//                   -p 9100:9100 \
//                   prom/node-exporter
//                 '''
//             }
//         }

//         stage('Deploy Prometheus') {
//             steps {
//                 sh '''
//                 docker rm -f prometheus || true
//                 docker run -d \
//                   --name prometheus \
//                   --network monitoring-network \
//                   -p 9090:9090 \
//                   -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
//                   prom/prometheus
//                 '''
//             }
//         }

//         stage('Deploy Grafana') {
//             steps {
//                 sh '''
//                 docker rm -f grafana || true
//                 docker run -d \
//                   --name grafana \
//                   --network monitoring-network \
//                   -p 3000:3000 \
//                   grafana/grafana
//                 '''
//             }
//         }
//     }

//     post {
//         success {
//             echo "✅ Deployment Successful 🚀"
//         }
//         failure {
//             echo "❌ Pipeline Failed"
//         }
//     }
// }

//  train and deploy on specific ec2 machine
pipeline {
    agent any

    environment {
        AWS_REGION = "us-east-1"
        ECR_REPO = "usa-ml-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        ACCOUNT_ID = "440977420038"
        ECR_URI = "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        FULL_IMAGE_NAME = "${ECR_URI}/${ECR_REPO}:${IMAGE_TAG}"
        EC2_HOST = "ubuntu@100.27.209.28"
}
    

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-credentials',
                    url: 'https://github.com/DineshKalluri5296/USA_Housing.git'
            }
        }

        // ✅ Better Copy (Reliable)
        stage('Copy Code to EC2') {
           steps {
               sshagent(['ec2-key']) {
                   sh '''
                   echo "📁 Creating directory on EC2..."
                   ssh -o StrictHostKeyChecking=no ${EC2_HOST} "rm -rf /home/ubuntu/USA_Housing && mkdir -p /home/ubuntu/USA_Housing"

                   echo "📦 Copying files to EC2..."
                   scp -o StrictHostKeyChecking=no -r * ${EC2_HOST}:/home/ubuntu/USA_Housing/
                    '''
        }
    }
}

        // ✅ Train on EC2 (Fixed)
        stage('Train Model on EC2') {
            steps {
                sshagent(['ec2-key']) {
                    sh '''
                    ssh ${EC2_HOST} "
                        cd ~/USA_Housing

                        echo '📦 Installing dependencies...'
                        sudo apt update -y
                        sudo apt install -y python3-pip awscli

                        sudo pip3 install -r requirements.txt

                        echo '🔍 Checking model in S3...'
                        aws s3 ls s3://usa-ml-app1/models/latest/model.pkl >/dev/null 2>&1

                        if [ $? -eq 0 ]; then
                            echo '✅ Model exists. Skipping training.'
                        else
                            echo '🚀 Training model...'
                            python3 train.py

                            echo '📦 Uploading model...'
                            aws s3 cp model.pkl s3://usa-ml-app1/models/latest/model.pkl
                        fi
                    "
                    '''
                }
            }
        }

        // ✅ Build Image
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${FULL_IMAGE_NAME} .'
            }
        }

        // ✅ Login ECR
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

        // ✅ Push Image
        stage('Push Image to ECR') {
            steps {
                sh 'docker push ${FULL_IMAGE_NAME}'
            }
        }

        // ✅ Deploy App
        stage('Deploy on EC2') {
            steps {
                sshagent(['ec2-key']) {
                    sh '''
                    ssh ${EC2_HOST} "
                        echo '🚀 Logging into ECR...'
                        aws ecr get-login-password --region ${AWS_REGION} | \
                        sudo docker login --username AWS --password-stdin ${ECR_URI}

                        echo '📥 Pulling image...'
                        sudo docker pull ${FULL_IMAGE_NAME}

                        echo '🧹 Removing old container...'
                        sudo docker rm -f usa-container || true

                        echo '🌐 Creating network...'
                        sudo docker network inspect monitoring-network >/dev/null 2>&1 || \
                        sudo docker network create monitoring-network

                        echo '🚀 Starting container...'
                        sudo docker run -d \
                          --name usa-container \
                          --network monitoring-network \
                          -p 8000:8000 \
                          ${FULL_IMAGE_NAME}
                    "
                    '''
                }
            }
        }

        // ✅ Monitoring (Fixed Prometheus)
        stage('Deploy Monitoring (EC2)') {
            steps {
                sshagent(['ec2-key']) {
                    sh '''
                    ssh ${EC2_HOST} "
                        echo '📊 Deploying monitoring...'

                        sudo docker rm -f node-exporter prometheus grafana || true

                        sudo docker run -d \
                          --name node-exporter \
                          --network monitoring-network \
                          -p 9100:9100 \
                          prom/node-exporter

                        sudo docker run -d \
                          --name prometheus \
                          --network monitoring-network \
                          -p 9090:9090 \
                          -v ~/USA_Housing/prometheus.yml:/etc/prometheus/prometheus.yml \
                          prom/prometheus

                        sudo docker run -d \
                          --name grafana \
                          --network monitoring-network \
                          -p 3000:3000 \
                          grafana/grafana
                    "
                    '''
                }
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


