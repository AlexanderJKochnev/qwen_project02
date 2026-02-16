FROM edoburu/pgbouncer:latest

# Копируем конфиги с правильными правами
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY userlist.txt /etc/pgbouncer/userlist.txt

# Убеждаемся, что права правильные
RUN chmod 644 /etc/pgbouncer/userlist.txt && \
    chmod 644 /etc/pgbouncer/pgbouncer.ini

EXPOSE 6432