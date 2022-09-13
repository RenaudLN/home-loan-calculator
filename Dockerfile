FROM python:3.10-slim-buster

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install package and its dependencies.
RUN pip install --no-cache-dir .

CMD gunicorn -b :8080 --workers 3 --timeout 0 sample_dash_app.application:server
