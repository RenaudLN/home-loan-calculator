FROM python:3.10-slim-buster

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install package and its dependencies.
RUN pip install --no-cache-dir .

CMD gunicorn --timeout 0 loan_calculator.application:server
