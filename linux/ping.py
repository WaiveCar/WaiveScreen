#!/usr/bin/python3

# For the UUID of the system. This should
# be robust to everything but the an actual
# board replacement.
#
# This may be a bad idea in the long run
# and we may want to do a full and complete
# decoupling and just do a UUIDv5 but this
# should be fine for now.
#
def get_uuid():
    import subprocess
    import json

    m = subprocess.run(["/bin/ip","-j","-p","addr","show","enp3s0"], stdout=subprocess.PIPE)
    json = json.loads(m.stdout.decode('utf-8'))

    for iface in json:
        if 'address' in iface:
            return iface['address']

uuid = get_uuid()
print(uuid)
