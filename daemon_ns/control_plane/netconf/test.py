from ncclient import manager

host = "172.20.112.137"

with manager.connect(host=host, port=8306, username="user", hostkey_verify=False) as m:
    c = m.get_config(source='running').data_xml
    with open(f"{host}.xml", 'w') as f:
        f.write(c)