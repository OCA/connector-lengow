# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from . import common


class TestLengowProductDiscuunt(common.SetUpLengowBase20):

    def setUp(self):
        super(TestLengowProductDiscuunt, self).setUp()

    def test_product_discount_percent_wrong_date(self):
        with self.assertRaises(ValidationError):
            self.env['lengow.discount.wizard'].with_context(
                active_ids=self.catalogue.binded_product_ids.ids
            ).create({
                'discount': 30,
                'discount_start': '2016-11-20',
                'discount_end': '2016-10-20'})

    def test_product_discount_percent_wrong_percent(self):
        with self.assertRaises(ValidationError):
            self.env['lengow.discount.wizard'].with_context(
                active_ids=self.catalogue.binded_product_ids.ids
            ).create({
                'discount': 120,
                'discount_start': '2016-11-20',
                'discount_end': '2016-12-20'})

    def test_product_discount_percent(self):
        wizard = self.env['lengow.discount.wizard'].with_context(
            active_ids=self.catalogue.binded_product_ids.ids).create({
                'discount': 30,
                'discount_start': '2016-11-20',
                'discount_end': '2016-12-20'})
        wizard.action_confirm()
        for lengow_product in self.catalogue.binded_product_ids:
            self.assertEqual(lengow_product.sale_from_date,
                             '2016-11-20')
            self.assertEqual(lengow_product.sale_end_date,
                             '2016-12-20')
            discount_price = lengow_product.lengow_price - (
                (lengow_product.lengow_price * wizard.discount) / 100.0)
            self.assertAlmostEqual(lengow_product.sale_price, discount_price)

    def test_product_discount_price(self):
        wizard = self.env['lengow.discount.wizard'].with_context(
            active_ids=self.catalogue.binded_product_ids.ids).create({
                'discount': 30,
                'discount_type': 'price',
                'discount_start': '2016-11-20',
                'discount_end': '2016-12-20'})
        wizard.action_confirm()
        for lengow_product in self.catalogue.binded_product_ids:
            self.assertEqual(lengow_product.sale_from_date,
                             '2016-11-20')
            self.assertEqual(lengow_product.sale_end_date,
                             '2016-12-20')
            self.assertAlmostEqual(lengow_product.sale_price, 30)

    def test_product_reset_discount(self):
        wiz_env = self.env['lengow.discount.wizard']
        wizard = wiz_env.with_context(
            active_ids=self.catalogue.binded_product_ids.ids).create({
                'discount': 30,
                'discount_type': 'price',
                'discount_start': '2016-11-20',
                'discount_end': '2016-12-20'})
        wizard.action_confirm()
        lengow_product_ids = self.catalogue.binded_product_ids.ids
        wizard = wiz_env.with_context(reset=True,
                                      active_ids=lengow_product_ids).create({})
        wizard.action_confirm()
        for lengow_product in self.catalogue.binded_product_ids:
            self.assertEqual(lengow_product.sale_from_date, False)
            self.assertEqual(lengow_product.sale_end_date, False)
            self.assertAlmostEqual(lengow_product.sale_price, 0.0)
