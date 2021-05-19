{
    'name': 'Product stock/price connector',
    'version': '18.5',
    'summary': 'send the new quantites and new prices of the product and recieve sale orders from'
               'a web service',
    'description': 'This module will send a post request to a web service that has its url defined in the '
                   'company form whenever a quantity or the price of a product is changed. as well as the '
                   'purpose of this module is to create sale orders comming from external post requests.',
    'category': '',
    'author': '',
    'website': '',
    'license': '',
    'depends': ['base', 'product', 'stock', 'sale'],
    'data': [
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/product.xml',
    ],
    #   'demo': [''],
    'installable': True,
    'auto_install': False,
    # 'external_dependencies': {
    #     'python': [''],
    # }
}
