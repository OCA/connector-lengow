# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields
import odoo.tests.common as common


class SetUpLengowBase(common.TransactionCase):
    """ Base class - Test the imports from a Lengow Mock.
    """

    def _configure_mock_request(self, key, mock_request):
        data = self.json_data
        mock_request.return_value.status_code = data[key]['status_code']
        mock_request.return_value.json.return_value = data[key]['json']
        return mock_request

    def setUp(self):
        super(SetUpLengowBase, self).setUp()
        self.backend_model = self.env['lengow.backend']
        self.catalogue_model = self.env['lengow.catalogue']
        self.marketplace_model = self.env['lengow.market.place']
        self.bind_wizard_model = self.env['lengow.product.binding.wizard']
        self.unbind_wizard_model = self.env['lengow.product.unbinding.wizard']
        self.product_bind_model = self.env['lengow.product.product']

        self.warehouse = self.env.ref('stock.warehouse0')
        self.fiscal_position = self.env['account.fiscal.position'].create(
            {'name': 'TEST'})
        self.post_method = 'odoo.addons.connector_lengow.components'\
                           '.adapter.requests.post'
        self.get_method = 'odoo.addons.connector_lengow.components'\
                          '.adapter.requests.get'
        self.json_data = {}
        self.component_builder = self.env['component.builder']
        self.component_builder._register_hook()
        self.component_builder.load_components('connector_lengow')


class SetUpLengowBase20(SetUpLengowBase):

    def setUp(self):
        super(SetUpLengowBase20, self).setUp()

        self.backend = self.backend_model.create(
            {'name': 'Test Lengow',
             'version': '2.0',
             'location': 'http://anyurl',
             'wsdl_location': 'http://anywsdlurl',
             'id_client': 'a4a506440102b8d06a0f63fdd1eadd5f',
             'warehouse_id': self.warehouse.id,
             'fiscal_position_id': self.fiscal_position.id}
        )

        self.amazon_analytic = self.env['account.analytic.account'].create(
            {'name': 'Amazon Sales'})

        self.marketplace = self.marketplace_model.create(
            {'backend_id': self.backend.id,
             'name': 'Amazon',
             'lengow_id': 'amazon',
             'specific_account_analytic_id': self.amazon_analytic.id,
             'sale_prefix_code': 'AMAZON'})

        self.catalogue = self.catalogue_model.create(
            {'name': 'Test Lengow Catalogue',
             'backend_id': self.backend.id,
             'product_ftp': False,
             'product_filename': 'products.csv',
             'warehouse_id': self.warehouse.id})

        self.json_data = {
            'orders': {
                'status_code': 200,
                'json': {
                    "orders_count": {
                        "count_total": "435",
                        "count_by_marketplace": {
                            "spartoo": "33",
                            "amazon": "287",
                            "cdiscount": "110",
                            "rueducommerce": "4",
                            "priceminister": "1"
                        },
                        "count_by_status": {
                            "cancel": "4",
                            "new": "0",
                            "shipped": "414",
                            "processing": "17"
                        }
                    },
                    "orders": [{
                        "marketplace": "amazon",
                        "idFlux": "99128",
                        "order_status": {
                            "marketplace": "accept",
                            "lengow": "processing"
                        },
                        "order_id": "999-2121515-6705141",
                        "order_mrid": "999-2121515-6705141",
                        "order_refid": "999-2121515-6705141",
                        "order_external_id": "99341",
                        "order_purchase_date": fields.Date.today(),
                        "order_purchase_heure": "04:51:24",
                        "order_amount": "305.65",
                        "order_tax": "0.00",
                        "order_shipping": "5.9",
                        "order_commission": "0.0",
                        "order_processing_fee": "0",
                        "order_currency": "EUR",
                        "order_payment": {
                            "payment_checkout": "",
                            "payment_status": "",
                            "payment_type": "",
                            "payment_date": fields.Date.today(),
                            "payment_heure": "04:51:24"
                        },
                        "order_invoice": {
                            "invoice_number": "",
                            "invoice_url": ""
                        },
                        "billing_address": {
                            "billing_society": "",
                            "billing_civility": "",
                            "billing_lastname": "Lengow A",
                            "billing_firstname": "",
                            "billing_email": "LengowA@marketplace."
                                             "amazon.de",
                            "billing_address": "Lengow",
                            "billing_address_2": "",
                            "billing_address_complement": "Lengow",
                            "billing_zipcode": "44000",
                            "billing_city": "Nantes",
                            "billing_country": "FR",
                            "billing_country_iso": "FR",
                            "billing_phone_home": "099999689492",
                            "billing_phone_office": "",
                            "billing_phone_mobile": "099999689493",
                            "billing_full_address": "Lengow"
                        },
                        "delivery_address": {
                            "delivery_society": "",
                            "delivery_civility": "",
                            "delivery_lastname": "Lengow B",
                            "delivery_firstname": "",
                            "delivery_email": "",
                            "delivery_address": "Lengow",
                            "delivery_address_2": "",
                            "delivery_address_complement": "Lengow",
                            "delivery_zipcode": "44000",
                            "delivery_city": "Nantes",
                            "delivery_country": "FR",
                            "delivery_country_iso": "FR",
                            "delivery_phone_home": "099999689492",
                            "delivery_phone_office": "",
                            "delivery_phone_mobile": "",
                            "delivery_full_address": "Lengow"
                        },
                        "tracking_informations": {
                            "tracking_method": "",
                            "tracking_carrier": "Standard",
                            "tracking_number": "",
                            "tracking_url": "",
                            "tracking_shipped_date": "2016-10-01"
                                                     " 09:32:16",
                            "tracking_relay": "",
                            "tracking_deliveringByMarketPlace": "1",
                            "tracking_parcel_weight": ""
                        },
                        "order_comments": "",
                        "customer_id": "",
                        "order_ip": "",
                        "order_items": "1",
                        "cart": {
                            "nb_orders": "1",
                            "products": [{
                                "idLengow": "9999_33543",
                                "idMP": "9999_33543",
                                "sku": "9999_33543",
                                "ean": "",
                                "title": "Pantalon G-star rovic slim, micro "
                                         "stretch twill GS Dk Fig Taille "
                                         "W29/L32",
                                "category": "Accueil > HOMME > JEANS/PANTALONS"
                                            " > PANTALONS",
                                "brand": "",
                                "url_product": "http://lengow.com/product.php"
                                               "?id\\_product=11199",
                                "url_image": "http://lengow.com/img/p/"
                                             "11199-42104-large.jpg",
                                "order_lineid": "",
                                "quantity": "2",
                                "price": "199.8",
                                "price_unit": "99.90",
                                "shipping_price": "",
                                "tax": "",
                                "status": ""
                            }, {
                                "idLengow": "9999_33544",
                                "idMP": "9999_33544",
                                "sku": "9999_33544",
                                "ean": "",
                                "title": "Pantalon G-star rovic slim, micro "
                                         "stretch twill GS Dk Fig Taille "
                                         "W30/L33",
                                "category": "Accueil > HOMME > JEANS/PANTALONS"
                                            " > PANTALONS",
                                "url_product": "http://lengow.com/product.php"
                                               "?id\\_product=11198",
                                "url_image": "http://lengow.com/img/p/"
                                             "11199-42102-large.jpg",
                                "quantity": "1",
                                "order_lineid": "",
                                "price": "99.95",
                                "price_unit": "99.95",
                                "shipping_price": "",
                                "tax": "",
                                "status": ""
                            }]}}]
                }
            }}
        self.product1 = self.env.ref('product.product_product_9')
        self.product2 = self.env.ref('product.product_product_11')
        self.product1.write({'default_code': '9999_33543'})
        self.product2.write({'default_code': '9999_33544',
                             'barcode': '4004764782703',
                             'description_sale': 'A smart description',
                             'list_price': 40.59,
                             'product_url': 'url_product',
                             'image_url': 'url_image'})
        bind_wizard = self.bind_wizard_model.create(
            {'catalogue_id': self.catalogue.id,
             'product_ids': [(6, 0, [self.product1.id, self.product2.id])]})
        bind_wizard.bind_products()
        journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        self.marketplace.payment_mode_id.write({
            'bank_account_link': 'fixed',
            'fixed_journal_id': journal.id})
        self.route = self.env['stock.location.route'].create({
            'name': 'Amazon Delivery',
            'sale_selectable': True})
        self.marketplace.write({'route_id': self.route.id})
        sale_wkf = self.env.ref('sale_automatic_workflow.automatic_validation')
        sale_wkf.write({'register_payment': True})
        self.marketplace.payment_mode_id.write({
            'workflow_process_id': sale_wkf.id})


class SetUpLengowBase30(SetUpLengowBase):

    def setUp(self):
        super(SetUpLengowBase30, self).setUp()
        self.backend = self.backend_model.create(
            {'name': 'Test Lengow',
             'version': '3.0',
             'location': 'http://anyurl',
             'access_token': 'a4a506440102b8d06a0f63fdd1eadd5f',
             'secret': '66eb2d56a4e930b0e12193b954d6b2e4',
             'warehouse_id': self.warehouse.id}
        )
        self.expected_token = "6b7280eb-e7d4-4b94-a829-7b3853a20126"
        self.expected_user = "1"
        self.expected_account = 1
        self.json_data = {
            'token': {
                'status_code': 200,
                'json': {
                    'token': self.expected_token,
                    'user_id': self.expected_user,
                    'account_id': self.expected_account}},
            'token_fail': {
                'status_code': 400,
                'json': {
                    "error": {
                        "code": 403,
                        "message": "Forbidden"}}},
            'marketplace': {
                'status_code': 200,
                'json': {
                    'admarkt': {
                        'country': 'NLD',
                        'description': 'Admarkt is a Dutch marketplace which'
                                       ' lets you generate qualified traffic'
                                       ' to your online shop.',
                        'homepage': 'http://www.marktplaatszakelijk.nl/'
                                    'admarkt/',
                        'logo': 'cdn/partners//_.jpeg',
                        'name': 'Admarkt',
                        'orders': {'actions': {},
                                   'carriers': {},
                                   'status': {}}},
                    'amazon_fr': {
                        'country': 'FRA',
                        'description': 'Coming soon : description',
                        'homepage': 'http://www.amazon.com/',
                        'logo': 'http://psp-img.gamergen.com/'
                                'amazon-fr-logo_027200C800342974.jpg',
                        'name': 'Amazon FR',
                        'orders': {
                            'actions': {
                                'accept': {
                                    'args': [],
                                    'optional_args': [],
                                    'status': ['new']},
                                'cancel': {
                                    'args': ['cancel_reason'],
                                    'optional_args': [],
                                    'status': ['new',
                                               'waiting_shipment',
                                               'shipped']},
                                'partially_cancel': {
                                    'args': ['line', 'cancel_reason'],
                                    'optional_args': [],
                                    'status': ['new',
                                               'waiting_shipment']},
                                'partially_refund': {
                                    'args': ['line', 'refund_reason'],
                                    'optional_args': [],
                                    'status': ['shipped']},
                                'ship': {
                                    'args': [],
                                    'optional_args': ['line',
                                                      'shipping_date',
                                                      'carrier',
                                                      'tracking_number',
                                                      'shipping_method'],
                                    'status': ['waiting_shipment']}},
                            'carriers': {},
                            'status': {
                                'canceled': ['Canceled'],
                                'new': ['PendingAvailability', 'Pending'],
                                'shipped': ['Shipped', 'InvoiceUnconfirmed'],
                                'waiting_shipment': ['Unshipped',
                                                     'PartiallyShipped',
                                                     'Unfulfillable']}}}}}}
