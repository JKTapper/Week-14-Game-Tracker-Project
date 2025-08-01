variable "lambda_image_uri" {
  description = "ECR image URI"
}
variable "lambda_image_uri_tl" {
  description = "ECR image tl URI"
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
variable "DB_SCHEMA" {
  description = "Group-specific schema for RDS"
  type        = string
}
