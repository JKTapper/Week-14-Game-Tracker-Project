# Command to build and push docker image to ecr
# Must be run at root of repo
# Use `bash src/elt_pipeline/steam_tl/deploy.sh`

aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 129033205317.dkr.ecr.eu-west-2.amazonaws.com

docker buildx build --platform linux/amd64 --provenance=false -f src/elt_pipeline/steam_tl/dockerfile -t 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c18-game-tracker-ecr:tl --push .