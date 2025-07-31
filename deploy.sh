# Command to build and push docker image to ecr
# Must be run at root of repo
# Use bash deploy.sh path-to-dockerfile-from-root image-tag
# e.g   bash deploy.sh src/elt/pipeline/steam_el/Dockerfile latest


aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 129033205317.dkr.ecr.eu-west-2.amazonaws.com

docker buildx build --platform linux/amd64 --provenance=false -f $1 -t 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c18-game-tracker-ecr:$2 --push .