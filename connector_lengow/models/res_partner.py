# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.component.core import Component


class LengowResPartner(models.Model):
    _name = 'lengow.res.partner'
    _inherit = 'lengow.binding'
    _inherits = {'res.partner': 'odoo_id'}
    _description = 'Lengow Partner'

    odoo_id = fields.Many2one(comodel_name='res.partner',
                              string='Partner',
                              required=True,
                              ondelete='cascade')


class PartnerImportMapper(Component):
    _name = 'lengow.res.partner.mapper'
    _inherit = 'lengow.import.mapper'
    _apply_on = 'lengow.res.partner'

    direct = [('address', 'street'),
              ('address_2', 'street2'),
              ('zipcode', 'zip'),
              ('city', 'city'),
              ('phone_home', 'phone'),
              ('phone_mobile', 'mobile'),
              ('email', 'email')]

    @mapping
    def name(self, record):
        if record['firstname']:
            name = " ".join([record['lastname'],
                             record['firstname']])
        else:
            name = record['lastname']
        return {'name': name}

    @mapping
    def country_id(self, record):
        country = self.env['res.country'].search(
            [('code', '=', record['country_iso'])])
        return {'country_id': country.id if country else None}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class PartnerImporter(Component):
    _name = 'lengow.res.partner.importer'
    _inherit = 'lengow.importer'
    _apply_on = 'lengow.res.partner'

    _discriminant_fields = ['firstname', 'lastname', 'city', 'email']
    _prefix = False

    def _clean_data_keys(self, data):
        """
            From the lengow API we receive 2 kinds of data for partner:
            - delivery data
            - billing data
            As they have the same values but a different prefix in their data
            naming convention, the goal of this method is to remove the prefix
            in order to unify the partner import.
            Example:
                billing_name -> name
                delivery_name -> name
        """
        prefix = data.keys()[0].split('_')[0]
        return self._remove_key_prefix(prefix, data)

    def _remove_key_prefix(self, prefix, data):
        prefix = '%s_' % prefix
        for key in data.keys():
            newkey = key.replace(prefix, '')
            data[newkey] = data.pop(key)
        return data

    def _generate_hash_key(self, record_data, clean_data=True):
        if clean_data:
            record_data = self._clean_data_keys(record_data)
        return super(PartnerImporter, self)._generate_hash_key(record_data)

    def run(self, lengow_id, lengow_data):
        lengow_data = self._clean_data_keys(lengow_data)
        return super(PartnerImporter, self).run(lengow_id, lengow_data)
