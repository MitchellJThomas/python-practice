import logging
import sys

from zeroconf import ServiceBrowser, Zeroconf, ZeroconfServiceTypes

# A quick study to learn a bit about the mDNS/Bonjour systems on my home network
# Much of this code was copied from https://github.com/jstasiak/python-zeroconf

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger()


class MyListener:
    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s" % (name, info))


print("\n".join(ZeroconfServiceTypes.find()))

zeroconf = Zeroconf()
listener = MyListener()
browsers = []
for s in ZeroconfServiceTypes.find():
    if len(s.split(".")[0]) <= 15:
        print(f"browsing {s}")
        browsers.append(ServiceBrowser(zeroconf, s, listener))

try:
    input("Press enter to exit...\n\n")  # nosec
finally:
    zeroconf.close()
