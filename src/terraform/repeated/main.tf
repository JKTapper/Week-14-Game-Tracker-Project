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


# LT lambda
resource "aws_lambda_function" "docker_lambda_lt" {
  function_name = "c18-game-tracker-lt-lambda"
  package_type  = "Image"
  image_uri     = var.lambda_image_uri # Assumes same image
  role          = aws_iam_role.lambda_exec_role_game_tracker_el.arn
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      LOG_LEVEL   = "INFO"
      DB_HOST     = var.DB_HOST
      DB_PORT     = var.DB_PORT
      DB_USER     = var.DB_USER
      DB_PASSWORD = var.DB_PASSWORD
      DB_NAME     = var.DB_NAME
      DB_SCHEMA   = "public"
    }
  }
}


resource "aws_cloudwatch_event_rule" "lt_schedule" {
  name                = "c18-game-tracker-lambda-lt-schedule"
  schedule_expression = "cron(30 * * * ? *)"
}

resource "aws_lambda_permission" "lt_permission" {
  statement_id  = "AllowExecutionFromEventBridgeLT"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.docker_lambda_lt.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lt_schedule.arn
}

resource "aws_cloudwatch_event_target" "lt_target" {
  rule      = aws_cloudwatch_event_rule.lt_schedule.name
  target_id = "lambda-lt"
  arn       = aws_lambda_function.docker_lambda_lt.arn
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
