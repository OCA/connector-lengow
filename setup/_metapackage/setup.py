import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-connector-lengow",
    description="Meta package for oca-connector-lengow Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-connector_lengow',
        'odoo10-addon-connector_lengow_amazon',
        'odoo10-addon-connector_lengow_fnac',
        'odoo10-addon-connector_lengow_naturedecouvertes',
        'odoo10-addon-connector_lengow_teeps',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
