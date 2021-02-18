# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime
#import xlwt
import base64
import io
import logging

class AsistenteReporteCompras(models.TransientModel):
    _name = 'l10n_sv_extra.asistente_reporte_compras'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuesto_id = fields.Many2one("account.tax", string="Impuesto", required=True)
    percepcion_id = fields.Many2one("account.tax", string="Percepción", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_sv_extra.asistente_reporte_compras',
             'form': self.read()[0]
        }
        logging.warn(data)
        return self.env.ref('l10n_sv_extra.action_reporte_compras').report_action(self, data=data)

    def print_report_excel(self):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['impuesto_id'] = [w.impuesto_id.id, w.impuesto_id.name]
            dict['diarios_id'] =[x.id for x in w.diarios_id]

            res = self.env['report.l10n_sv_extra.reporte_compras'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']
            libro = xlwt.Workbook()
            hoja = libro.add_sheet('reporte')

            xlwt.add_palette_colour("custom_colour", 0x21)
            libro.set_colour_RGB(0x21, 200, 200, 200)
            estilo = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
            hoja.write(0, 0, 'LIBRO DE COMPRAS Y SERVICIOS')
            hoja.write(2, 0, 'NUMERO DE IDENTIFICACION TRIBUTARIA')
            hoja.write(2, 1, w.diarios_id[0].company_id.partner_id.vat)
            hoja.write(3, 0, 'NOMBRE COMERCIAL')
            hoja.write(3, 1, w.diarios_id[0].company_id.partner_id.name)
            hoja.write(2, 3, 'DOMICILIO FISCAL')
            hoja.write(2, 4, w.diarios_id[0].company_id.partner_id.street)
            hoja.write(3, 3, 'REGISTRO DEL')
            hoja.write(3, 4, str(w.fecha_desde) + ' al ' + str(w.fecha_hasta))

            y = 5

            hoja.write(y, 6, 'Compra')
            hoja.write(y, 7, 'exenta')
            hoja.write(y, 8, 'Compra')
            hoja.write(y, 9, 'gravada')

            y = 6
            hoja.write(y, 0, 'Correlativo')
            hoja.write(y, 1, 'Fecha')
            hoja.write(y, 2, '# Comprobante')
            hoja.write(y, 3, 'NIT')
            hoja.write(y, 4, 'Registro')
            hoja.write(y, 5, 'Cliente')
            hoja.write(y, 6, 'Interna')
            hoja.write(y, 7, 'Importación')
            hoja.write(y, 8, 'Interna')
            hoja.write(y, 9, 'Importación')
            hoja.write(y, 10, 'IVA')
            hoja.write(y, 11, 'Total')
            hoja.write(y, 12, 'Retención')
            hoja.write(y, 13, 'Retención 2%')
            hoja.write(y, 14, 'IVA terceros')

            correlativo = 1
            mes_actual = ''
            for linea in lineas:
                if mes_actual != datetime.strftime(linea['fecha'], '%Y-%m'):
                    mes_actual = datetime.strftime(linea['fecha'], '%Y-%m')
                    correlativo = 1

                y += 1
                hoja.write(y, 0, correlativo)
                correlativo += 1
                hoja.write(y, 1, str(linea['fecha']))
                hoja.write(y, 2, linea['numero'])
                hoja.write(y, 3, linea['proveedor']['vat'])
                hoja.write(y, 4, linea['proveedor']['numero_registro'])
                hoja.write(y, 5, linea['proveedor']['name'])
                hoja.write(y, 6, '-')
                hoja.write(y, 7, '-')
                hoja.write(y, 8, linea['compra'])
                hoja.write(y, 9, linea['importacion'])
                hoja.write(y, 10, linea['iva'])
                hoja.write(y, 11, linea['total'])
                hoja.write(y, 12, linea['compra_exento'])
                hoja.write(y, 13, '-')
                hoja.write(y, 14, '-')

            y += 1
            hoja.write(y, 3, 'Totales')
            hoja.write(y, 6, '-')
            hoja.write(y, 7, '-')
            hoja.write(y, 8, totales['compra']['neto'])
            hoja.write(y, 9, totales['importacion']['neto'])
            hoja.write(y, 10, totales['compra']['iva'] + totales['servicio']['iva'] + totales['combustible']['iva'] + totales['importacion']['iva'])
            hoja.write(y, 11, totales['compra']['total'] + totales['servicio']['total'] + totales['combustible']['total'] + totales['importacion']['total'])
            hoja.write(y, 12, totales['compra']['exento'])
            hoja.write(y, 13, '-')
            hoja.write(y, 14, '-')

            f = io.BytesIO()
            libro.save(f)
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'libro_de_compras.xls'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_sv_extra.asistente_reporte_compras',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
