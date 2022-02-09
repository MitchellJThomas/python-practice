FROM python:3.9-alpine3.15
RUN addgroup -g 2000 yt && \
    adduser -S -u 2000 -G yt yt

COPY --from=toy-manifest-service-builder /build /build
ENV PATH /build/.venv/bin:$PATH

WORKDIR /code

COPY src/ /code/
RUN python -m compileall -q /code/

# COPY build/version /code/

USER yt:yt

EXPOSE 4000

CMD ["python", "main.py"]
