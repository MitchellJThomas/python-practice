# The Toy Manifest Service

The service which supports uploading a set of layers in a specific
order and generating an ​OCI manifest​ when asked.

| Resource | Description |
| :--------- | :------------- |
| `GET /manifest/{manifest_id}` | Given a manifest_id in the form of a sha256 hash return the describing OCI manifest specification. |
| `POST /manifest` | Post your designed schema to this endpoint, afterwards a call to '/manifest/{manifest_id}'must return an OCI manifest specification for the given manifest hash. |
| `GET /layer/{layer_id}` |  Provides the layer contents in tar.gz format for the given layer id. The layers you will need to upload to your service ​can be found here​. |

## Requirements

### Mandatory

The minimum work required to satisfy

   - Choose Python or Go as the programming language for implementation.

   - The API endpoints above should work with a simple HTTP Client such
   as curl or Postman.

   - The service must work ephemerally, persisting necessary data structures in memory.

### Suggested

   - Use Postgres or MySQL to implement persistent storage. We should be
     able to restart your service and have it give repeatable responses.
 
   - Explain your database schema choices in either comments or prose.
 
   - Explain how you would change the schema after it has been defined,
    e.g add/remove/change columns with/without downtime to the service.
 
   - Use a migration script for each phase of the migration.

### Stretch

   - Implement http range requests for the "/layer" endpoints.

   - Design for scale and make this apparent with comments or prose.

   - Support ​manifest annotations​.

## Setup

Its default port is 4000.

Set up your environment:

1. Install Docker Desktop ([Mac](https://docs.docker.com/docker-for-mac/install/) or [Windows](https://docs.docker.com/docker-for-windows/install-windows-home/)) or [Docker Engine for Linux](https://docs.docker.com/engine/install/#server)
1. Install make
1. Run `make run`

## Building

Run `make build`

## Testing

Run `make test`

## Committing changes

1. Ensure pre-commit tool is installed e.g. `pipx install pre-commit`
1. Ensure pre-commit hooks are installed e.g. `pre-commit install`
1. Run `pre-commit run -a` to check all the things
1. Create a concise description of the changes and commit!

## Clean up

Run `make clean`
