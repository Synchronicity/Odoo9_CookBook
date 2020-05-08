# -*- coding: utf-8 -*-
import os  # P 99
from openerp import models, fields
from openerp.addons import decimal_precision as dp
from openerp import api
from openerp.fields import Date as fDate
from datetime import timedelta as td
from openerp.exceptions import UserError  # P 99


class LibraryBook(models.Model):
    #   JLS : Attributes
    _name = 'library.book'
    # _inherit = ['base.archive']     # Page 90(113)

    # Page 66(89)
    _rec_name = "short_name"
    _order = 'name, date_release desc'

    name = fields.Char('Title', required=True)
    # The Char fields suppot a few specific attribues.
    short_name = fields.Char(
        string='Short Title',
        # size=100,  # For Char only !!! In general, it is advised not to use it !!!
        translate=False,  # also for Text fields
    )
    notes = fields.Text('Internal Notes')
    date_release = fields.Date('Release Date')
    author_ids = fields.Many2many(comodel_name='res.partner',
                                  string='Authors')
    state = fields.Selection([('draft', 'Unavailable'),
                              ('available', 'Available'),
                              ('borrowed', 'Borrowed'),
                              ('lost', 'Lost')],
                             'State')
    # The HTML fields also hve specific attributes
    description = fields.Html(
        'Description',
        # optional:
        sanitize=True,
        strip_style=False,
    )
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_updated = fields.Datetime('Last Updated')
    reader_rating = fields.Float(
        'Reader Average Rating',
        (14, 4),  # Optional precision (total, decimals)
    )
    # All these fields (above) support a few common attributes (like this):
    pages = fields.Integer(
        string='Number of Pages',
        default=0,
        help='Total book page count',
        groups='base.group_user',
        states={'cancel': [('readonly', True)]},
        copy=True,
        index=False,
        readonly=False,
        required=False,
        company_dependent=False,
    )

    # Page 71(94)
    cost_price = fields.Float(
        'Book Cost', dp.get_precision('Book Price'))

    # Page 73(96)
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency')
    retail_price = fields.Monetary(
        'Retail Price',
        # optional: currency_field='currency_id',
    )

    # Page 74(97)
    publisher_id = fields.Many2one(
        comodel_name='res.partner', string='Publisher',
        # optional:
        ondelete='set null',
        context={},
        domain=[],
    )

    # Page 81(104) ==> library_book_categ ?!?
    _sql_constraints = [
        ('name_uniq',
         'UNIQUE (name)',
         'Book title must be unique.')
    ]

    # Page 82(105)
    age_days = fields.Float(
        string='Days Since Release',
        compute='_compute_age',
        inverse='_inverse_age',
        search='_search_age',
        store=False,
        compute_sudo=False,
    )

    # Page 85(108)
    publisher_city = fields.Char(
        'Publisher City',
        related='publisher_id.city')

    #   JLS : Methods
    # Page 66(89) De base, affiche le nom de l'onglet (representation)
    def name_get(self):
        res = []
        for rec in self:
            res.append(
                (rec.id,
                 u"%s (%s)" % (rec.name, rec.author_ids.name)
                 ))
        return res

    # Page 81(104)
    @api.constrains('date_release')
    def _check_release_date(self):
        for r in self:
            if r.date_release > fields.Date.today():
                raise models.ValidationError(
                    'Release date must be in the past')

    # Page 83(106)
    @api.depends('date_release')
    def _compute_age(self):
        today = fDate.from_string(fDate.today())
        for book in self.filtered('date_release'):
            delta = (fDate.from_string(book.date_release) - today)
            book.age_days = delta.days

    def _inverse_age(self):
        today = fDate.from_string(fDate.today())
        for book in self.filtered('date_release'):
            d = td(days=book.age_days) - today
            book.date_release = fDate.to_string(d)

    def _search_age(operator, value):
        today = fDate.from_string(fDate.today())
        value_days = td(days=value)
        value_date = fDate.to_string(today - value_days)
        return [('date_release', operator, value_date)]

    # Page 86(109)
    @api.model
    def _referencable_models(self):
        models = self.env['res.request.link'].search([])
        return [(x.object, x.name) for x in models]

    ref_doc_id = fields.Reference(
        selection=_referencable_models,
        string='Reference Document')

    # Page 96(119)
    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'available'),
                   ('available', 'borrowed'),
                   ('borrowed', 'available'),
                   ('available', 'lost'),
                   ('borrowed', 'lost'),
                   ('lost', 'available')]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for book in self:
            if book.is_allowed_transition(book.state, new_state):
                book.state = new_state
            else:
                continue

    # Page 101(124)
    @api.model
    def get_all_library_members(self):
        library_member_model = self.env['library.member']
        return library_member_model.search([])


# JLS : Classes complémentaires (idéalement dans d'autres fichiers)
# Page 75(98)
class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'

    books_ids = fields.One2many(
        comodel_name='library.book', inverse_name='publisher_id',
        string='Published Books')

    book_ids = fields.Many2many(
        comodel_name='library.book',
        # relation='library_book_res_partner_rel'  # optional
        string='Authored Books',
    )

    # Page 88(111)
    authored_book_ids = fields.Many2many(
        comodel_name='library.book', string='Authored Books')
    count_books = fields.Integer(
        'Number of Authored Books',
        compute='_compute_count_books'
    )

    @api.depends('authored_book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.authored_book_ids)


# Page 90(113)
class BaseArchive(models.AbstractModel):
    _name = 'base.archive'
    active = fields.Boolean(default=True)

    def do_archive(self):
        for record in self:
            record.active = not record.active


# Page 92(115)
class LibraryMember(models.Model):
    _name = 'library.member'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        ondelete='cascade')

    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()


# Page 99(122)
class SomeModel(models.Model):
    _name = 'some.model'

    data = fields.Text('Data')

    @api.multi
    def save(self, filename):
        if '/' in filename or '\\' in filename:
            raise UserError('Illegal filename %s' % filename)
        path = os.path.join('/opt/exports', filename)
        try:
            with open(path, 'w') as fobj:
                for record in self:
                    fobj.write(record.data)
                    fobj.write('\n')
        except (IOError, OSError) as exc:
            message = 'Unable to save file: %s' % exc
            raise UserError(message)
