import requests
import getpass
import stdiomask

def login(session, base_url, username, password):
    login_url = f"{base_url}/api/login"
    login_data = {"username": username, "password": password}
    response = session.post(login_url, json=login_data)
    response.raise_for_status()

def get_sites(session, base_url):
    sites_url = f"{base_url}/api/self/sites"
    response = session.get(sites_url)
    response.raise_for_status()
    return response.json()['data']

def get_admins(session, base_url, site_name):
    admins_url = f"{base_url}/api/s/{site_name}/cmd/sitemgr"
    admins_data = {'cmd': 'get-admins'}
    response = session.post(admins_url, json=admins_data)
    response.raise_for_status()
    return response.json()['data']

def get_all_admins(session, base_url):
    sites = get_sites(session, base_url)
    all_admins = set()
    for site in sites:
        site_name = site['name']
        admins = get_admins(session, base_url, site_name)
        for admin in admins:
            all_admins.add((admin.get('name'), admin.get('_id')))
    return all_admins

def revoke_admin(session, base_url, site_name, admin_id):
    revoke_url = f"{base_url}/api/s/{site_name}/cmd/sitemgr"
    revoke_data = {'cmd': 'revoke-admin', 'admin': admin_id}
    response = session.post(revoke_url, json=revoke_data)
    response.raise_for_status()

def main():
    session = requests.Session()

    # Prompt for details
    url = input("Enter your UniFi Controller URL including port e.g unifi.example.com:8443: ")
    username = input("Enter your UniFi Controller username: ")
    password = stdiomask.getpass("Enter your UniFi Controller password: ", mask="*")

    api_base_url = "https://"+ url

    print("Connecting to UniFi Controller...")
    login(session, api_base_url, username, password)

    all_sites = get_sites(session, api_base_url)
    all_admins = list(get_all_admins(session, api_base_url))

    # Sort admins by name
    all_admins = sorted(all_admins, key=lambda admin: admin[0])

    # Print all admins 
    for i, (name, _id) in enumerate(all_admins):
        print(f"Admin: {name}, ID: {_id}")

    # Ask user to input the admin ID directly to make sure that they are deleting the correct user
    admin_id = input("Enter the ID of the admin to delete: ")

    # Find the admin with the input ID
    for name, _id in all_admins:
        if _id == admin_id:
            break
    else:
        print(f"No admin found with ID {admin_id}")
        return

    # Revoke selected admin from all sites
    print(f"Revoking admin {name} from all sites...")
    for site in all_sites:
        site_name = site['name']
        try:
            revoke_admin(session, api_base_url, site_name, admin_id)
        except requests.HTTPError as e:
            # If the admin is not an admin on this site, the server will return a 400 error.
            # We'll ignore this error and continue with the next site.
            if e.response.status_code != 400:
                raise
    print(f"Admin {name} has been revoked from all sites.")

if __name__ == "__main__":
    main()
