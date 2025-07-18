# -*- encoding: utf-8 -*-

{
    'name': 'El Salvador - Reportes y funcionalidad extra',
    'version': '1.1',
    'category': 'Localization',
    'description': """ Reportes requeridos y otra funcionalidad extra para llevar un contabilidad en El Salvador. """,
    'author': 'Aquih, S.A.',
    'website': 'http://aquih.com/',
    'depends': ['l10n_sv'],
    'data': [
        'views/account_views.xml',
        'report/report_views.xml',
        'report/reporte_ventas_views.xml',
        'report/reporte_compras_views.xml',
        'report/reporte_mayor_views.xml',
        'report/reporte_kardex_views.xml',
        'wizard/asistente_kardex_views.xml',
        'wizard/asistente_reporte_compras_views.xml',
        'wizard/asistente_reporte_mayor_views.xml',
        'wizard/asistente_reporte_ventas_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
