{
    "name": "IMC: Manufacturing Components BOM",
     'version': '0.1',
    "summary": "Allow only specific group to edit price_unit on sale order lines and clear pricelist on manual price changes.",
    "depends": ['base','mrp','product','stock'],
    "data": [
        'security/ir.model.access.csv',
        "views/sale_order.xml",
    ],
    "license": "LGPL-3",
    "author": "IMC",

}
