=================================
Ultradns Collection Release Notes
=================================

.. contents:: Topics

v1.1.0
======

Release Summary
---------------

| Release Date: 2025-03-20
| Added support for zone_facts, zone_meta_facts, and record_facts modules

New Modules
-----------

- zone_facts - Get facts about zones in UltraDNS
- zone_meta_facts - Get metadata for specific zones in UltraDNS
- record_facts - Get facts about DNS records in a zone in UltraDNS

v1.0.3
======

Release Summary
---------------

| Release Date: 2024-03-03
| Added support for TTL-only updates of DNS records and refactored the connection module to use the ultra_rest_client.

Minor Changes
-------------

- Added support for TTL-only updates of DNS records without requiring the `data` parameter
- Added PATCH method to the UltraConnection class for partial updates
- Refactored base connection module to use the ultra_rest_client for connection
- Fixed the error it was returning if you tried to rerun a solo record playbook with no change to the rdata

v1.0.2
======

Release Summary
---------------

| Release Date: 2024-12-20
| improved AAAA record handling

Minor Changes
-------------

- CNAME and SOA records now update correctly
- Fix v4 and v6 IP address comparisons

v1.0.1
======

Release Summary
---------------

| Release Date: 2024-12-16
| fixing up readme for galaxy formatting and display

v1.0.0
======

Release Summary
---------------

| Release Date: 2024-12-16
| Organizing the base UltraDNSModule class

Minor Changes
-------------

- Module documentation cleanup
- Refactoring of the base UltraDNSModule class

v0.5.0
======

Release Summary
---------------

| Release Date: 2024-12-13
| Project cleanup and refactor from initial results

Minor Changes
-------------

- Add doc_fragments to reduce duplication in the documentation

v0.1.0
======

Release Summary
---------------

| Release Date: 2024-12-13
| The initial pre-release to get the `ultradns.ultradns` collection into Galaxy

New Modules
-----------

- record - Manage zone resource records in UltraDNS
- secondary_zone - Manage secondary zones in UltraDNS
- zone - Manage primary zones in UltraDNS
