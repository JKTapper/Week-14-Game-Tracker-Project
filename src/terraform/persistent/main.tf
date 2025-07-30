provider "aws" {
  region = var.aws_region
}

# Create a security group to allow access to RDS
resource "aws_security_group" "rds_sg" {
  name        = "rds-postgres-sg"
  description = "Allow PostgreSQL access"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "c18-game-tracker-subnet"
  subnet_ids = var.subnet_ids
}

# Create the PostgreSQL DB
resource "aws_db_instance" "c18-game-tracker-rds" {
  identifier             = var.db_name
  engine                 = "postgres"
  engine_version         = 17.5
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  username               = var.db_username
  password               = var.db_password
  port                   = 5432
  publicly_accessible    = true
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  skip_final_snapshot    = true
}


resource "aws_s3_bucket" "c18-game-tracker-s3" {
  bucket = "c18-game-tracker-s3"
}

# ECR Repository
resource "aws_ecr_repository" "c18_game_tracker_repo" {
  name                 = "c18-game-tracker-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}


# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role_game_tracker_el" {
  name = "lambda_exec_role_game_tracker_el"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

# IAM Policy (CloudWatch Logs + S3)
resource "aws_iam_policy" "lambda_policy" {
  name = "lambda_basic_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_exec_role_game_tracker_el.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Lambda Function from ECR
resource "aws_lambda_function" "docker_lambda" {
  function_name = "el-lambda"
  package_type  = "Image"
  image_uri     = var.lambda_image_uri
  role          = aws_iam_role.lambda_exec_role_game_tracker_el.arn

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }
}

# Schedule (every hour)
resource "aws_cloudwatch_event_rule" "hourly" {
  name                = "lambda-hourly-schedule"
  schedule_expression = "rate(1 hour)"
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_event" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.docker_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly.arn
}

# EventBridge Target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.hourly.name
  target_id = "lambda"
  arn       = aws_lambda_function.docker_lambda.arn
}
