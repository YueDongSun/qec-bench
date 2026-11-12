FROM python:3.11.18-slim-bookworm

# Pinned to pyproject.toml and uv.lock. Packages are installed at build time.
# No network at test time.
RUN pip install --no-cache-dir \
    stim==1.16.0 \
    pymatching==2.4.0 \
    mitiq==1.1.0 \
    cirq-core==1.6.1 \
    numpy==2.2.6 \
    scipy==1.17.1 \
    pytest==9.2.0
