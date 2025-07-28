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
