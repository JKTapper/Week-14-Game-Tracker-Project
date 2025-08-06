provider "aws" {
  region = "eu-west-2"
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
  function_name = "c18-game-tracker-el-lambda"
  package_type  = "Image"
  image_uri     = var.lambda_image_uri
  role          = aws_iam_role.lambda_exec_role_game_tracker_el.arn
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }
}

# Schedule (every hour)
resource "aws_cloudwatch_event_rule" "hourly" {
  name                = "c18-game-tracker-lambda-el-hourly-schedule"
  schedule_expression = "cron(0 * * * ? *)"
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


# tl lambda
resource "aws_lambda_function" "docker_lambda_tl" {
  function_name = "c18-game-tracker-tl-lambda"
  package_type  = "Image"
  image_uri     = var.lambda_image_uri_tl
  role          = aws_iam_role.lambda_exec_role_game_tracker_el.arn
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      LOG_LEVEL         = "INFO"
      DATABASE_IP       = var.DATABASE_IP
      DATABASE_PORT     = var.DATABASE_PORT
      DATABASE_USERNAME = var.DATABASE_USERNAME
      DATABASE_PASSWORD = var.DATABASE_PASSWORD
      DATABASE_NAME     = var.DATABASE_NAME
      DB_SCHEMA         = "public"
    }
  }
}


resource "aws_cloudwatch_event_rule" "tl_schedule" {
  name                = "c18-game-tracker-lambda-tl-schedule"
  schedule_expression = "cron(30 * * * ? *)"
}

resource "aws_lambda_permission" "tl_permission" {
  statement_id  = "AllowExecutionFromEventBridgetl"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.docker_lambda_tl.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.tl_schedule.arn
}

resource "aws_cloudwatch_event_target" "tl_target" {
  rule      = aws_cloudwatch_event_rule.tl_schedule.name
  target_id = "lambda-tl"
  arn       = aws_lambda_function.docker_lambda_tl.arn
}


# Existing data
data "aws_ecs_cluster" "existing" {
  cluster_name = var.ecs-cluster-name
}
data "aws_ecr_repository" "repo" {
  name = var.ecr_repo_name
}
data "aws_vpc" "c18-vpc" {
  id = "vpc-0adcb6a62ca552c01"
}
data "aws_subnet" "public_1" {
  id = "subnet-0679d4b1f9e7839ef"
}
data "aws_subnet" "public_2" {
  id = "subnet-0f10662561eade8c3"
}
data "aws_subnet" "public_3" {
  id = "subnet-0aed07ac008a10da9"
}

# ECS security group and rules
resource "aws_security_group" "ecs_sg" {
  name        = "c18-game-tracker-ecs-sg"
  description = "Allows all outbound traffic from ECS."
  vpc_id      = data.aws_vpc.c18-vpc.id
}

resource "aws_vpc_security_group_egress_rule" "allow_all" {
  security_group_id = aws_security_group.ecs_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "allow_all_in" {
  security_group_id = aws_security_group.ecs_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# Cloudwatch log group
resource "aws_cloudwatch_log_group" "game-tracker-logs" {
  name              = "/ecs/c18-game-tracker-dashboard-task"
  retention_in_days = 7
}

# Task definition
resource "aws_ecs_task_definition" "service" {
  family                   = "c18-game-tracker-dashboard-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  task_role_arn            = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([
    {
      name      = "c18-game-tracker-dashboard"
      image     = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c18-game-tracker-ecr:dashboard"
      cpu       = 256
      memory    = 1024
      essential = true
      environment = [
        { name = "DB_HOST", value = var.DB_HOST },
        { name = "DB_PORT", value = var.DB_PORT },
        { name = "DB_USER", value = var.DB_USER },
        { name = "DB_PASSWORD", value = var.DB_PASSWORD },
        { name = "DB_NAME", value = var.DB_NAME },
        { name = "DB_SCHEMA", value = var.DB_SCHEMA }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/c18-game-tracker-dashboard-task"
          awslogs-region        = "eu-west-2"
          awslogs-stream-prefix = "etl"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "dashboard_service" {
  name            = "c18-game-tracker-dashboard-service"
  cluster         = data.aws_ecs_cluster.existing.id
  task_definition = aws_ecs_task_definition.service.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets = [
      data.aws_subnet.public_1.id,
      data.aws_subnet.public_2.id,
      data.aws_subnet.public_3.id
    ]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  depends_on = [aws_ecs_task_definition.service]
}




# CloudWatch Logs
resource "aws_cloudwatch_log_group" "form_app_logs" {
  name              = "/ecs/c18-game-tracker-form-app"
  retention_in_days = 7
}

resource "aws_iam_policy" "ses_verify_email_policy" {
  name        = "SESVerifyEmailPolicy"
  description = "Allow ECS tasks to verify emails using SES"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ses:VerifyEmailIdentity",
          "ses:GetIdentityVerificationAttributes"
        ],
        Resource = "*"
      }
    ]
  })
}
data "aws_iam_role" "ecs_task_execution" {
  name = "ecsTaskExecutionRole"
}

resource "aws_iam_role_policy_attachment" "attach_ses_policy_to_external_role" {
  role       = data.aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.ses_verify_email_policy.arn
}



# ECS Task Definition for Flask Form App
resource "aws_ecs_task_definition" "form_app_task" {
  family                   = "c18-game-tracker-form-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  task_role_arn            = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "c18-game-tracker-form-app"
      image     = "${data.aws_ecr_repository.repo.repository_url}:form"
      cpu       = 256
      memory    = 1024
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "DB_HOST", value = var.DB_HOST },
        { name = "DB_PORT", value = var.DB_PORT },
        { name = "DB_USERNAME", value = var.DB_USER },
        { name = "DB_PASSWORD", value = var.DB_PASSWORD },
        { name = "DB_NAME", value = var.DB_NAME },
        { name = "DB_SCHEMA", value = var.DB_SCHEMA }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/c18-game-tracker-form-app"
          awslogs-region        = "eu-west-2"
          awslogs-stream-prefix = "form"
        }
      }
    }
  ])
}

# ECS Service for Flask Form App
resource "aws_ecs_service" "form_app_service" {
  name            = "c18-game-tracker-form-app-service"
  cluster         = data.aws_ecs_cluster.existing.id
  task_definition = aws_ecs_task_definition.form_app_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets = [
      data.aws_subnet.public_1.id,
      data.aws_subnet.public_2.id,
      data.aws_subnet.public_3.id
    ]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  depends_on = [aws_ecs_task_definition.form_app_task]
}


# Daily emails lambda
resource "aws_lambda_function" "daily_email" {
  function_name = "c18-game-tracker-noti-sender"
  # re-used role

  role = aws_iam_role.lambda_exec_role_game_tracker_el.arn

  package_type = "Image"
  image_uri    = var.lambda_image_uri_notification

  timeout     = 60
  memory_size = 256

  environment {
    variables = {
      DB_HOST     = var.DB_HOST
      DB_PORT     = var.DB_PORT
      DB_USERNAME = var.DB_USER
      DB_PASSWORD = var.DB_PASSWORD
      DB_NAME     = var.DB_NAME
      DB_SCHEMA   = var.DB_SCHEMA
    }
  }
}

resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "c18-game-tracker-daily-noti-schedule"
  schedule_expression = "cron(0 11 * * ? *)" # Every day at noon BST
}

resource "aws_cloudwatch_event_target" "lambda_target_daily_email" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "lambda-daily-email"
  arn       = aws_lambda_function.daily_email.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.daily_email.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
}

# Adding SES permissions
resource "aws_iam_policy" "ses_send_email_policy" {
  name        = "game-tracker-ses-send-email"
  description = "Allow Lambda to send email via SES"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_ses_attachment" {
  role       = aws_iam_role.lambda_exec_role_game_tracker_el.name
  policy_arn = aws_iam_policy.ses_send_email_policy.arn
}
