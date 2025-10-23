#!/usr/bin/env python3
# SDK_zones.py by Sharif Bey
#  Disables SSL verification
#  Logs into sharif81.ctera.me as admin
#  Ensures zone exists (create if missing) at GLOBAL scope with 'Selected Folders' policy
#  Adds device(s) to the zone 
#  Adds folder(s) to the zone

import cterasdk
import cterasdk.settings
from cterasdk import GlobalAdmin
from cterasdk.core.enum import PolicyType
from cterasdk.core import types as core_types
from cterasdk import exceptions as ctera_exc
from typing import List, Dict

# Inputs
PORTAL_HOST = 'sharif81.ctera.me'
USERNAME    = 'admin'
PASSWORD    = "12345"

ZONE_NAME        = 'test zone'
ZONE_DESCRIPTION = 'sdkzone'

DEVICES_TO_ADD: List[str] = ['vGateway-3814']

# Folders to add: list of dicts with 'name' and 'owner' keys
FOLDERS_TO_ADD: List[Dict[str, str]] = [
    {"name": "Certs",         "owner": "admin"},
    {"name": "Agenttest",     "owner": "admin"},
    {"name": "CF_2",          "owner": "admin"},
    {"name": "CF-broken",     "owner": "admin"},
    {"name": "192.168.22.12", "owner": "admin"},
]

# Helper to get 'Selected Folders' policy enum
def _policy_selected():
    for attr in ('SelectedFolders', 'selectedFolders', 'SELECTED_FOLDERS'):
        if hasattr(PolicyType, attr):
            return getattr(PolicyType, attr)
    return 'selectedFolders'

# Helper to get 'No Folders' policy enum
def _policy_none():
    for attr in ('None', 'NoPolicy', 'NONE', 'noFolders'):
        if hasattr(PolicyType, attr):
            return getattr(PolicyType, attr)
    return 'noFolders'

# Ensure zone exists with 'Selected Folders' policy
def ensure_zone_selected(admin: GlobalAdmin, name: str, description: str):
    selected = _policy_selected()
    try:
        # If zone exists, try to set policy to Selected Folders (if modify exists)
        admin.cloudfs.zones.get(name)
        try:
            admin.cloudfs.zones.modify(name, policy_type=selected, description=description)
            print(f"Zone '{name}' policy set to Selected Folders.")
        except Exception:
            print(f"Zone '{name}' exists. (Modify not available; using existing settings.)")
        return
    except ctera_exc.CTERAException:
        pass

    print(f"Creating zone '{name}' with Selected Folders policy...")
    try:
        admin.cloudfs.zones.add(name=name, policy_type=selected, description=description)
    except Exception as e:
        if selected != 'selectedFolders':
            print(f"Create failed with enum ({e}); retrying with string policy_type='selectedFolders'...")
            admin.cloudfs.zones.add(name=name, policy_type='selectedFolders', description=description)
        else:
            raise
    print(f"Zone '{name}' created.")

# Add devices to zone
def add_devices(admin: GlobalAdmin, zone_name: str, devices: List[str]) -> None:
    if not devices:
        return
    print(f"Adding device(s) to zone '{zone_name}': {', '.join(devices)}")
    admin.cloudfs.zones.add_devices(zone_name, devices)
    print("Devices added.")

# Add folders to zone
def add_folders(admin: GlobalAdmin, zone_name: str, specs: List[Dict[str, str]]) -> None:
    if not specs:
        return
    helpers = []
    labels  = []
    for s in specs:
        name  = (s.get('name') or '').strip()
        owner = (s.get('owner') or '').strip()
        if not name or not owner:
            continue
        helpers.append(core_types.CloudFSFolderFindingHelper(name, core_types.UserAccount(owner)))
        labels.append(f"{name} (owner={owner})")

    if not helpers:
        print("No valid folder specs to add.")
        return

    print(f"Adding folder(s) to zone '{zone_name}': {', '.join(labels)}")
    try:
        admin.cloudfs.zones.add_folders(zone_name, helpers)
        print("Folders added.")
    except Exception as e:
        print(f"Bulk add_folders failed: {e}; retrying one-by-one...")
        for s in specs:
            name  = (s.get('name') or '').strip()
            owner = (s.get('owner') or '').strip()
            if not name or not owner:
                continue
            try:
                admin.cloudfs.zones.add_folders(
                    zone_name,
                    [core_types.CloudFSFolderFindingHelper(name, core_types.UserAccount(owner))]
                )
                print(f"  ✓ {name} (owner={owner})")
            except Exception as ie:
                print(f"  ✗ {name} (owner={owner}) -> {ie}")
                # Handle individual folder add failure 
    
# call main
def main() -> int:
    cterasdk.settings.core.syn.settings.connector.ssl = False  # disable SSL verification

    with GlobalAdmin(PORTAL_HOST) as admin:
        admin.login(USERNAME, PASSWORD)
        print("Logged in as Global Admin")

        # 1) Ensure zone exists and is 'Selected Folders'
        ensure_zone_selected(admin, ZONE_NAME, ZONE_DESCRIPTION)

        # 2) Add device(s)
        add_devices(admin, ZONE_NAME, DEVICES_TO_ADD)

        # 3) Add folders
        add_folders(admin, ZONE_NAME, FOLDERS_TO_ADD)

        print(f"\nDone. Zone '{ZONE_NAME}' updated (policy=Selected Folders ➜ devices ➜ folders).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

