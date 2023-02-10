# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io

class AsistenteReporteVentas(models.TransientModel):
    _name = 'l10n_sv_extra.asistente_reporte_ventas'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuesto_id = fields.Many2one("account.tax", string="Impuesto", required=True)
    iva_retenido_id = fields.Many2one("account.tax", string="IVA retenido", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    resumido = fields.Boolean(string="Resumido")
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def print_report_contribuyente(self):
        self.resumido = False
        data = {
             'ids': [],
             'model': 'l10n_sv_extra.asistente_reporte_ventas',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_sv_extra.action_reporte_ventas').report_action(self, data=data)

    def print_report_consumidor_final(self):
        self.resumido = True
        data = {
             'ids': [],
             'model': 'l10n_sv_extra.asistente_reporte_ventas',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_sv_extra.action_reporte_ventas').report_action(self, data=data)

    def print_report_excel_contribuyente(self):
        self.resumido = False
        return self.print_report_excel(False)
    
    def print_report_excel_consumidor_final(self):
        self.resumido = True
        return self.print_report_excel(True)

    def print_report_excel(self, resumido):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['impuesto_id'] = [w.impuesto_id.id, w.impuesto_id.name]
            dict['iva_retenido_id'] = [w.iva_retenido_id.id, w.iva_retenido_id.name]
            dict['diarios_id'] =[x.id for x in w.diarios_id]
            dict['resumido'] = w['resumido']
            
            res = self.env['report.l10n_sv_extra.reporte_ventas'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']
            
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte')

            hoja.write(0, 0, w.diarios_id[0].company_id.partner_id.name)
            hoja.write(1, 0, 'LIBRO VENTAS CONTRIBUYENTES' if resumido == False else 'LIBRO VENTAS CONSUMIDOR FINAL')
            hoja.write(3, 0, 'NIT {}'.format(w.diarios_id[0].company_id.partner_id.vat))
            hoja.write(4, 0, 'NRC {}'.format(w.diarios_id[0].company_id.partner_id.numero_registro))
            hoja.write(5, 0, 'MES {} {}'.format(['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'][w.fecha_desde.month-1], w.fecha_desde.day))

            y = 6
            if resumido == False:
                #Libro de ventas Contribuyente
                hoja.write(y, 0, 'No. COR.')
                hoja.write(y, 1, 'FECHA')
                hoja.write(y, 2, 'NUMERO COMP.')
                hoja.write(y, 3, 'NOMBRE DEL CLIENTE')
                hoja.write(y, 4, 'NUMERO DE REGISTRO')
                hoja.write(y, 5, 'VENTAS EXENTAS')
                hoja.write(y, 6, 'VENTAS NO SUJETAS')
                hoja.write(y, 7, 'VENTAS GRAVADAS')
                hoja.write(y, 8, 'DEBITO FISCAL')
                hoja.write(y, 9, 'TERCEROS VENTAS')
                hoja.write(y, 10, 'TERCEROS IVA')
                hoja.write(y, 11, 'IVA RETENIDO')
                hoja.write(y, 12, 'VENTA TOTAL')
            else:
                hoja.write(y, 0, 'FECHA')
                hoja.write(y, 1, 'NUMERO')
                hoja.write(y, 2, 'VENTAS EXENTAS')
                hoja.write(y, 3, 'VENTAS NO SUJETAS')
                hoja.write(y, 4, 'VENTAS GRAVADAS LOCALES')
                hoja.write(y, 5, 'VENTAS GRAVADAS EXPORTACIONES')
                hoja.write(y, 6, 'VENTA TOTAL')
                hoja.write(y, 7, 'RET. 1%')
                hoja.write(y, 8, 'VENTA POR TERCEROS')

            for linea in lineas:
                y += 1
                if resumido == False:
                    hoja.write(y, 0, linea['correlativo'])
                    hoja.write(y, 1, linea['fecha'].strftime('%d/%m/%Y'))
                    hoja.write(y, 2, linea['numero'])
                    hoja.write(y, 3, linea['cliente'])
                    hoja.write(y, 4, linea['numero_registro'])
                    hoja.write(y, 5, linea['compra_exento'] + linea['servicio_exento'])
                    hoja.write(y, 6, 0)
                    hoja.write(y, 7, linea['compra'] + linea['servicio'])
                    hoja.write(y, 8, linea['iva'])
                    hoja.write(y, 9, 0)
                    hoja.write(y, 10, 0)
                    hoja.write(y, 11, abs(linea['iva_retenido']))
                    hoja.write(y, 12, linea['total'])
                else:
                    hoja.write(y, 0, linea['fecha'].strftime('%d/%m/%Y'))
                    hoja.write(y, 1, linea['numero'])
                    hoja.write(y, 2, linea['compra_exento'] + linea['servicio_exento'])
                    hoja.write(y, 3, 0)
                    hoja.write(y, 4, linea['compra'] + linea['servicio'])
                    hoja.write(y, 5, linea['importacion'])
                    hoja.write(y, 6, linea['total'])
                    hoja.write(y, 7, 0)
                    hoja.write(y, 8, 0)

            y += 1
            if resumido == False:
                hoja.write(y, 4, 'Totales')
                hoja.write(y, 5, totales['compra']['exento'] + totales['servicio']['exento'])
                hoja.write(y, 6, 0)
                hoja.write(y, 7, totales['compra']['neto'] + totales['servicio']['neto'])
                hoja.write(y, 8, totales['compra']['iva'] + totales['servicio']['iva']  + totales['importacion']['iva'])
                hoja.write(y, 9, 0)
                hoja.write(y, 10, 0)
                hoja.write(y, 11, totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])
                hoja.write(y, 12, totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])
            else:
                hoja.write(y, 1, 'Totales')
                hoja.write(y, 2, totales['compra']['exento'] + totales['servicio']['exento'])
                hoja.write(y, 3, 0)
                hoja.write(y, 4, totales['compra']['neto'] + totales['servicio']['neto'])
                hoja.write(y, 5, totales['importacion']['neto'])
                hoja.write(y, 6, totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])
                hoja.write(y, 7, 0)
                hoja.write(y, 8, 0)

            y += 2
            hoja.write(y, 0, 'RESUMEN DE OPERACIONES A CREDITO FISCAL' if resumido == False else 'RESUMEN DE OPERACIONES A CONSUMIDORES FINALES')
            y += 2
            
            if resumido == False:
                hoja.write(y, 0, 'VENTAS NETAS')
                hoja.write(y, 1, totales['compra']['neto'] + totales['servicio']['neto'])
                y += 1
                hoja.write(y, 0, 'IVA COMPROBANTES DE CRÉDITO FISCAL')
                hoja.write(y, 1, totales['compra']['iva'] + totales['servicio']['iva'] + totales['importacion']['iva'])
                y += 1
                hoja.write(y, 0, 'TOTAL DE VENTAS GRAVADAS')
                hoja.write(y, 1, totales['compra']['neto'] + totales['servicio']['neto'])
                y += 1
                hoja.write(y, 0, 'TOTAL N/C')
                hoja.write(y, 1, totales['nota_credito'])
                y += 1
                hoja.write(y, 0, 'TOTAL DE VENTAS EXENTAS')
                hoja.write(y, 1, totales['compra']['exento'] + totales['servicio']['exento'])
                y += 1
                hoja.write(y, 0, 'TOTAL DE VENTAS NO SUJETAS')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'TOTAL DE VENTAS EXPORTACIÓN')
                hoja.write(y, 1, totales['importacion']['neto'])
                y += 1
                hoja.write(y, 0, 'TOTAL DE IVA RETENIDO')
                hoja.write(y, 1, totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido'] + totales['importacion']['iva_retenido'])
                y += 1
                hoja.write(y, 0, 'VENTAS A TERCEROS')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'IVA DE VENTAS A TERCEROS')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'TOTAL DE VENTAS A TERCEROS')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'TOTAL DE VENTAS')
                hoja.write(y, 1, totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])
                y += 1
            else:
                hoja.write(y, 0, 'VENTAS NETAS')
                hoja.write(y, 6, (totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])/1.13)
                y += 1
                hoja.write(y, 0, '13% IVA')
                hoja.write(y, 1, ((totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])/1.13)*0.13)
                y += 1
                hoja.write(y, 0, 'RETENCION 1%')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'VENTAS TOTALES GRAVADAS')
                hoja.write(y, 1, (totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])/1.13 + ((totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])/1.13)*0.13)
                y += 1
                hoja.write(y, 0, 'VENTAS NETAS')
                hoja.write(y, 1, (totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])/1.13)
                y += 1
                hoja.write(y, 0, 'VENTAS EXENTAS')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'VENTAS NO SUJETAS')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'VENTAS POR EXPORTACIONES')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'TOTAL VENTAS DEL MES')
                hoja.write(y, 1, (totales['compra']['total'] + totales['servicio']['total'] + totales['importacion']['total'] + totales['compra']['iva_retenido'] + totales['servicio']['iva_retenido']  + totales['importacion']['iva_retenido'])/1.13)
                y += 1
                hoja.write(y, 0, 'VENTAS A CUENTAS DE TERCEROS')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'IVA POR VENTA A CUENTA DE TERCEROS')
                hoja.write(y, 1, 0)
                y += 1
                hoja.write(y, 0, 'TOTAL DE VENTA A CUENTA DE TERCEROS')
                hoja.write(y, 1, 0)
                y += 1
            
            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'libro_de_ventas.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_sv_extra.asistente_reporte_ventas',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
