# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
import logging


class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one('res.partner', string='Dirección')
    resolucion = fields.Char(string='Resolución')
    serie = fields.Char(string='Serie')
    rango_inicio = fields.Char(string='Rango inicio')
    rango_fin = fields.Char(string='Rango fin')
