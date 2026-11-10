FROM tiangolo/uwsgi-nginx-flask:python3.12
ENV LISTEN_PORT 8080
EXPOSE 8080
COPY ./requirements.txt /app/requirements.txt
# requirements.txt is a complete pinned lockfile; --no-deps installs it verbatim
# so a transitive's stale upper cap (iiif-prezi3 3.1.1 pins Pillow<=12.0.0) cannot
# block the security bump to Pillow 13. See requirements.txt / PR for rationale.
RUN pip install --no-cache-dir --no-deps --upgrade -r /app/requirements.txt
COPY . /app

CMD /app/start.sh
