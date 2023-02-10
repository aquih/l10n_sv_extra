# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime
import xlsxwriter
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
            dict['percepcion_id'] = [w.percepcion_id.id, w.percepcion_id.name]
            dict['diarios_id'] =[x.id for x in w.diarios_id]

            res = self.env['report.l10n_sv_extra.reporte_compras'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']
            
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte')
            
            hoja.write(0, 0, w.diarios_id[0].company_id.partner_id.name)
            hoja.write(1, 0, 'LIBRO VENTAS COMPRAS')
            hoja.write(3, 0, 'NIT {}'.format(w.diarios_id[0].company_id.partner_id.vat))
            hoja.write(4, 0, 'NRC {}'.format(w.diarios_id[0].company_id.partner_id.numero_registro))
            hoja.write(5, 0, 'MES {} {}'.format(['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'][w.fecha_desde.month-1], w.fecha_desde.day))

            y = 6
            hoja.write(y, 0, 'NO. COR.')
            hoja.write(y, 1, 'FECHA')
            hoja.write(y, 2, 'NO. DE COMPROB.')
            hoja.write(y, 3, 'NÚMERO DE REGISTRO')
            hoja.write(y, 4, 'NIT')
            hoja.write(y, 5, 'NOMBRE DEL PROVEEDOR')
            hoja.write(y, 6, 'COMPRA EXENTA LOCAL')
            hoja.write(y, 7, 'COMPRA EXENTA IMPORT')
            hoja.write(y, 8, 'COMPRA EXENTA INTERN')
            hoja.write(y, 9, 'COMPRA GRAVADA LOCAL')
            hoja.write(y, 10, 'COMPRA GRAVADA IMPORT')
            hoja.write(y, 11, 'COMPRA GRAVADA INTERN')
            hoja.write(y, 12, 'CREDITO FISCAL')
            hoja.write(y, 13, 'TOTAL')
            hoja.write(y, 14, 'PERCEPCION')
            hoja.write(y, 15, 'RETENCIÓN')
            hoja.write(y, 16, 'COMPRA SUJETO EXCLU')
            hoja.write(y, 17, 'IVA TERCEROS')

            correlativo = 1
            mes_actual = ''
            for linea in lineas:
                y += 1
                hoja.write(y, 0, linea['correlativo'])
                hoja.write(y, 1, linea['fecha'].strftime('%d/%m/%Y'))
                hoja.write(y, 2, linea['numero'])
                hoja.write(y, 3, linea['proveedor'].numero_registro)
                hoja.write(y, 4, linea['proveedor'].vat)
                hoja.write(y, 5, linea['proveedor'].name)
                hoja.write(y, 6, 0)
                hoja.write(y, 7, 0)
                hoja.write(y, 8, 0)
                hoja.write(y, 9, linea['compra'] + linea['servicio'])
                hoja.write(y, 10, linea['importacion'])
                hoja.write(y, 11, 0)
                hoja.write(y, 12, linea['iva'])
                hoja.write(y, 13, linea['total'])
                hoja.write(y, 14, linea['percepcion'])
                hoja.write(y, 15, linea['compra_exento'])
                hoja.write(y, 16, 0)
                hoja.write(y, 17, 0)

            y += 1    
            hoja.write(y, 5, 'Totales')
            hoja.write(y, 6, 0)
            hoja.write(y, 7, 0)
            hoja.write(y, 8, 0)
            hoja.write(y, 9, totales['compra']['neto'] + totales['servicio']['neto'])
            hoja.write(y, 10, totales['importacion']['neto'])
            hoja.write(y, 11, 0)
            hoja.write(y, 12, totales['compra']['iva'] + totales['servicio']['iva'] + totales['combustible']['iva'] + totales['importacion']['iva'])
            hoja.write(y, 13, totales['compra']['percepcion'] + totales['servicio']['percepcion'] + totales['combustible']['percepcion'] + totales['importacion']['percepcion'])
            hoja.write(y, 14, totales['compra']['exento'])
            hoja.write(y, 15, totales['compra']['total'] + totales['servicio']['total'] + totales['combustible']['total'] + totales['importacion']['total'] + totales['compra']['exento'])
            hoja.write(y, 16, 0)
            hoja.write(y, 17, 0)
            y += 2
            hoja.write(y, 0, 'RESUMEN DE COMPRAS')
            y += 2
            
            hoja.write(y, 0, 'TOTAL COMPRAS')
            hoja.write(y, 1, totales['compra']['percepcion'] + totales['servicio']['percepcion'] + totales['combustible']['percepcion'] + totales['importacion']['percepcion'])

            y += 1
            hoja.write(y, 0, 'TOTAL N/C')
            hoja.write(y, 1, 0)
            y += 1
            hoja.write(y, 0, 'COMPRAS GRAVADAS')
            hoja.write(y, 1, totales['compra']['neto'] + totales['servicio']['neto'])

            y += 1
            hoja.write(y, 0, 'IVA GRAVADO')
            hoja.write(y, 1, totales['compra']['iva'] + totales['servicio']['iva'] + totales['combustible']['iva'] + totales['importacion']['iva'])
            y += 1
            hoja.write(y, 0, 'PERCEPCION')
            hoja.write(y, 1, totales['compra']['percepcion'] + totales['servicio']['percepcion'] + totales['combustible']['percepcion'] + totales['importacion']['percepcion'])
            y += 1
            hoja.write(y, 0, 'COMPRAS EXENTAS')
            hoja.write(y, 1, 0)
            y += 1
            hoja.write(y, 0, 'COMPRAS EXENTAS IMPORTACIONES')
            hoja.write(y, 1, 0)
            y += 1
            hoja.write(y, 0, 'COMPRAS EXENTAS INTERNACIONES')
            hoja.write(y, 1, 0)
            y += 1
            hoja.write(y, 0, 'COMPRAS GRAVADAS IMPORTACION')
            hoja.write(y, 1, 0)
            y += 1
            hoja.write(y, 0, 'COMPRAS GRAVADAS INTERNACIONES')
            hoja.write(y, 1, 0)
            y += 1
            hoja.write(y, 0, 'COMPRAS SUJETO EXCLUIDOS')
            hoja.write(y, 1, 0)
            y += 1
            hoja.write(y, 0, 'RETENCIONES')
            hoja.write(y, 1, totales['compra']['total'] + totales['servicio']['total'] + totales['combustible']['total'] + totales['importacion']['total'] + totales['compra']['exento'])
            y += 1
            hoja.write(y, 0, 'TOTAL DE COMPRAS')
            hoja.write(y, 1, totales['compra']['percepcion'] + totales['servicio']['percepcion'] + totales['combustible']['percepcion'] + totales['importacion']['percepcion'])
            y += 1
            hoja.write(y, 0, 'TOTAL DE IMPUESTOS')
            hoja.write(y, 1, totales['compra']['iva'] + totales['servicio']['iva'] + totales['combustible']['iva'] + totales['importacion']['iva'] + totales['compra']['total'] + totales['servicio']['total'] + totales['combustible']['total'] + totales['importacion']['total'] + totales['compra']['exento'])
            y += 1
            
            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'libro_de_compras.xlsx'})

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
