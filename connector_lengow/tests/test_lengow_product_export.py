# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import csv
from cStringIO import StringIO
from base64 import b64decode

from . import common


class TestLengowProductBinding(common.SetUpLengowBase20):

    def setUp(self):
        super(TestLengowProductBinding, self).setUp()

    def test_export_products(self):
        """
            Export a product and check result file
        """
        with self.backend.work_on('lengow.product.product') as work:
            products_exporter = work.component(usage='record.exporter')

            products_exporter.run(self.catalogue)

            csv_file = self.env['ir.attachment'].search(
                [('name', '=', self.catalogue.product_filename)])

            datas = b64decode(csv_file.datas)
            reader = csv.DictReader(StringIO(datas),
                                    delimiter=';')

            linesByID = {}
            for line in reader:
                linesByID[line['ID_PRODUCT']] = line

            self.assertEqual(2, len(linesByID))

            lineDict = linesByID['9999_33544']
            expectedDict = {
                'BRAND': '',
                'CATEGORY': 'All > Saleable > Physical',
                'DESCRIPTION': 'A smart description',
                'EAN': '4004764782703',
                'ID_PRODUCT': '9999_33544',
                'NAME_PRODUCT': 'iPod',
                'PRICE_PRODUCT': '40.59',
                'QUANTITY': '26',
                'SUPPLIER_CODE': '',
                'URL_IMAGE': 'url_image',
                'URL_PRODUCT': 'url_product',
                'SALE_PRICE': '',
                'SALE_FROM_DATE': '',
                'SALE_END_DATE': ''}
            self.assertDictEqual(lineDict, expectedDict)

    def test_export_products_lang(self):
        """
            Export a product and check result file
            - Set french as export language
        """
        wiz_lang = self.env['base.language.install'].create(
            {'lang': 'fr_FR'})
        wiz_lang.lang_install()

        self.product2.with_context(lang="fr_FR").write(
            {'name': 'Ipod en français',
             'description_sale': 'Description de vente'})

        fr = self.env['res.lang'].search([('code', '=', 'fr_FR')])
        self.catalogue.write({'default_lang_id': fr.id})

        with self.backend.work_on('lengow.product.product') as work:
            products_exporter = work.component(usage='record.exporter')

            products_exporter.run(self.catalogue)

            csv_file = self.env['ir.attachment'].search(
                [('name', '=', self.catalogue.product_filename)])

            datas = b64decode(csv_file.datas)
            reader = csv.DictReader(StringIO(datas),
                                    delimiter=';')

            linesByID = {}
            for line in reader:
                linesByID[line['ID_PRODUCT']] = line

            self.assertEqual(2, len(linesByID))

            lineDict = linesByID['9999_33544']
            expectedDict = {
                'BRAND': '',
                'CATEGORY': 'Tous > En vente > Physique',
                'DESCRIPTION': 'Description de vente',
                'EAN': '4004764782703',
                'ID_PRODUCT': '9999_33544',
                'NAME_PRODUCT': 'Ipod en français',
                'PRICE_PRODUCT': '40.59',
                'QUANTITY': '26',
                'SUPPLIER_CODE': '',
                'URL_IMAGE': 'url_image',
                'URL_PRODUCT': 'url_product',
                'SALE_PRICE': '',
                'SALE_FROM_DATE': '',
                'SALE_END_DATE': ''
            }
            self.assertDictEqual(lineDict, expectedDict)

    def test_export_products_pricelist(self):
        """
            Export a product and check result file
            - set a pricelist of 10% discount on product
        """
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test Pricelist'
        })
        self.env['product.pricelist.item'].create({
            'name': 'Test Item',
            'pricelist_id': pricelist.id,
            'compute_price': 'formula',
            'applied_on': '1_product',
            'base': 'list_price',
            'product_id': self.product2.id,
            'price_discount': 10.0,
        })
        self.catalogue.write({'product_pricelist_id': pricelist.id})

        wizard = self.env['lengow.discount.wizard'].with_context(
            active_ids=self.catalogue.binded_product_ids.ids).create({
                'discount': 30,
                'discount_type': 'price',
                'discount_start': '2016-11-20',
                'discount_end': '2016-12-20'})
        wizard.action_confirm()

        with self.backend.work_on('lengow.product.product') as work:
            products_exporter = work.component(usage='record.exporter')

            products_exporter.run(self.catalogue)

            csv_file = self.env['ir.attachment'].search(
                [('name', '=', self.catalogue.product_filename)])

            datas = b64decode(csv_file.datas)
            reader = csv.DictReader(StringIO(datas),
                                    delimiter=';')

            linesByID = {}
            for line in reader:
                linesByID[line['ID_PRODUCT']] = line

            self.assertEqual(2, len(linesByID))

            lineDict = linesByID['9999_33544']
            expectedDict = {
                'BRAND': '',
                'CATEGORY': 'All > Saleable > Physical',
                'DESCRIPTION': 'A smart description',
                'EAN': '4004764782703',
                'ID_PRODUCT': '9999_33544',
                'NAME_PRODUCT': 'iPod',
                'PRICE_PRODUCT': '36.53',
                'QUANTITY': '26',
                'SUPPLIER_CODE': '',
                'URL_IMAGE': 'url_image',
                'URL_PRODUCT': 'url_product',
                'SALE_PRICE': '30.0',
                'SALE_FROM_DATE': '2016-11-20',
                'SALE_END_DATE': '2016-12-20'
            }
            self.assertDictEqual(lineDict, expectedDict)
