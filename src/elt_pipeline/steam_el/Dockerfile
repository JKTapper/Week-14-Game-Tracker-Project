FROM public.ecr.aws/lambda/python:3.12
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY src/elt_pipeline/steam_el/ ${LAMBDA_TASK_ROOT}/


CMD ["lambda.handler"]



