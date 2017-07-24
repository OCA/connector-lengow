# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
from cStringIO import StringIO
import csv
from collections import OrderedDict
import logging
_logger = logging.getLogger(__name__)
try:
    import ftputil.session
except (ImportError, IOError) as err:
    _logger.debug(err)

from odoo import api, fields, models
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class LengowProductProduct(models.Model):
    _name = 'lengow.product.product'
    _inherit = 'lengow.binding'
    _inherits = {'product.product': 'odoo_id'}
    _description = 'Lengow Product'

    catalogue_id = fields.Many2one(comodel_name='lengow.catalogue',
                                   string='Lengow Catalogue',
                                   required=True,
                                   ondelete='restrict')
    odoo_id = fields.Many2one(comodel_name='product.product',
                              string='Product',
                              required=True,
                              ondelete='restrict')
    lengow_qty = fields.Float(string='Computed Stock Quantity',
                              help="Last computed quantity to send "
                                   "on Lengow.")
    active = fields.Boolean(default=True)
    lengow_price = fields.Float('Price',
                                compute='_compute_price',
                                compute_sudo=False,
                                store=False)
    sale_price = fields.Float('Promo Price')
    sale_from_date = fields.Date('Promo Start Date')
    sale_end_date = fields.Date('Promo End Date')

    _sql_constraints = [
        ('lengow_uniq_catalog', 'unique(backend_id, catalogue_id, lengow_id)',
         'This product is already binded to this catalogue'),
    ]

    @job(default_channel='root.lengow')
    @api.multi
    def export_products(self, catalogue_id):
        with catalogue_id.backend_id.work_on('lengow.product.product') as work:
            exporter = work.component(usage='record.exporter')
            res = exporter.run(catalogue_id)
            return res

    @api.multi
    def compute_lengow_qty(self):
        for product in self:
            if product.catalogue_id.product_stock_field_id:
                stock_field = product.catalogue_id.product_stock_field_id.name
            else:
                stock_field = 'virtual_available'

            location = self.env['stock.location']
            if self.env.context.get('location'):
                location = location.browse(self.env.context['location'])
            else:
                location = product.catalogue_id.warehouse_id.lot_stock_id

            product.sudo().write({'lengow_qty':
                                  product.with_context(location=location.id)
                                  [stock_field]})

    @api.multi
    def _compute_price(self):
        for product in self:
            product_pricelist_id = product.catalogue_id.product_pricelist_id.id
            if product_pricelist_id:
                product.lengow_price = product.with_context(
                    pricelist=product_pricelist_id).price
            else:
                product.lengow_price = product.lst_price


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _search_lengow_catalogue_ids(self, operator, value):
        lengow_prod_obj = self.env['lengow.product.product']
        bindings = lengow_prod_obj.search(
            [('catalogue_id.name', operator, value)])

        return [('id', 'in',
                 bindings.mapped('odoo_id').ids)]

    lengow_bind_ids = fields.One2many(
        comodel_name='lengow.product.product',
        inverse_name='odoo_id',
        string='Lengow Bindings',
    )
    lengow_catalogue_ids = fields.Many2many(
        string='Lengow Catalogues',
        comodel_name='lengow.catalogue',
        compute='_compute_catalogue_ids',
        store=False,
        search=_search_lengow_catalogue_ids)

    product_url = fields.Char()
    image_url = fields.Char()

    @api.multi
    def _compute_catalogue_ids(self):
        for product in self:
            product.lengow_catalogue_ids = [binding.catalogue_id.id for binding
                                            in product.lengow_bind_ids]

    @api.multi
    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if 'active' in vals and not vals.get('active'):
            bind_records = self.env['lengow.product.product'].search(
                [('odoo_id', 'in', self.ids)])
            if bind_records:
                bind_records.write({'active': vals.get('active')})
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _search_lengow_catalogue_ids(self, operator, value):
        lengow_prod_obj = self.env['lengow.product.product']
        bindings = lengow_prod_obj.search(
            [('catalogue_id.name', operator, value)])

        return [('id', 'in',
                 bindings.mapped('odoo_id.product_tmpl_id').ids)]

    lengow_catalogue_ids = fields.Many2many(
        string='Lengow Catalogues',
        comodel_name='lengow.catalogue',
        related='product_variant_ids.lengow_catalogue_ids',
        store=False,
        search=_search_lengow_catalogue_ids)


class LengowProductExportMapper(Component):
    _name = 'lengow.product.export.mapper'
    _inherit = 'lengow.export.mapper'
    _apply_on = 'lengow.product.product'

    direct = []

    @mapping
    def ID_PRODUCT(self, record):
        return {'ID_PRODUCT': record.lengow_id}

    @mapping
    def NAME_PRODUCT(self, record):
        return {'NAME_PRODUCT': record.name}

    @mapping
    def DESCRIPTION(self, record):
        return {'DESCRIPTION': record.description_sale or record.name}

    @mapping
    def PRICE_PRODUCT(self, record):
        price_product = round(record.lengow_price, 2) if record.lengow_price \
            else ''
        return {'PRICE_PRODUCT': price_product}

    @mapping
    def CATEGORY(self, record):
        cat = record.categ_id.display_name or ''
        cat = cat.replace('/', '>')
        return {'CATEGORY': cat}

    @mapping
    def URL_PRODUCT(self, record):
        return {'URL_PRODUCT': record.product_url or ''}

    @mapping
    def URL_IMAGE(self, record):
        return {'URL_IMAGE': record.image_url or ''}

    @mapping
    def EAN(self, record):
        return {'EAN': record.barcode or ''}

    @mapping
    def SUPPLIER_CODE(self, record):
        supplier_code = record.seller_ids[0].product_code or '' if \
            record.seller_ids else ''
        return {'SUPPLIER_CODE': supplier_code}

    @mapping
    def BRAND(self, record):
        return {'BRAND': ''}

    @mapping
    def QUANTITY(self, record):
        qty = int(record.lengow_qty)
        return {'QUANTITY': qty}

    @mapping
    def SALE_PRICE(self, record):
        return {'SALE_PRICE': record.sale_price or ''}

    @mapping
    def SALE_FROM_DATE(self, record):
        return {'SALE_FROM_DATE': record.sale_from_date or ''}

    @mapping
    def SALE_END_DATE(self, record):
        return {'SALE_END_DATE': record.sale_end_date or ''}


class LengowProductAdapter(Component):
    _name = 'lengow.product.adapter'
    _inherit = 'lengow.adapter20'
    _apply_on = 'lengow.product.product'

    _DataMap = {'ID_PRODUCT': 0,
                'NAME_PRODUCT': 1,
                'DESCRIPTION': 2,
                'PRICE_PRODUCT': 3,
                'CATEGORY': 4,
                'URL_PRODUCT': 5,
                'URL_IMAGE': 6,
                'EAN': 7,
                'SUPPLIER_CODE': 8,
                'BRAND': 9,
                'QUANTITY': 10,
                'SALE_PRICE': 11,
                'SALE_FROM_DATE': 12,
                'SALE_END_DATE': 13}

    def getCSVFromRecord(self, record):
        values = []
        data = OrderedDict(sorted(self._DataMap.items(), key=lambda r: r[1]))
        for attr, _ in data.items():
            if attr in record:
                val = record[attr]
                if isinstance(val, unicode):
                    try:
                        val = val.encode('utf-8')
                    except UnicodeError:
                        pass  # pragma: nocover
                values.append(val)

        return values

    def getCSVHeader(self):
        header = OrderedDict(sorted(self._DataMap.items(), key=lambda r: r[1]))
        return header.keys()


class LengowProductExporter(Component):
    _name = 'lengow.product.exporter'
    _inherit = 'lengow.exporter'
    _apply_on = 'lengow.product.product'

    def uploadFTP(self, catalogue, ir_attachment):
        port_session_factory = ftputil.session.session_factory(
            port=int(catalogue.product_ftp_port))
        with ftputil.FTPHost(catalogue.product_ftp_host,
                             catalogue.product_ftp_user,
                             catalogue.product_ftp_password,
                             session_factory=port_session_factory) as ftp_conn:
            target_name = catalogue.product_ftp_directory\
                + '/' + ir_attachment.datas_fname
            with ftp_conn.open(target_name, mode='wb') as fileobj:
                fileobj.write(base64.b64decode(ir_attachment.datas))

    def run(self, catalogue=None):
        data = None
        adapter = self.component(usage='backend.adapter')
        csvFile = StringIO()
        csvRows = [adapter.getCSVHeader()]
        products = catalogue.binded_product_ids
        products.compute_lengow_qty()
        if catalogue.default_lang_id:
            lang = catalogue.default_lang_id.code
        else:
            lang = self.env.user.lang or 'en_US'
        for product in products.with_context(lang=lang):
            self._lengow_record = product
            map_record = self._map_data()
            vals = self.export(map_record)
            csvRows.append(adapter.getCSVFromRecord(vals))

        wr = csv.writer(csvFile, quoting=csv.QUOTE_ALL, delimiter=';')
        wr.writerows(csvRows)

        job_uuid = self.env.context.get('job_uuid', False)
        exp_job = self.env['queue.job'].sudo().search(
            [('uuid', '=', job_uuid)], limit=1)

        attach_data = {'name': catalogue.product_filename,
                       'datas': base64.encodestring(csvFile.getvalue()),
                       'datas_fname': catalogue.product_filename}
        if exp_job:
            attach_data.update({'res_model': 'queue.job',
                                'res_id': exp_job.id})

        ir_attachment = self.env['ir.attachment'].create(
            attach_data)

        if catalogue.product_ftp:
            self.uploadFTP(catalogue, ir_attachment)

        catalogue.sudo().write({'last_export_date': fields.Datetime.now()})
        return data
