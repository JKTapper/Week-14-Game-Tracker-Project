output "rds_endpoint" {
  value = aws_db_instance.c18-game-tracker-rds.endpoint
}

output "rds_db_name" {
  value = aws_db_instance.c18-game-tracker-rds.identifier
}
