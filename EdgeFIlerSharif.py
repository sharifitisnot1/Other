
import sys
import getpass

import cterasdk
import cterasdk.settings
from cterasdk import GlobalAdmin, Edge
from cterasdk.edge.sync import Sync

# 1) Disable SSL verification for self-signed certs
cterasdk.settings.core.syn.settings.connector.ssl = False
cterasdk.settings.edge.syn.settings.connector.ssl = False

def get_primary_ip(conn):
    """
    Return the first non-loopback privateIP, else non-loopback publicIP, else None.
    """
    if conn.privateIP and not conn.privateIP.startswith("127."):
        return conn.privateIP
    if conn.publicIP and not conn.publicIP.startswith("127."):
        return conn.publicIP
    return None

def main():

    ga_host     = input("Global Admin host (e.g. sharif81.ctera.me): ").strip()
    portal_name = input("Portal (tenant) name      : ").strip()
    ga_user     = input("Global Admin username     : ").strip()
    ga_pass     = getpass.getpass("Global Admin password     : ")


    with GlobalAdmin(ga_host) as admin:
        admin.login(ga_user, ga_pass)
        admin.portals.browse(portal_name)
        filers = admin.devices.filers(include=['deviceConnectionStatus'])

        print(f"\n{'IP':15} {'NAME':20} {'TYPE':10} {'CONNECTED':9} {'VERSION'}")
        print("-" * 70)

    
        valid = []
        for f in filers:
            conn = f.deviceConnectionStatus
            ip = get_primary_ip(conn)
            if not ip:
                continue
            valid.append((f, ip))
            print(f"{ip:15} {f.name:20} {f.deviceType:10} {str(conn.connected):9} {f.version}")

        admin.portals.browse_global_admin()

    if not valid:
        print("No reachable filers found.")
        sys.exit(1)

  
    target_ip = input("\nEnter the IP of the filer to inspect sync of: ").strip()
    selected = None
    for f, ip in valid:
        if ip == target_ip:
            selected = f
            break
    if not selected:
        print(f"No filer found with IP '{target_ip}'.")
        sys.exit(1)

    print(f"\nSelected Edge Filer: {selected.name} ({target_ip})")
    print("\nEnter credentials for the selected Edge Filer:")
    ef_user = input("  Username: ").strip()
    ef_pass = getpass.getpass("  Password: ")

  
    with Edge(target_ip) as edge:
        edge.login(ef_user, ef_pass)
        sync = Sync(edge)
        status = sync.get_status()
        print(f"\nCloud-Sync status for {target_ip}: {status}")

if __name__ == "__main__":
    main()

