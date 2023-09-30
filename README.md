# Catline

Catline (short for "cat outline") is an [Outline VPN](https://getoutline.org/) client provisioning script.

This script uses the [outline server API](https://github.com/Jigsaw-Code/outline-server/tree/master/src/shadowbox/server/api.yml).

It ensures that for a given list of clients and a given list of servers, each client has an access key provisioned on each server, and then print out keys for all clients on all servers.

[Prefix for TLS client hello](https://old.reddit.com/r/outlinevpn/wiki/index/prefixing) is attached to all access keys to improve resistance to DPI.

[Dynamic access](https://old.reddit.com/r/outlinevpn/wiki/index/dynamic_access_keys) keys may be used as an alternative to this script.

## Usage

* Check the comment at the top of `provision.py` for the format to create the `clients.json` and `servers.json` files, containing your servers API URLs and client names.
* Create a virtual environment and install the `requests` dependency.
* Run `python3 provision.py`, repeat when you need to change servers or clients.

## Caution

Do not run this script from within censored or untrusted networks, as this script does not currently pin the self-signed certificates of the Outline APIs due to a bug of requests / urllib validating them, therefore it is vulnerable to MITM attacks.

## Disclaimer

At the time of writing I am a Google employee, but not part of the team maintaining Outline. This script is shared in a personal capacity only, it is not a Google product and not in any way endorsed by Google.
