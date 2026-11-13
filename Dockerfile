FROM python:3.12-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install TeX Live and fonts required by template
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    lmodern \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY api.py build_resume.py ./

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT} --timeout 60 api:app"]
