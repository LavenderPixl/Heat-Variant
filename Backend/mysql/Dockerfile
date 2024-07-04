FROM mysql:8.0-debian

RUN apt-get update && apt-get -y install cron

# Add test-cron file in the cron directory
ADD crontab/test-cron /etc/cron.d/test-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/test-cron

# Apply cron job
RUN cron /etc/cron.d/test-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
RUN cron

CMD /usr/sbin/mysqld -u mysql