FROM mambaorg/micromamba:0.22.0 as builder

### To be used preferentially to get dependencies from conda-forge rather than pipy
# COPY --chown=$MAMBA_USER:$MAMBA_USER conda-linux-64.lock /locks/conda-linux-64.lock
# RUN micromamba install --name base --yes --file /locks/conda-linux-64.lock && \
#     micromamba clean --all --yes

# Otherwise, just install python 3.9
RUN micromamba install --yes --name base --channel conda-forge python=3.9 && \
    micromamba clean --all --yes

### Install keyring package required to connect to private pypi repository
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir keyrings.google-artifactregistry-auth

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install package and its dependencies.
ARG GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/GAUTH
ARG PIP_EXTRA_INDEX_URL
RUN --mount=type=secret,id=GAUTH,uid=1000 pip install --no-cache-dir . --extra-index-url $PIP_EXTRA_INDEX_URL

CMD gunicorn -b :8080 --workers 3 --timeout 0 sample_dash_app.application:server

### Use a distroless container as primary container
# FIXME: this does not work currently bitbucket pipeline due to user mapping issues
# FROM gcr.io/distroless/base-debian10
# COPY --from=builder /opt/env /opt/env
# ENTRYPOINT [ "opt/env/bin/gunicorn", "-b", ":8080", "--workers", "3", "--timeout", "0", "sample_dash_app.application:server" ]
