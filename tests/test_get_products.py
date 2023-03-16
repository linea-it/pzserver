import sys
sys.path.append('..')
print(sys.path)
from pz_server import PzServer
token = '6c5035393d4153b1996481092e31578130f9f8a3'
pz_server = PzServer(token=token, host='pz-dev')

print('-----------------------------------------') 
print('  ### Get basic info from PZ Server ###  ')
print('-----------------------------------------')
print('pz_server.get_product_types()')
print(pz_server.get_product_types())
print('-----------------------------------------')
print('pz_server.get_users()')
print(pz_server.get_users())
print('-----------------------------------------')
print('pz_server.get_releases()')
print(pz_server.get_releases())
print('-----------------------------------------')
print('pz_server.get_products_list()')
print(pz_server.get_products_list())
print('-----------------------------------------')
print('''pz_server.get_products_list(filters={"release": "LSST DP0", 
                                  "product_type": "Spec-z Catalog",
                                  "uploaded_by": "Gschwend"})''')
print(pz_server.get_products_list(filters={"release": "LSST DP0", 
                                  "product_type": "Spec-z Catalog",
                                  "uploaded_by": "Gschwend"}))
print('-----------------------------------------')
print()
print()
print('Done')
print()


