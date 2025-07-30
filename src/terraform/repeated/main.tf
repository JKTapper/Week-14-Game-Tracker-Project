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
