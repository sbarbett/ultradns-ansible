# Ultradns Modules for Ansible Collection

Collection of Ansible modules for managing UltraDNS zones and records

## Description
The UltraDNS Ansible collection provides ability to manage DNS zones and records on UltraDNS using Ansible tasks.

## Requirements

- Python 3.10 or later
- Ansible core 2.15 or later
- [UltraDNS](https://vercara.com/authoritative-dns) account 
- Python [Requests module](https://requests.readthedocs.io/)

## Modules

- `zone` - Configure a zone managed by UltraDNS
- `secondary_zone` - Configure a zone using UltraDNS as secondary nameserver
- `record` - Configure DNS records in an UltraDNS managed zone

## Installation

```bash
    ansible-galaxy collection install ultradns.ultradns
```

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml` using the format:

```yaml
collections:
  - name: ultradns.ultradns
```

To upgrade the collection to the latest available version, run the following command:

```bash
ansible-galaxy collection install ultradns.ultradns --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax where `X.Y.Z` can be any [available version](https://galaxy.ansible.com/ultradns/ultradns):

```bash
ansible-galaxy collection install ultradns.ultradns:==X.Y.Z
```


## Using the modules

### `connection: local`
UltraDNS Ansible modules run from the control node.  Your tasks using `ultradns.ultradns.` modules must have the connection set to `local`.  Setting up the local connection can be done a couple of ways, refer to [Ansible documentation](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_delegation.html#local-playbooks) for more information.

- Put a localhost definition into your inventory

```yaml
---
local:
  hosts:
    localhost:
      ansible_connection: local
...
```

- Alternatively, a local connection can be used in a single playbook play, even if other plays in the playbook use the default remote connection type

```yaml
---
- hosts: 127.0.0.1
  connection: local
```

### Calling UltraDNS APIs
The UltraDNS modules for Ansible call the UltraDNS API to make changes.  Your tasks must know how to connect to your UltraDNS account, this can be done in the following ways:

##### **Include a `provider` variable in your playbook**

UltraDNS modules provide an optional `provider` dictionary variable for UltraDNS authentication described as follows

```yaml
provider:
      username: string <your UltraDNS username>
      password: string <your UltraDNS password>
      use_test: boolean <true | false>
```

- `username` and `password` provide your UltraDNS credentials
- `use_test`: if true, forces the module to interact with the UltraDNS customer testing API instead of the main UltraDNS API. Default is `false`

When using the `provider` section it recommended to define a variable inside of a vault to hide the credentials. For example:

In your vault
```yaml
ultra_provider:
  use_test: false
  username: <your UltraDNS username>
  password: <your UltraDNS password>
```

Then in your tasks, set the `provider` variable to `"{{ ultra_provider }}"` as:
```yaml
tasks:
  - name: ultradns primary zone
    ultradns.ultradns.zone:
      name: example.com.
      account: accountname
      state: present
      provider: "{{ ultra_provider }}"
```

##### **Use environment variables**
The UltraDNS Ansible modules can also get the necessary credentials from environment variables.  If there is no `provider` section or if the data in the provider is incomplete the modules will fallback to using the environment variables if they are available.

- `ULTRADNS_USERNAME` your UltraDNS username
- `ULTRADNS_PASSWORD` your crendtial password
- `ULTRADNS_USE_TEST` any value. If variable exists then use test environment

## Release notes

See the [changelog](https://github.com/ultradns/ultradns-ansible/blob/master/CHANGELOG.rst)

## More information

- [UltraDNS home page](https://vercara.com/authoritative-dns)
- [UltraDNS documentation](https://docs.ultradns.com/)
- [UltraDNS support](https://dns.ultraproducts.support)

## Issues and Requests

If you need assistance or have requests for the UltraDNS Ansible collection you can support from multiple channels:

- **GitHub Issues**
  - open a ticket in the [UltraDNS ansible](https://github.com/ultradns/ultradns-ansible/issues) GitHub repository

- **UltraDNS Support**
  - contact [UltraDNS support](https://dns.ultraproducts.support) directly

## Licensing

Released under GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
