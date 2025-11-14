pipeline {
    agent {
        docker {
            image 'python:3.10'
            args '-v /var/run/mysql/mysql.sock:/var/run/mysqld/mysqld.sock'
        }
    }

    environment {
        DB_HOST = 'localhost'
        DB_USER = 'root'
        DB_PASSWORD = 'root'
        DB_NAME = 'test_isd'
        APP_SECRET_KEY = 'test-secret-key'
    }

    stages {
        stage('Setup') {
            steps {
                sh 'apt-get update && apt-get install -y default-mysql-client'
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest pytest-cov safety bandit'
            }
        }

        stage('Test Database Setup') {
            steps {
                sh '''
                    mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS test_isd;"
                    mysql -u root -proot test_isd -e "
                    CREATE TABLE IF NOT EXISTS admin (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        Username VARCHAR(255) UNIQUE,
                        Email VARCHAR(255) UNIQUE,
                        Password VARCHAR(255)
                    );
                    CREATE TABLE IF NOT EXISTS car (
                        Car_plate VARCHAR(20) PRIMARY KEY,
                        Model VARCHAR(255),
                        Year INT,
                        VIN VARCHAR(255),
                        Next_Oil_Change DATE,
                        Owner_id INT
                    );
                    CREATE TABLE IF NOT EXISTS appointment (
                        Appointment_id INT AUTO_INCREMENT PRIMARY KEY,
                        Date DATE,
                        Time TIME,
                        Notes TEXT,
                        Car_plate VARCHAR(20),
                        FOREIGN KEY (Car_plate) REFERENCES car(Car_plate)
                    );
                    CREATE TABLE IF NOT EXISTS service (
                        Service_ID INT AUTO_INCREMENT PRIMARY KEY,
                        Service_Type VARCHAR(255)
                    );
                    CREATE TABLE IF NOT EXISTS appointment_service (
                        Appointment_id INT,
                        Service_ID INT,
                        PRIMARY KEY (Appointment_id, Service_ID),
                        FOREIGN KEY (Appointment_id) REFERENCES appointment(Appointment_id),
                        FOREIGN KEY (Service_ID) REFERENCES service(Service_ID)
                    );
                    INSERT IGNORE INTO service (Service_Type) VALUES 
                    ('Oil Change'), 
                    ('Tire Rotation'), 
                    ('Brake Inspection'), 
                    ('Battery Check');
                    "
                '''
            }
        }

        stage('Test') {
            steps {
                sh 'pytest tests/ -v --cov=. --cov-report=xml --cov-report=html'
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                    cobertura autoUpdateHealth: false, 
                              autoUpdateStability: false, 
                              coberturaReportFile: 'coverage.xml', 
                              conditionalCoverageTargets: '70, 0, 0', 
                              failUnhealthy: false, 
                              failUnstable: false, 
                              lineCoverageTargets: '80, 0, 0', 
                              maxNumberOfBuilds: 0, 
                              methodCoverageTargets: '80, 0, 0', 
                              onlyStable: false, 
                              sourceEncoding: 'ASCII', 
                              zoomCoverageChart: false
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh 'safety check'
                sh 'bandit -r . -f html -o security-report.html'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'security-report.html',
                    reportName: 'Security Report'
                ])
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh 'echo "Deploying to production..."'
                // Add deployment commands
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}