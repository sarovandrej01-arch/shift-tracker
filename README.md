# shift-tracker

## Local infrastructure

```bash
docker compose up -d
docker compose ps
docker compose down
```

PostgreSQL: `localhost:5432`  
MinIO S3 API: `localhost:9000`  
MinIO Console: `localhost:9001`

`docker compose down` keeps the named volumes. `docker compose down -v` deletes PostgreSQL and MinIO data.

When the backend runs on the host, use `S3_ENDPOINT_URL=http://localhost:9000`. If the backend later runs inside Compose, that URL must point at the `minio` service. A presigned URL built from the internal hostname will not open in a browser; a separate public endpoint can be added later.
