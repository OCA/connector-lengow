# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import timedelta, date

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.addons.connector.unit.mapper import mapping
from odoo.addons.component.core import Component


_logger = logging.getLogger(__name__)


class LengowSaleOrder(models.Model):
    _name = 'lengow.sale.order'
    _inherit = 'lengow.binding'
    _inherits = {'sale.order': 'odoo_id'}
    _description = 'Lengow Sale Order'

    backend_id = fields.Many2one(index=True)
    odoo_id = fields.Many2one(comodel_name='sale.order',
                              string='Sale Order',
                              required=True,
                              ondelete='cascade')
    lengow_order_line_ids = fields.One2many(
        comodel_name='lengow.sale.order.line',
        inverse_name='lengow_order_id',
        string='Lengow Order Lines'
    )
    total_amount = fields.Float(
        digits=dp.get_precision('Account')
    )
    total_amount_tax = fields.Float(
        string='Total amount w. tax',
        digits=dp.get_precision('Account')
    )
    lengow_order_id = fields.Char(string='Lengow Order ID',
                                  index=True)
    marketplace_id = fields.Many2one(string='MarketPlace',
                                     comodel_name='lengow.market.place',
                                     index=True)
    id_flux = fields.Char('Id Flux on Lengow',
                          index=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    lengow_bind_ids = fields.One2many(
        comodel_name='lengow.sale.order',
        inverse_name='odoo_id',
        string='Lengow Bindings',
    )

    is_from_lengow = fields.Boolean(string='Order imported from Lengow',
                                    compute='_compute_is_from_lengow',
                                    store=True)

    lengow_total_amount = fields.Float(
        string='Lengow Total amount',
        digits=dp.get_precision('Account'),
        compute='_compute_lengow_total_amount',
        store=True
    )
    lengow_total_amount_tax = fields.Float(
        string='Lengow Total amount w. tax',
        digits=dp.get_precision('Account'),
        compute='_compute_lengow_total_amount_tax',
        store=True
    )

    @api.depends('lengow_bind_ids')
    @api.multi
    def _compute_is_from_lengow(self):
        for order in self:
            order.is_from_lengow = len(order.lengow_bind_ids) > 0

    @api.depends('lengow_bind_ids')
    @api.multi
    def _compute_lengow_total_amount(self):
        for order in self:
            if len(order.lengow_bind_ids):
                binding = order.lengow_bind_ids[0]
                order.lengow_total_amount = binding.total_amount
            else:
                order.lengow_total_amount = False

    @api.depends('lengow_bind_ids')
    @api.multi
    def _compute_lengow_total_amount_tax(self):
        for order in self:
            if len(order.lengow_bind_ids):
                binding = order.lengow_bind_ids[0]
                order.lengow_total_amount_tax = binding.total_amount_tax
            else:
                order.lengow_total_amount_tax = False

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if 'reference' not in invoice_vals:
            invoice_vals['reference'] = self.name
        return invoice_vals


class LengowSaleOrderAdapter(Component):
    _name = 'lengow.sale.order.adapter'
    _inherit = 'lengow.adapter20'
    _apply_on = 'lengow.sale.order'
    _api = "V2/%s/%s/%s/%s/%s/commands/%s/%s/"

    def search(self, filters=None, from_date=None, to_date=None):
        id_client = self.backend_record.id_client
        id_group = filters.pop('id_group', '0')
        id_flux = filters.pop('id_flux', 'orders')
        state = filters.pop('state', 'processing')
        if not from_date:
            start_date = date.today() - timedelta(days=1)
            from_date = fields.Date.to_string(start_date)
        if not to_date:
            to_date = fields.Date.today()
        self._api = str(self._api % (from_date,
                                     to_date,
                                     id_client,
                                     id_group,
                                     id_flux,
                                     state,
                                     'json'))
        return super(LengowSaleOrderAdapter, self).search()


class SaleOrderBatchImporter(Component):
    _name = 'lengow.sale.order.batch.importer'
    _inherit = 'lengow.delayed.batch.importer'
    _apply_on = 'lengow.sale.order'

    def _import_record(self, record_id, record_data):
        """ Import the record directly """
        return super(SaleOrderBatchImporter, self)._import_record(
            record_id, record_data)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        result = self.backend_adapter.search(
            filters,
            from_date=from_date,
            to_date=to_date)
        orders_data = result['orders'] or []
        order_ids = [data['order_id'] for data in orders_data]
        _logger.info('Search for lengow sale orders %s returned %s',
                     filters, order_ids)
        for order_data in orders_data:
            order_count = self.env['lengow.sale.order'].search_count(
                [('backend_id', '=', self.backend_record.id),
                 ('lengow_id', '=', order_data['order_id'])])
            if order_count == 0:
                self._import_record(order_data['order_id'], order_data)


class SaleOrderMapper(Component):
    _name = 'lengow.sale.order.mapper'
    _inherit = 'lengow.import.mapper'
    _apply_on = 'lengow.sale.order'

    direct = [('order_id', 'client_order_ref'),
              ('order_purchase_date', 'date_order'),
              ('order_comments', 'note'),
              ('order_amount', 'total_amount'),
              ('order_tax', 'total_amount_tax')]

    children = [('cart', 'lengow_order_line_ids', 'lengow.sale.order.line')]

    def _add_shipping_line(self, map_record, values):
        record = map_record.source
        ship_amount = float(record.get('order_shipping') or 0.0)
        if not ship_amount:
            return values
        line_builder = self.component(usage='order.line.builder.shipping')

        line_builder.price_unit = ship_amount

        line = (0, 0, line_builder.get_line())
        values['order_line'].append(line)
        return values

    def _get_partner_id(self, partner_data):
        binding_model = 'lengow.res.partner'
        with self.backend_record.work_on(binding_model) as work:
            importer = work.component(usage='record.importer')
            partner_lengow_id = importer._generate_hash_key(partner_data)
            binder = self.binder_for(binding_model)
            partner_id = binder.to_internal(partner_lengow_id, unwrap=True)
            assert partner_id is not None, (
                "partner %s should have been imported in "
                "LengowSaleOrderImporter._import_dependencies"
                % partner_data)
            return partner_id.id

    @mapping
    def partner_id(self, record):
        partner_id = self._get_partner_id(record['billing_address'])
        return {'partner_id': partner_id,
                'partner_invoice_id': partner_id}

    @mapping
    def partner_shipping_id(self, record):
        partner_id = self._get_partner_id(record['delivery_address'])
        return {'partner_shipping_id': partner_id}

    @mapping
    def user_id(self, record):
        return {'user_id': False}

    @mapping
    def markeplace_id(self, record):
        return {'marketplace_id': self.options.marketplace.id or False}

    @mapping
    def project_id(self, record):
        analytic_account = self.options.marketplace.account_analytic_id
        return {'project_id': analytic_account.id or False}

    @mapping
    def fiscal_position_id(self, record):
        # looking for fiscal position based on delivery country
        country_code_iso = record['delivery_address']['country_iso']
        tax_mapping = \
            self.options.marketplace.backend_id.tax_mapping_ids \
                .filtered(lambda x: x.country_id.code == country_code_iso)
        if tax_mapping:
            fiscal_position = tax_mapping.fiscal_position_id
        else:
            fiscal_position = self.options.marketplace.fiscal_position_id
        return {'fiscal_position_id': fiscal_position.id or False}

    @mapping
    def warehouse_id(self, record):
        warehouse = self.options.marketplace.warehouse_id
        return {'warehouse_id': warehouse.id or False}

    @mapping
    def payment_method_id(self, record):
        return {'payment_mode_id':
                self.options.marketplace.payment_mode_id.id or False}

    @mapping
    def name(self, record):
        if self.options.marketplace.sale_prefix_code:
            name = '%s-%s' % (self.options.marketplace.sale_prefix_code,
                              record['order_id'])
        else:
            name = record['order_id']
        return {'name': name}

    @mapping
    def id_flux(self, record):
        return {'id_flux': record['idFlux']}

    @mapping
    def pricelist_id(self, record):
        currency_code = record['order_currency']
        currency = self.env['res.currency'].search(
            [('name', '=', currency_code)])
        if currency:
            currency_mapping = \
                self.options.marketplace.backend_id.currency_mapping_ids\
                    .filtered(lambda x: x.currency_id.id == currency.id)
            if currency_mapping:
                return {'pricelist_id': currency_mapping.pricelist_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    def finalize(self, map_record, values):
        values.setdefault('order_line', [])
        values = self._add_shipping_line(map_record, values)
        onchange = self.component(
            usage='ecommerce.onchange.manager.sale.order')
        return onchange.play(values, values['lengow_order_line_ids'])


class LengowSaleOrderImporter(Component):
    _name = 'lengow.sale.order.importer'
    _inherit = 'lengow.importer'
    _apply_on = 'lengow.sale.order'

    def _import_dependencies(self):
        record = self.lengow_record
        billing_partner_data = record['billing_address']
        self._import_dependency(False,
                                'lengow.res.partner',
                                billing_partner_data,)
        delivery_partner_data = record['delivery_address']
        self._import_dependency(False,
                                'lengow.res.partner',
                                delivery_partner_data)

    def _get_market_place(self, record):
        marketplace_binder = self.binder_for('lengow.market.place')
        marketplace = marketplace_binder.to_internal(record['marketplace'])
        assert marketplace, (
            "MarketPlace %s does not exists."
            % record['marketplace'])
        return marketplace

    def _check_is_marketplacedelivering(self, record):
        tracking_data = record.get('tracking_informations', {})

        if tracking_data:
            marketplacedelivering = tracking_data.get(
                'tracking_deliveringByMarketPlace', "0")
            return True if marketplacedelivering == "1" else False
        return False

    def _create_data(self, map_record, **kwargs):
        marketplace = self._get_market_place(map_record.source)
        is_marketplacedelivering = self._check_is_marketplacedelivering(
            map_record.source)
        return super(LengowSaleOrderImporter, self)._create_data(
            map_record,
            marketplace=marketplace,
            lengow_order_id=self.lengow_id,
            is_marketplacedelivering=is_marketplacedelivering,
            **kwargs)

    def _update_data(self, map_record, **kwargs):
        # sale order update is not managed
        return

    def _create(self, data):
        binding = super(LengowSaleOrderImporter, self)._create(data)
        if binding.fiscal_position_id:
            binding.odoo_id._compute_tax_id()
        return binding

    def _update(self, binding, data):
        # sale order update is not managed
        return

    def _order_line_preprocess(self, lengow_data):
        # simplify message structure for child mapping and remove refused
        # or cancelled lines
        lines = []
        for line in lengow_data['cart']['products']:
            if not line.get('status', False) in ('cancel', 'refused'):
                lines.append(line)
        lengow_data['cart'] = lines
        return lengow_data

    def _after_import(self, binding):
        super(LengowSaleOrderImporter, self)._after_import(binding)
        main_partner = binding.partner_id
        shipping_partner = binding.partner_shipping_id

        if (main_partner != shipping_partner and
                shipping_partner.parent_id != main_partner):
            data = {
                'type': 'delivery',
                'parent_id': main_partner.id
            }
            shipping_partner.write(data)

    def run(self, lengow_id, lengow_data):
        lengow_data = self._order_line_preprocess(lengow_data)
        return super(LengowSaleOrderImporter, self).run(lengow_id, lengow_data)


class LengowSaleOrderLine(models.Model):
    _name = 'lengow.sale.order.line'
    _inherit = 'lengow.binding'
    _inherits = {'sale.order.line': 'odoo_id'}
    _description = 'Lengow Sale Order Line'

    odoo_id = fields.Many2one(comodel_name='sale.order.line',
                              string='Sale Order Line',
                              required=True,
                              ondelete='cascade')
    lengow_order_id = fields.Many2one(comodel_name='lengow.sale.order',
                                      string='Lengow Sale Order',
                                      required=True,
                                      ondelete='cascade',
                                      index=True)
    lengow_orderline_id = fields.Char(string='Lengow Order Line ID')

    @api.model
    def create(self, vals):
        lengow_order_id = vals['lengow_order_id']
        binding = self.env['lengow.sale.order'].browse(lengow_order_id)
        vals['order_id'] = binding.odoo_id.id
        return super(LengowSaleOrderLine, self).create(vals)


class LengowSaleOrderLineMapper(Component):
    _name = 'lengow.sale.order.line.mapper'
    _inherit = 'lengow.import.mapper'
    _apply_on = 'lengow.sale.order.line'

    direct = [('title', 'name'),
              ('quantity', 'product_uom_qty'),
              ('price_unit', 'price_unit')]

    @mapping
    def lengow_order_id(self, record):
        return {'lengow_order_id': self.options.lengow_order_id}

    @mapping
    def product_id(self, record):
        binder = self.binder_for('lengow.product.product')
        product_id = binder.to_internal(record['sku'], unwrap=True)
        assert product_id is not None, (
            "product_id %s is not binded to a Lengow catalogue" %
            record['sku'])
        return {'product_id': product_id.id}

    @mapping
    def route_id(self, record):
        if self.options.is_marketplacedelivering:
            route = self.options.marketplace.route_id
            assert route, ("No route defined on marketplace %s "
                           "for auto-delivery"
                           % self.options.marketplace.name)
            return {'route_id': self.options.marketplace.route_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
