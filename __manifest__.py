{
    'name': 'Zalo OA Integration',
    'version': '13.0.1.0.1',
    'license': 'AGPL-3',
    'summary': 'Zalo OA Integration',
    'description': '',
    'author': 'Zalo OA NOS',
    'company': 'NOS ERP',
    'maintainer': '',
    'website': 'https://www.nostech.vn/',
    'depends': ['base', 'account', 'sale_management', 'mass_mailing'],
    'data': [
        # data
        'data/ir_cron.xml',
        'data/data.xml',
        # security
        'security/ir.model.access.csv',
        # menu
        'views/zalo_menu.xml',
        # views
        'views/zalo_oa_transaction_views.xml',   
        'views/zalo_oa_views.xml',
        'views/res_config_settings_views.xml',
        'views/zns_templates.xml',
        'views/zns_messages_views.xml',
        'views/zns_campaign_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/pos_order_views.xml',
        'views/zalo_connector_security.xml',
        # 'views/account_move_views.xml',
        'wizard/schedule_date_campaign_views.xml',
        'wizard/send_zns_template_views.xml',
        'wizard/create_zns_template_views.xml',
        
    ],
    'installable': True,
    'application': True,
    'qweb': [],
    'auto_install': False,
    'sequence':2,
}
