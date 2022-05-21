# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from restapi.models import Category


class CategoryTestCase(TestCase):
    def setUp(self):
        Category.objects.create(name="Learning")
        Category.objects.create(name="Teaching")

    def test_category_can_print(self):
        """Check if Category prints correctly"""
        learning = Category.objects.get(name="Learning")
        teaching = Category.objects.get(name="Teaching")
        self.assertEqual(str(learning), 'Category: Learning')
        self.assertEqual(str(teaching), 'Category: Teaching')
