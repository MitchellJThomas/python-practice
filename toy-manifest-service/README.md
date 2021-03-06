# The Toy Manifest Service

The service which supports uploading a set of layers in a specific order and generating an ​[OCI manifest](https://github.com/opencontainers/image-spec/blob/master/manifest.md)​ when asked.

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
     - Discussion points:
       - Single partitioned table
         - Partitioned by time to allow simpler age-out/storage management
         - Partitioned by time for performance (maybe). Assumption
            last few months of images are "popular", assumes frequently updated
            images. Caching choices and retention guarantees may lead
            to interesting design choices
       - Using JSONB type for URLs and annotations
          - Query performance of JSONB TBD
          - Accomodate highly variable key/value space
       - Inefficiences (maybe): redundant manifest config info
       - No ORM, learn Postgres and SQL-isms
         - Reduce code dependencies, fewer security issues
         - Reduce code paths, simpler to debug issues
 
   - Explain how you would change the schema after it has been defined, e.g add/remove/change columns with/without downtime to  the service.
     - Discussion points:
       - Establish uptime guarantees/contract to understand schema
            change requirements
       - Obvious but usually under-invested: ensure of a reliable
            archive/restore process
       - New columns with no dependency on existing data are simple
            with some caviates (valid column names, database resources
            etc.)
       - Changing a column name... do this rarely if ever.  This
            requires code to manange the transition from the old name
            the new with the new run-time.
            Removing old column names could be
            performed when the partition sub-tables and the associated
            indexes are dropped after aging out.
       - To remove columns, see changing column names as this is
            essentially the same as a column name change from something
            to nothing.
       - Use a migration script for each phase of the migration. In this
            implementation I use https://github.com/sqitchers/sqitch to
            manage the schema changes.

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

## Coding 

1. [Install python](https://www.python.org/downloads/)... your system
   may already have Python installed
1. [Install pyenv](https://github.com/pyenv/pyenv) helpful when new
   versions of python become available
1. Install python 3.8 using pyenv e.g. `pyenv install 3.8.5`
1. [Install pipenv](https://pipenv.pypa.io/en/latest/install/)
1. Run `pipenv install` to install python dependencies


### Updating Python dependencies

1. Run `pipenv update`

Sometimes you may need to remove the Pipfile.lock and then run `pipenv install`

### Committing changes

1. Ensure pre-commit tool is installed e.g. `pipx install pre-commit`
1. Ensure pre-commit hooks are installed e.g. `pre-commit install`
1. Run `pre-commit run -a` to check all the things
1. Create a concise description of the changes and commit!

## Clean up

Run `make clean`


## Notes

Interesting links

1. https://github.com/vsoch/oci-python
1. https://jessewarden.com/2020/03/write-unbreakable-python.html
