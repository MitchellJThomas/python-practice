# A basic tool to discover mDNS / Bonjour systems

Ever wonder what's on your network? mDNS is often used as a service/device discovery tool e.g. [Sonos devices](https://www.sonos.com/en-us/home) and the Sonos iOS App. It uses mDNS to discover what Sonos players are installed on your network.

## Setup

1. Install Python 3.9.  I use pyenv to install different non-system Python interpreters e.g. `pyenv install 3.9`
1. Install pipenv e.g. `pip install pipenv`
1. Install the dependencies in this directory `pipenv install`
1. Run the scripts `pipenv run python list.py`
