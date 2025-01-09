FROM tiangolo/uwsgi-nginx-flask:python3.12
ENV LISTEN_PORT 8080
EXPOSE 8080
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY . /app

CMD /app/start.sh
