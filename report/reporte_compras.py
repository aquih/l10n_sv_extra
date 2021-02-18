# -*- encoding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import UserError
from datetime import datetime
import logging

class ReporteCompras(models.AbstractModel):
    _name = 'report.l10n_sv_extra.reporte_compras'

    def lineas(self, datos):
        totales = {}

        totales['num_facturas'] = 0
        totales['compra'] = {'exento':0,'neto':0,'iva':0,'percepcion':0,'total':0}
        totales['servicio'] = {'exento':0,'neto':0,'iva':0,'percepcion':0,'total':0}
        totales['importacion'] = {'exento':0,'neto':0,'iva':0,'percepcion':0,'total':0}
        totales['combustible'] = {'exento':0,'neto':0,'iva':0,'percepcion':0,'total':0}
        totales['pequenio_contribuyente'] = 0

        journal_ids = [x for x in datos['diarios_id']]
        facturas = self.env['account.move'].search([
            ('state','in',['posted']),
            ('type','in',['in_invoice','in_refund']),
            ('journal_id','in',journal_ids),
            ('date','<=',datos['fecha_hasta']),
            ('date','>=',datos['fecha_desde']),
        ], order='date, name')

        lineas = []
        correlativo = 1
        mes_actual = ''
        for f in facturas:
            if mes_actual != datetime.strftime(f.date, '%Y-%m'):
                mes_actual = datetime.strftime(f.date, '%Y-%m')
                correlativo = 1

            totales['num_facturas'] += 1

            tipo_cambio = 1
            if f.currency_id.id != f.company_id.currency_id.id:
                total = 0
                for l in f.move_id.line_ids:
                    if l.account_id.id == f.account_id.id:
                        total += l.credit - l.debit
                tipo_cambio = abs(total / f.amount_total)

            tipo = 'FACT'
            if f.type != 'in_invoice':
                tipo = 'NC'
            if f.partner_id.pequenio_contribuyente:
                tipo += ' PEQ'

            linea = {
                'correlativo': correlativo,
                'estado': f.state,
                'tipo': tipo,
                'fecha': f.date,
                'numero': f.name or '',
                'proveedor': f.partner_id,
                'compra': 0,
                'compra_exento': 0,
                'servicio': 0,
                'servicio_exento': 0,
                'combustible': 0,
                'combustible_exento': 0,
                'importacion': 0,
                'importacion_exento': 0,
                'base': 0,
                'iva': 0,
                'percepcion': 0,
                'total': 0
            }

            correlativo += 1
            for l in f.invoice_line_ids:
                precio = ( l.price_unit * (1-(l.discount or 0.0)/100.0) ) * tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1

                tipo_linea = f.tipo_gasto
                if f.tipo_gasto == 'mixto':
                    if l.product_id.type == 'product':
                        tipo_linea = 'compra'
                    else:
                        tipo_linea = 'servicio'

                r = l.tax_ids.compute_all(precio, currency=f.currency_id, quantity=l.quantity, product=l.product_id, partner=f.partner_id)

                linea['base'] += r['total_excluded']
                totales[tipo_linea]['total'] += r['total_excluded']
                if len(l.tax_ids) > 0:
                    linea[tipo_linea] += r['total_excluded']
                    totales[tipo_linea]['neto'] += r['total_excluded']
                    for i in r['taxes']:
                        if i['id'] == datos['impuesto_id'][0]:
                            linea['iva'] += i['amount']
                            totales[tipo_linea]['iva'] += i['amount']
                            totales[tipo_linea]['total'] += i['amount']
                        elif i['id'] == datos['percepcion_id'][0]:
                            linea['percepcion'] += i['amount']
                            totales[tipo_linea]['percepcion'] += i['amount']
                            totales[tipo_linea]['total'] += i['amount']
                        elif i['amount'] > 0:
                            linea[f.tipo_gasto+'_exento'] += i['amount']
                            totales[tipo_linea]['exento'] += i['amount']
                else:
                    linea[tipo_linea+'_exento'] += r['total_excluded']
                    totales[tipo_linea]['exento'] += r['total_excluded']

                linea['total'] += precio * l.quantity

            if f.partner_id.pequenio_contribuyente:
                totales['pequenio_contribuyente'] += linea['base']

            lineas.append(linea)

        return { 'lineas': lineas, 'totales': totales }

    def mes(self, numero):
        dict = {}
        dict['01'] = 'ENERO'
        dict['02'] = 'FEBRERO'
        dict['03'] = 'MARZO'
        dict['04'] = 'ABRIL'
        dict['05'] = 'MAYO'
        dict['06'] = 'JUNIO'
        dict['07'] = 'JULIO'
        dict['08'] = 'AGOSTO'
        dict['09'] = 'SEPTIEMBRE'
        dict['10'] = 'OCTUBRE'
        dict['11'] = 'NOVIEMBRE'
        dict['12'] = 'DICIEMBRE'
        return(dict[numero])

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        if len(data['form']['diarios_id']) == 0:
            raise UserError("Por favor ingrese al menos un diario.")

        diario = self.env['account.journal'].browse(data['form']['diarios_id'][0])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
            'mes': self.mes,
            'direccion': diario.direccion and diario.direccion.street,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
