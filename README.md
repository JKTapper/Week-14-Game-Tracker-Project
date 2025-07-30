# Week-14-Game-Tracker-Project

(Unofficial docs for requesting more data for a given store page App ID)[https://github.com/Revadike/InternalSteamWebAPI/wiki/Get-App-Details]

### Commands

To build and push docker image for EL pipeline you will first need to authenticate (use your account id can be found on top-right of AWS console):
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com

And then to build and push image to ecr:
docker buildx build --platform linux/amd64 --provenance=false -f src/elt_pipeline/steam_el/Dockerfile -t ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/c18-game-tracker-ecr:el --push .
