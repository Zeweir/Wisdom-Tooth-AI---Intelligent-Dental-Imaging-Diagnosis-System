FROM python:3.12-slim-bookworm

WORKDIR /app

ARG APT_MIRROR=http://deb.debian.org/debian
ARG APT_SECURITY_MIRROR=http://security.debian.org/debian-security
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_EXTRA_INDEX_URL=
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_DEFAULT_TIMEOUT=120
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
ENV TORCH_INDEX_URL=${TORCH_INDEX_URL}

RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "60";\nAcquire::https::Timeout "60";\n' > /etc/apt/apt.conf.d/80-retries
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i "s|http://deb.debian.org/debian|${APT_MIRROR}|g; s|http://security.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && if [ -f /etc/apt/sources.list ]; then \
        sed -i "s|http://deb.debian.org/debian|${APT_MIRROR}|g; s|http://security.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" /etc/apt/sources.list; \
    fi
RUN for attempt in 1 2 3 4 5; do \
        apt-get update \
        && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
        && break; \
        apt-get clean; \
        rm -rf /var/lib/apt/lists/*; \
        echo "apt install failed, retrying (${attempt}/5)"; \
        sleep 5; \
    done \
    && dpkg --configure -a \
    && apt-get install -f -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --index-url "${TORCH_INDEX_URL}" \
    torch==2.5.1+cpu torchvision==0.20.1+cpu
RUN if [ -n "${PIP_EXTRA_INDEX_URL}" ]; then \
        pip install --no-cache-dir --index-url "${PIP_INDEX_URL}" --extra-index-url "${PIP_EXTRA_INDEX_URL}" -r requirements.txt; \
    else \
        pip install --no-cache-dir --index-url "${PIP_INDEX_URL}" -r requirements.txt; \
    fi

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
