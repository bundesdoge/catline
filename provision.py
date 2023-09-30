# Outline VPN client provisioning script
#
# This script uses the outline server API below:
# https://github.com/Jigsaw-Code/outline-server/master/src/shadowbox/server/api.yml
#
# It ensures that for a given list of clients and a given list of servers,
# each client has an access key provisioned on each server, and then print
# out keys for all clients on all servers.
#
# Prefix for TLS client hello is attached to all access keys to improve
# resistance to DPI (https://old.reddit.com/r/outlinevpn/wiki/index/prefixing).
#
# Dynamic access keys may be used as an alternative to this script.
# https://old.reddit.com/r/outlinevpn/wiki/index/dynamic_access_keys

import os
import sys
import requests
import json

_TIMEOUT_SECONDS = 5
_URI_ENCODED_PREFIX = "%16%03%01%40%00%01"

# Server names and API URLs to be added in a new file servers.json, in the format of:
# {
#    "ServerA": "https://1.2.3.4:51234/xyz_ABCDEF1234",
#    "ServerB": "https://5.6.7.8:55678/zyx_HIJKLM5678"
# }
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "servers.json"), "r") as f:
    servers = json.loads(f.read())

# Client names to be added in a new file clients.json, in the format of:
# ["ClientNameA", "ClientNameB"]
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "clients.json"), "r") as f:
    clients = json.loads(f.read())


def get_certificate(server_name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, "certificates", "{}.pem".format(server_name))


def check_server_alive(server_name, server_api):
    # TODO: urllib is not verifying self-signed certificates by outline correctly
    # These certificates use CN rather than IP SAN, which causes validations to fail.
    # r = requests.get("{}/server".format(server_api),
    #                  timeout=_TIMEOUT_SECONDS, verify=get_certificate(server_name))
    r = requests.get("{}/server".format(server_api),
                     timeout=_TIMEOUT_SECONDS, verify=False)
    if r.status_code == 200:
        return r.json()
    r.raise_for_status()


def list_access_keys(server_name, server_api):
    r = requests.get("{}/access-keys".format(server_api),
                     timeout=_TIMEOUT_SECONDS, verify=False)
    if r.status_code != 200:
        r.raise_for_status()
    return r.json()


def create_access_key(server_name, server_api, client_name):
    r = requests.post("{}/access-keys".format(server_api),
                      timeout=_TIMEOUT_SECONDS, verify=False)
    if r.status_code != 200:
        r.raise_for_status()

    rsp = r.json()
    if 'accessUrl' not in rsp:
        raise ValueError("expected accessUrl or id not found when creating key for client {} in {}".format(
            client_name, server_name))

    id = rsp['id']
    url = rsp['accessUrl']

    r = requests.put("{}/access-keys/{}/name".format(server_api, id),
                     json={'name': client_name}, timeout=_TIMEOUT_SECONDS, verify=False)
    if r.status_code != 200:
        r.raise_for_status()
    return url


def add_prefix(access_url):
    return access_url.strip() + "&prefix={}".format(_URI_ENCODED_PREFIX)


all_servers_alive = True
for server_name, server_api in servers.items():
    if not check_server_alive(server_name, server_api):
        all_servers_alive = False
        print("Server {} is NOT alive".format(server_name))
    else:
        print("Server {} is alive".format(server_name))

if not all_servers_alive:
    cont = input(
        "Not all servers alive, continue to provision on alive servers? [y/N]:")
    if cont.strip().lower() != "Y":
        print("Stopping...")
        sys.exit(1)

print("Ensuring all clients have access keys...")
client_keys = {}
for server_name, server_api in servers.items():
    access_keys = list_access_keys(
        server_name, server_api).get('accessKeys', [])

    for client_name in clients:
        client_has_key = False
        for access_key in access_keys:
            if client_name == access_key.get('name', ""):
                print("Found existing access key for {} in {}".format(
                    client_name, server_name))
                client_has_key = True

                if 'accessUrl' not in access_key:
                    raise ValueError("accessUrl not found for client {} in {}".format(
                        client_name, server_name))

                client_keys[(client_name, server_name)] = add_prefix(
                    access_key['accessUrl'])

        if client_has_key:
            continue

        print("Creating access key for {} in {}...".format(
            client_name, server_name))
        client_keys[(client_name, server_name)] = add_prefix(
            create_access_key(server_name, server_api, client_name))

print("Client keys:")
for name, url in sorted(client_keys.items()):
    print("Client {}, Server {}: {}".format(name[0], name[1], url))
