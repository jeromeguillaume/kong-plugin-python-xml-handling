# docker build -t kong-gateway-xml-handling .
# Ko (ALPINE) -> FROM kong/kong-gateway:3.1.1.1-alpine (crit] 2168#0: *907 connect() to unix:/usr/local/kong/python_pluginserver.sock failed (2: No such file or directory), context: ngx.timer)
# Ko (ALPINE) -> FROM kong/kong-gateway:3.1.0.0-alpine **** same error as above ****
# Ok (ALPINE) -> FROM kong/kong-gateway:3.0.2.0-alpine
# Ok (ALPINE) -> FROM kong/kong-gateway:3.0.0.0-alpine
# Ok (ALPINE) -> FROM kong/kong-gateway:2.8.2.2
# Ko (DEBIAN) -> FROM kong/kong-gateway:3.1.1.1

FROM kong/kong-gateway:arm64-3.0.2.0-alpine
USER root

# ALPINE
RUN apk update && \
    apk add python3 py3-pip python3-dev musl-dev libffi-dev gcc g++ file make
RUN PYTHONWARNINGS=ignore pip3 install kong-pdk lxml

# DEBIAN
#RUN apt-get update && \
#    apt-get install -y python3 python3-pip python3-dev musl-dev libffi-dev gcc g++ file make && \
#    PYTHONWARNINGS=ignore pip3 install kong-pdk

# COPY /plugins/xml-transform.py /usr/local/kong/python/

# reset back the defaults
USER kong
ENTRYPOINT ["/docker-entrypoint.sh"]
STOPSIGNAL SIGQUIT
HEALTHCHECK --interval=10s --timeout=10s --retries=10 CMD kong health
CMD ["kong", "docker-start"]
