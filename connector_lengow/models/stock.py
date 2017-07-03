# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests

from odoo import api, models, fields
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job
from .configurator import MarketPlaceConfigurator


class LengowStockPicking(models.Model):
    _name = 'lengow.stock.picking'
    _inherit = 'lengow.binding'
    _inherits = {'stock.picking': 'odoo_id'}
    _description = 'Lengow Delivery Order'

    odoo_id = fields.Many2one(comodel_name='stock.picking',
                              string='Stock Picking',
                              required=True,
                              ondelete='cascade')
    lengow_order_id = fields.Many2one(comodel_name='lengow.sale.order',
                                      string='Lengow Sale Order',
                                      ondelete='set null')
    picking_method = fields.Selection(selection=[('complete', 'Complete'),
                                                 ('partial', 'Partial')],
                                      required=True)

    @job(default_channel='root.lengow')
    @api.multi
    def export_picking_done(self):
        """ Export a complete or partial delivery order. """
        self.ensure_one()
        exporter = self.component(usage='record.exporter')
        res = exporter.run(self)
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    lengow_bind_ids = fields.One2many(
        comodel_name='lengow.stock.picking',
        inverse_name='odoo_id',
        string="Lengow Bindings",
    )


class StockPickingAdapter(Component):
    _name = 'lengow.stock.picking.adapter'
    _inherit = 'lengow.adapter20'
    _apply_on = 'lengow.stock.picking'


class LengowPickingExporter(Component):
    _name = 'lengow.stock.picking.exporter'
    _inherit = 'lengow.exporter'
    _apply_on = ['lengow.stock.picking']

    def run(self, picking_id):
        picking = self.env['lengow.stock.picking'].browse(picking_id)
        sale = picking.sale_id
        marketplace = sale.lengow_bind_ids.marketplace_id.lengow_id
        config = MarketPlaceConfigurator().get_configurator(
            self.env, marketplace)
        assert config is not None, (
            'No MarketplaceConfigurator found for %s' % marketplace)
        adapter = self.component(usage='backend.adapter')
        api_url = '%s/%s' % (
            self.backend_record.wsdl_location,
            config().get_export_picking_api(sale.lengow_bind_ids[0].id_flux,
                                            sale.lengow_bind_ids[0].lengow_id))
        tracking_params = config().configure_tracking_params(
            picking.carrier_tracking_ref,
            picking.carrier_id.lengow_value or False)

        adapter.process_request(requests.post, api_url,
                                params=tracking_params,
                                ignore_result=True)


class LengowBindingStockPickingListener(Component):
    _name = 'lengow.binding.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['lengow.stock.picking']

    def on_record_create(self, record, fields=None):
        job_name = "Export Lengow Picking %s (Order: %s)" % (
            record.name, record.sale_id.name)
        record.with_delay(description=job_name).export_picking_done()


class LengowStockPickingListener(Component):
    _name = 'lengow.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.picking']

    def on_picking_out_done(self, record, picking_method):
        """
        Create a ``lengow.stock.picking`` record. This record will then
        be exported to Lengow.
        :param picking_method: picking_method, can be 'complete' or 'partial'
        :type picking_method: str
        """
        sale = record.sale_id
        if not sale:
            return
        for lengow_sale in sale.lengow_bind_ids:
            self.env['lengow.stock.picking'].create({
                'backend_id': lengow_sale.backend_id.id,
                'odoo_id': record.id,
                'lengow_order_id': lengow_sale.id,
                'picking_method': picking_method})
