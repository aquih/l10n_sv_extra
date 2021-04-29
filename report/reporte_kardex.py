# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.tools import float_is_zero
import logging

class ReporteKardex(models.AbstractModel):
    _name = 'report.l10n_sv_extra.reporte_kardex'

    def inicial(self, datos):
        self.env.cr.execute("select sum(qty_in) as entrada, sum(qty_out) as salida, product_id \
            from ( \
               select sum(product_qty) as qty_in, 0 as qty_out, product_id \
               from stock_move \
               where state = 'done' and product_id = %s and location_dest_id = %s and date <= %s \
               group by product_id \
               union \
               select 0 as qty_in, sum(product_qty) as qty_out, product_id \
               from stock_move \
               where state = 'done' and product_id = %s and  location_id = %s and date <= %s \
               group by product_id \
            ) movimientos\
            group by product_id",
            (datos['producto_id'], datos['ubicacion_id'], datos['fecha_desde'], datos['producto_id'], datos['ubicacion_id'], datos['fecha_desde']))
        lineas = self.env.cr.dictfetchall()

        total = 0
        for l in lineas:
            total += l['entrada'] - l['salida']

        return total

    def lineas(self, datos, product_id):
        totales = {}
        totales['entrada'] = 0
        totales['salida'] = 0
        totales['inicio'] = 0

        producto = self.env['product.product'].browse([product_id])
        dict = {'producto_id': producto.id, 
                'ubicacion_id': datos['ubicacion_id'][0], 
                'fecha_desde': datos['fecha_desde']
               }

        totales['inicio'] = self.inicial(dict)

        saldo = totales['inicio']
        lineas = []
        correlativo = 1
        movimientos = self.env['stock.move'].search([('product_id','=',producto.id), ('date','>=',datos['fecha_desde']), ('date','<=',datos['fecha_hasta']), ('state','=','done'), '|', ('location_id','=',datos['ubicacion_id'][0]), ('location_dest_id','=',datos['ubicacion_id'][0])], order = 'date')
        for m in movimientos:

            detalle = {
                'correlativo': correlativo,
                'empresa':'-',
                'unidad_medida': m.product_id.uom_id.name,
                'fecha': m.date,
                'entrada': 0,
                'entrada_costo_unitario': 0,
                'entrada_costo_total': 0,
                'salida': 0,
                'salida_costo_unitario': 0,
                'salida_costo_total': 0,
                'saldo':saldo,
                'saldo_costo_unitario': 0,
                'saldo_costo_total': 0,
            }
            correlativo += 1

            if m.picking_id:
                detalle['documento'] = m.picking_id.name
                if m.picking_id.partner_id:
                    detalle['empresa'] = m.picking_id.partner_id.name

            else:
                detalle['documento'] = m.name

#            costo = m.product_id.get_history_price(m.company_id.id, date=m.date)

            domain = [
                ('product_id', 'in', [m.product_id.id]),
                ('company_id', '=', m.company_id.id),
                ('create_date', '<=', m.date),
            ]
            groups = self.env['stock.valuation.layer'].read_group(domain, ['value:sum', 'quantity:sum'], ['product_id'])
            costo = 0
            for group in groups:
                valor = self.env.company.currency_id.round(group['value'])
                cantidad = group['quantity']
                costo = valor / cantidad

            detalle['costo'] = costo

            if m.location_dest_id.id == datos['ubicacion_id'][0]:
                detalle['tipo'] = 'Ingreso'
                detalle['entrada'] = m.product_qty
                detalle['entrada_costo_unitario'] = costo
                detalle['entrada_costo_total'] = costo * detalle['entrada']
                totales['entrada'] += m.product_qty
            elif m.location_id.id == datos['ubicacion_id'][0]:
                detalle['tipo'] = 'Salida'
                detalle['salida'] = -m.product_qty
                detalle['salida_costo_unitario'] = costo
                detalle['salida_costo_total'] = costo * detalle['salida']
                totales['salida'] -= m.product_qty

            saldo += detalle['entrada']+detalle['salida']
            detalle['saldo'] = saldo
            detalle['saldo_costo_unitario'] = costo
            detalle['saldo_costo_total'] = costo * saldo

            lineas.append(detalle)

        return {'producto': producto.name, 'lineas': lineas, 'totales': totales}
    
    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        return  {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
