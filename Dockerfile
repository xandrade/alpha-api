# docker build -t api .
# docker run --name api-tcp5000 --restart unless-stopped -e PORT=5000 -e HOST="0.0.0.0" -p 5000:5000 -v "/mnt/d/Dropbox/Python Projects/alpha-api/db":"/usr/src/api/db" -d api 
# docker stop api-tcp5000 && docker rm api-tcp5000

# ---- Base Python ----
FROM python:3.10-slim-buster AS base

# Update image
RUN apt-get -y update  && \
    apt-get -y upgrade && \
    apt-get -y dist-upgrade && \
    apt-get install --no-install-recommends nano && \
    apt install -y gcc && \
    apt-get -y update && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR "/usr/src/api"

# ---- Virtual environment ---
ENV VIRTUAL_ENV=.venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# ---- Dependencies ----
COPY requirements.txt .

# Instal all dependencies
RUN pip install -U setuptools pip && \
    pip install --no-cache-dir -r requirements.txt && \ 
    rm ./requirements.txt

# ---- Copy Files/Build ----
COPY ./app/*.py /.


#HEALTHCHECK --interval=5m --timeout=3s \
#  CMD curl -f http://127.0.0.1:5000/health || exit 1


FROM python:3.10-slim as built

# Update image
RUN apt-get -y update  && \
    apt-get install --no-install-recommends nano && \
    rm -rf /var/lib/apt/lists/*

WORKDIR "/usr/src/api"
COPY --from=base /usr/src/api/ /.
ENV PATH=".venv/bin:$PATH"

# Switch to non-root user:
#RUN useradd --create-home afkar
#WORKDIR /home/appuser
#USER afkar

# Run the application:
#CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5000",  "main:app"]
#CMD ["python3", "main.py"]
CMD ["hypercorn", "--bind", "0.0.0.0:5000", "main:app", "-w", "1", "--worker-class", "uvloop"]