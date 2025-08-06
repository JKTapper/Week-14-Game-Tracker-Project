variable "lambda_image_uri" {
  description = "ECR image URI"
}
variable "lambda_image_uri_tl" {
  description = "ECR image tl URI"
}
variable "lambda_image_uri_notification" {
  description = "ECR image noti URI"
}
variable "lambda_image_el_epic_uri" {
  description = "ECR image el epic URI"
}

variable "lambda_image_el_gog_uri" {
  description = "ECR image el gog URI"
}

variable "lambda_image_uri_summary" {
  description = "ECR image summary"
}


variable "ecr_repo_name" {
  default     = "c18-game-tracker-ecr"
  description = "ecr repo name"
}
variable "image_tag" {
  default     = "dashboard"
  description = "Docker tag"
}

variable "ecs-cluster-name" {
  default = "streamlit-cluster"
}

variable "DATABASE_IP" {
  description = "IP to access the RDS"
  type        = string
}
variable "DATABASE_PORT" {
  description = "Port for Postgres"
  type        = string
}
variable "DATABASE_USERNAME" {
  description = "Group-specific username for RDS"
  type        = string
}
variable "DATABASE_PASSWORD" {
  description = "Group-specific password for RDS"
  type        = string
}
variable "DATABASE_NAME" {
  description = "Database name for RDS"
  type        = string
}
variable "DB_SCHEMA" {
  description = "Group-specific schema for RDS"
  type        = string
}

variable "DB_HOST" {
  description = "IP to access the RDS"
  type        = string
}
variable "DB_PORT" {
  description = "Port for Postgres"
  type        = string
}
variable "DB_USER" {
  description = "Group-specific username for RDS"
  type        = string
}
variable "DB_PASSWORD" {
  description = "Group-specific password for RDS"
  type        = string
}

variable "DB_NAME" {
  description = "Database name for RDS"
  type        = string
}
