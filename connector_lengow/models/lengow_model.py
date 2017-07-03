# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import timedelta, date

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo.addons.connector.components.mapper import mapping
from odoo import exceptions

from odoo.addons.component.core import Component


_logger = logging.getLogger(__name__)


class LengowBackend(models.Model):
    _name = 'lengow.backend'
    _description = 'Lengow Backend'
    _inherit = 'connector.backend'

    @api.model
    def select_versions(self):
        """ Available versions in the backend.

        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [('2.0', '2.0'), ('3.0', '3.0')]

    version = fields.Selection(selection='select_versions', required=True)
    location = fields.Char(
        required=True,
        help="Url to Lengow application",
    )
    wsdl_location = fields.Char(
        help="Url to Lengow Wsdl (To update Orders)",
    )
    access_token = fields.Char(
        help="WebService Access Token",
    )
    secret = fields.Char(
        help="Webservice password",
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda x: x._get_default_company(),
        required=True
    )
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        help='If specified, this analytic account will be used to fill the '
        'field  on the sale order created by the connector. The value can '
        'also be specified on the marketplace.'
    )
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal position',
        help='If specified, this fiscal position will be used to fill the '
        'field fiscal position on the sale order created by the connector.'
        'The value can also be specified on the marketplace.'
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='If specified, this warehouse will be used to fill the '
        'field warehouse on the sale order created by the connector.'
        'The value can also be specified on the marketplace.',
    )
    catalogue_ids = fields.One2many(
        string='Catalogue',
        comodel_name='lengow.catalogue',
        inverse_name='backend_id')
    binded_products_count = fields.Float(
        compute='_compute_count_binded_products')
    id_client = fields.Char('Lengow Id Client')
    import_orders_from_date = fields.Date('Import Orders from Date')
    currency_mapping_ids = fields.One2many(
        string='Currencies',
        comodel_name='lengow.currency.mapping',
        inverse_name='backend_id')
    tax_mapping_ids = fields.One2many(
        string='Taxes',
        comodel_name='lengow.tax.mapping',
        inverse_name='backend_id')

    def _compute_count_binded_products(self):
        for catalogue in self.catalogue_ids:
            self.binded_products_count += catalogue.binded_products_count

    def _get_default_company(self):
        return self.env.user.company_id

    @api.multi
    def synchronize_metadata(self):
        try:
            for backend in self:
                with backend.work_on('lengow.market.place') as work:
                    a = work.component(usage='batch.importer')
                    a.run()
            return True
        except Exception as e:
            _logger.error(e.message, exc_info=True)
            raise UserError(
                _(u"Check your configuration, we can't get the data. "
                  u"Here is the error:\n%s") %
                str(e).decode('utf-8', 'ignore'))

    @api.multi
    def import_sale_orders(self, filters=None):
        if filters is None:
            filters = {}
        start_date = date.today() - timedelta(days=1)
        import_start_time = fields.Date.to_string(start_date)
        if self.import_orders_from_date:
            from_date = self.import_orders_from_date or None
        else:
            from_date = None
        if 'from_date' not in filters:
            filters['from_date'] = from_date
        if 'to_date' not in filters:
            filters['to_date'] = fields.Date.today()

        self.env['lengow.sale.order'].with_delay(priority=1).import_batch(
            self,
            filters=filters
        )
        self.write({'import_orders_from_date': import_start_time})

    @api.model
    def _lengow_backend(self, callback, domain=None, filters=None):
        if domain is None:
            domain = []
        if filters is None:
            filters = {}
        backends = self.search(domain)
        if backends:
            getattr(backends, callback)(filters)

    @api.model
    def _scheduler_import_sale_orders(self, domain=None, filters=None):
        self._lengow_backend('import_sale_orders', domain=domain,
                             filters=filters)


class LengowCurrencyMapping(models.Model):
    _name = 'lengow.currency.mapping'

    backend_id = fields.Many2one(string='Lengow Backend',
                                 comodel_name='lengow.backend',
                                 required=True)
    currency_id = fields.Many2one(string='Currency',
                                  comodel_name='res.currency',
                                  required=True)
    pricelist_id = fields.Many2one(string='Pricelist',
                                   comodel_name='product.pricelist',
                                   required=True)

    _sql_constraints = [
        ('curency_map_uniq',
         'unique(backend_id, currency_id)',
         'A binding already exists for this currency.'),
    ]

    @api.multi
    @api.constrains('pricelist_id')
    def _check_currency(self):
        for curr_mapping in self:
            if curr_mapping.currency_id and curr_mapping.pricelist_id:
                if curr_mapping.currency_id.id != \
                        curr_mapping.pricelist_id.currency_id.id:
                    raise exceptions.ValidationError(
                        _('Pricelist should be in the same currency.'))


class LengowTaxMapping(models.Model):
    _name = 'lengow.tax.mapping'

    backend_id = fields.Many2one(string='Lengow Backend',
                                 comodel_name='lengow.backend',
                                 required=True)
    country_id = fields.Many2one(string='Country',
                                 comodel_name='res.country',
                                 required=True)

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal position'
    )

    _sql_constraints = [
        ('country_map_uniq',
         'unique(backend_id, country_id)',
         'A binding already exists for this country.'),
    ]


class LengowCatalogue(models.Model):
    _name = 'lengow.catalogue'
    _description = 'Lengow Catalogue'

    backend_id = fields.Many2one(string='Lengow Backend',
                                 comodel_name='lengow.backend',
                                 required=True)

    name = fields.Char()

    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="This the default language used to export products, if nothing"
             "is specified, the language of the user responsible fo the export"
             "will be used",
    )
    product_ftp = fields.Boolean('Send By FTP')
    product_ftp_host = fields.Char(
        string='Host',
        help="FTP server used to send products file.")
    product_ftp_port = fields.Char(
        string='Port')
    product_ftp_user = fields.Char(
        string='User')
    product_ftp_password = fields.Char(
        string='Password')
    product_ftp_directory = fields.Char(
        string='Upload Directory')
    product_filename = fields.Char(
        string='Products File Name',
        required=True)
    last_export_date = fields.Datetime('Last Export on')
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse used to compute the '
             'stock quantities.',
    )
    product_stock_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Stock Field',
        default=lambda x: x._get_stock_field_id(),
        domain="[('model', 'in', ['product.product', 'product.template']),"
               " ('ttype', '=', 'float')]",
        help="Choose the field of the product which will be used for "
             "stock inventory updates.\nIf empty, Quantity Available "
             "is used.",
        required=True
    )
    product_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Sale Price List',
        help='If specified, this price list will be used to determine the '
        'price exported to Lengow'
    )
    binded_product_ids = fields.One2many(
        string="Binded Products",
        comodel_name='lengow.product.product',
        inverse_name='catalogue_id')
    binded_products_count = fields.Float(
        string='Binded Products',
        compute='_compute_count_binded_products')

    @api.model
    def _get_stock_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'virtual_available')],
            limit=1)
        return field

    def _compute_count_binded_products(self):
        for backend in self:
            backend.binded_products_count = len(backend.binded_product_ids)

    @api.multi
    def export_binded_products(self):
        self._scheduler_export_catalogue(
            domain=[('id', 'in', self.ids)])

    @api.multi
    def name_get(self):
        result = []
        for catalogue in self:
            result.append((catalogue.id, "%s (%s)" %
                           (catalogue.name, catalogue.backend_id.name)))
        return result

    @api.multi
    def write(self, vals):
        if 'backend_id' in vals:
            raise ValidationError(_('You are not allowed to update the backend'
                                    ' reference !'))
        return super(LengowCatalogue, self).write(vals)

    _sql_constraints = [
        ('product_filename_uniq', 'unique(product_filename, product_ftp_host'
         ',product_ftp_directory)',
         'A catalogue already exists with the same product filename'
         ' in the same directory on the same host.'),
    ]

    @api.model
    def _scheduler_export_catalogue(self, domain=None):
        if domain is None:
            domain = []
        catalogues = self.env['lengow.catalogue'].search(domain)
        for catalogue in catalogues:
            self.env['lengow.product.product'].with_delay(
                description="Export Lengow Catalogue %s (Lengow Backend: %s)" %
                (catalogue.name, catalogue.backend_id.name)
            ).export_products(catalogue)


class LengowMarketPlace(models.Model):
    _name = 'lengow.market.place'
    _inherit = ['lengow.binding']
    _description = 'Lengow Market Place'
    _parent_name = 'backend_id'

    name = fields.Char(required=True)
    homepage = fields.Char(string='Home Page')
    description = fields.Text(string='Text')
    specific_account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Specific analytic account',
    )
    specific_fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Specific fiscal position',
    )
    specific_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Specific warehouse',
    )
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        compute='_compute_account_analytic_id',
    )
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal position',
        compute='_compute_fiscal_position_id',
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='warehouse',
        compute='_compute_warehouse_id')
    backend_version = fields.Selection(related='backend_id.version')
    payment_mode_id = fields.Many2one(string='Payment Modz',
                                      comodel_name='account.payment.mode')
    sale_prefix_code = fields.Char(string='Prefix for Order Reference')
    route_id = fields.Many2one(string='Route',
                               comodel_name='stock.location.route',
                               domain=[('sale_selectable', '=', True)])

    @api.multi
    def _compute_account_analytic_id(self):
        for mp in self:
            mp.account_analytic_id = (
                mp.specific_account_analytic_id or
                mp.backend_id.account_analytic_id)

    @api.multi
    def _compute_fiscal_position_id(self):
        for mp in self:
            mp.fiscal_position_id = (
                mp.specific_fiscal_position_id or
                mp.backend_id.fiscal_position_id)

    @api.multi
    def _compute_warehouse_id(self):
        for mp in self:
            mp.warehouse_id = (
                mp.specific_warehouse_id or
                mp.backend_id.warehouse_id)

    @api.model
    def create(self, vals):
        marketplace = super(LengowMarketPlace, self).create(vals)
        # create a payment method for sales on this market place
        payment_method = self.env.ref(
            'payment.account_payment_method_electronic_in')
        payment_mode = self.env['account.payment.mode'].create({
            'name': marketplace.name,
            'marketplace_id': marketplace.id,
            'company_id': marketplace.backend_id.company_id.id,
            'bank_account_link': 'variable',
            'payment_method_id': payment_method.id})
        marketplace.write({'payment_mode_id': payment_mode.id})
        return marketplace


class LengowMarketPlaceAdapter(Component):
    _name = 'lengow.market.place.adapter'
    _inherit = 'lengow.adapter'
    _apply_on = 'lengow.market.place'

    _api = "v3.0/marketplaces/"

    def search(self, params, with_account=False):
        return super(LengowMarketPlaceAdapter, self).search(params,
                                                            with_account=True)


class LengowMarketPlaceBatchImporter(Component):
    _name = 'lengow.market.place.batch.importer'
    _inherit = 'lengow.direct.batch.importer'
    _apply_on = 'lengow.market.place'


class LengowMarketPlaceMapper(Component):
    _name = 'lengow.market.place.mapper'
    _inherit = 'lengow.import.mapper'
    _apply_on = 'lengow.market.place'

    direct = [('homepage', 'homepage'),
              ('description', 'description')]

    @mapping
    def name(self, record):
        name = record['name']
        if name is None:
            name = _('Undefined')
        return {'name': name}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class LengowMarketPlaceImporter(Component):
    _name = 'lengow.market.place.importer'
    _inherit = 'lengow.importer'
    _apply_on = 'lengow.market.place'
