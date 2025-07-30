output "rds_endpoint" {
  value = aws_db_instance.c18-game-tracker-rds.endpoint
}

output "rds_db_name" {
  value = aws_db_instance.c18-game-tracker-rds.identifier
}

output "ecr_repository_url" {
  value = aws_ecr_repository.c18_game_tracker_repo.repository_url
}
