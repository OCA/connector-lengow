.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================
Lengow Connector
====================

This module allows you to connect your Odoo to the Lengow platform(www.lengow.com).
It is build on top of the connector framework. It is is structured so that
it can be extended or modified easily from separate addons.


Usage
=====

=========
Features
=========

- Define catalogue, link your products and export them to Lengow
- Import your orders from all marketplaces supported by Lengow
- Inform the marketplace once you deliver the goods
- Export the tracking number to the marketplace
- Support the delivery by MarketPlace (Amazon Full Fillment for example). More Details below.

===============================
Delivery By MarketPlace (HowTO)
===============================
- Install the OCA module stock\_auto_\move from https://github.com/OCA/stock-logistics-workflow
- Define a route using automatic move
- Set the route on the marketplace


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/connector-lengow/10.0

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "10.0" for example

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/connector-lengow/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Cédric Pigeon <cedric.pigeon@acsone.eu>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
