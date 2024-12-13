# Ultradns Modules for Ansible Collections

Collection of Ansible modules for managing UltraDNS zones and records

## Description
The UltraDNS Ansible collection provides ability to manage UltraDNS zones and records using Ansible tasks.

## Requirements

- Python 3.10 or later
- Ansible core 2.15 or later
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
UltraDNS Ansible modules run from the control node and do not connect to hosts in the inventory.  Your tasks using `ultradns.ultradns.` modules must have the connection set to `local`.

### Calling UltraDNS APIs
The UltraDNS modules for Ansible call the UltraDNS API to make changes.  Your plays must know how to connect to your UltraDNS account, this can be done in the following ways:

##### **Include a `provider` option in your playbook**

UltraDNS modules provide an optional `provider` section described as follows

```yaml
provider:
      username: string <username>
      password: string <mypass>
      use_test: boolean <True | False>
```

- `username` and `password` provide your UltraDNS credentials
- `use_test`
  - `use_test: True` forces the module to interact with the UltraDNS customer testing API
  - `use_test: False` **(default)** sends the module to the main UltraDNS API endpoints

When using the `provider` section it recommended to define a variable inside of a vault to hide the credentials. For example:

In your vault
```yaml
ultradns:
  use_test: False
  username: ultrauser
  password: myUltraPa55word
```

Then in your plays, set the `provider` to `{{ ultradns }}` like so:
```yaml
tasks:
  - name: ultradns primary zone
    ultradns.ultradns.zone:
      name: example.com.
      account: accountname
      state: present
      provider: "{{ ultradns }}"
```

##### **Use environment variables**
The UltraDNS Ansible modules can get the necessary credentials from environment variables.  If there is no `provider` section or if the data in the provider is incomplete the modules will fallback to using the environment variables if they are available.

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
