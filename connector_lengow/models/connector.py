# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons.queue_job.job import job


class LengowBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All the models used as bindings between Lengow and OpenERP
    (``lengow.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'lengow.binding'
    _inherit = 'external.binding'
    _description = 'Lengow Binding (abstract)'

    # odoo_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='lengow.backend',
        string='Lengow Backend',
        required=True,
        ondelete='restrict',
    )
    lengow_id = fields.Char(string='ID on Lengow')

    @job(default_channel='root.lengow')
    @api.model
    def import_record(self, backend, external_id, record_data):
        """ Import a Lengow record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, record_data)

    @job(default_channel='root.lengow')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Magento """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)
