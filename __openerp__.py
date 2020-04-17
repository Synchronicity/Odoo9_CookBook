# -*- coding: utf-8 -*-
{
    'name': 'Chapter 04 code',
    'summary': "Gestion de bibliothèque",
    'description': """Long description
                    Sur plusieurs lignes...
                    Et dautres encore...""",
    'author': "JLS",
    'license': "AGPL-3",
    'website': "http://192.168.56.102:8069/web",
    'category': 'Library',
    'version': '9.0c',
    'depends': ['base', 'decimal_precision'],
    'data': [
        'security/library_security.xml',
        'security/ir.model.access.csv',
        'views/library_book.xml',
    ],
}
