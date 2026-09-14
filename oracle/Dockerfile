# syntax=docker/dockerfile:1@sha256:ecfaec9ed6d810b56388c508f4121597bfbba70d41a6dfeee4d8cad5f295fc32

FROM rocker/r-ver:4.5.1@sha256:03b023fbf7b1b24ac1bb8b2ac5fd7e15a767e67b40ff50c155e328110981c2aa

ARG GGSTATSPLOT_REVISION=7a724cd0ab55668b9d0b2e84b12c711c5be68ac8

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        cmake \
        gfortran \
        git \
        libcurl4-openssl-dev \
        libfontconfig1-dev \
        libfreetype6-dev \
        libfribidi-dev \
        libharfbuzz-dev \
        libicu-dev \
        libjpeg-dev \
        libgmp3-dev \
        libgsl-dev \
        libmpfr-dev \
        libpng-dev \
        libssl-dev \
        libtiff-dev \
        libxml2-dev \
        pandoc \
        pari-gp \
    && rm -rf /var/lib/apt/lists/*

ENV GGSTATSPLOT_REVISION=${GGSTATSPLOT_REVISION}
COPY oracle/DESCRIPTION oracle/renv.lock /oracle/
RUN --mount=type=cache,target=/root/.cache/R/renv \
    Rscript -e 'options(pkgType = "source", warn = 2); install.packages("https://github.com/rstudio/renv/archive/f98afd8becc4fc7453837ebf14a6ee0ab74faec1.tar.gz", repos = NULL, type = "source"); stopifnot(as.character(packageVersion("renv")) == "1.2.4")' \
    && Rscript -e 'options(repos = c(CRAN = "https://cloud.r-project.org"), pkgType = "source", warn = 2); renv::restore(project = "/oracle", lockfile = "/oracle/renv.lock", library = "/usr/local/lib/R/site-library", prompt = FALSE); metadata <- packageDescription("ggstatsplot"); stopifnot(identical(metadata$RemoteSha, Sys.getenv("GGSTATSPLOT_REVISION")))'

WORKDIR /work
ENTRYPOINT ["Rscript", "/work/oracle/generate.R"]
