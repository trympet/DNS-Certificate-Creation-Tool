# (c) 2020 by Trym Lund Flogard
# https://github.com/trympet/
# The following code is licensed under MIT license (see LICENSE for details).
# Please read the license issued by The OpenSSL Project and SSLeay as well.

import os
def createPFX():
  ip = input("IP Address: ")
  # test path
  if not os.path.isdir("out/{}".format(ip)):
    print("no directory for ip. try again.")
    # recursion :-) very nice
    createPFX()
  # windows and *nix support
  openssl_prefix = ""
  if os.name == 'nt':
    # set openssl env vars
    pwd = os.path.dirname(os.path.realpath(__file__))
    os.environ['RANDFILE'] = pwd + "\\.rnd"
    os.environ['OPENSSL_CONF'] = pwd + "\\openssl\\openssl.cfg"
    openssl_prefix = "openssl\\openssl"
  else:
    # check openssl exsists
    openssl_prefix = os.popen("which openssl").read().rstrip()
    if (openssl_prefix == ""):
      print("Could not find openssl in env")
      exit(1)
  os.system("{} pkcs12 -export -out out/{}/{}.pfx -inkey out/{}/{}.key -in out/{}/{}.crt".format(openssl_prefix,ip,ip,ip,ip,ip,ip))
createPFX()
print("Success!")