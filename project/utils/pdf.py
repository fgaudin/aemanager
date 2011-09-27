# -*- coding: utf-8 -*-

from decimal import Decimal
from reportlab.platypus import Table, TableStyle, Image, Paragraph
from django.conf import settings
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Spacer
from django.utils.formats import localize
from django.utils.translation import ugettext_lazy as _, ugettext
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.rl_config import defaultPageSize
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from custom_canvas import NumberedCanvas

class ProposalTemplate(object):

    styleH = ParagraphStyle({})
    styleH.fontSize = 14
    styleH.leading = 16
    styleH.borderPadding = (5,) * 4

    styleH2 = ParagraphStyle({})
    styleH2.fontSize = 14
    styleH2.leading = 16

    styleCustomer = ParagraphStyle({})
    styleCustomer.fontSize = 12
    styleCustomer.leading = 14
    styleCustomer.borderPadding = (5,) * 4

    styleN = ParagraphStyle({})
    styleN.fontSize = 12
    styleN.leading = 14

    styleTotal = ParagraphStyle({})
    styleTotal.fontSize = 14
    styleTotal.leading = 16
    styleTotal.borderColor = colors.black
    styleTotal.borderWidth = 0.5
    styleTotal.borderPadding = (5,) * 4

    styleTitle = ParagraphStyle({})
    styleTitle.fontSize = 14
    styleTitle.fontName = "Helvetica-Bold"

    styleF = ParagraphStyle({})
    styleF.fontSize = 10
    styleF.alignment = TA_CENTER

    styleLabel = ParagraphStyle({})

    styleDetail = ParagraphStyle({})
    styleDetail.fontName = 'Helvetica-Oblique'
    styleDetail.textColor = colors.gray

    def __init__(self, response, user):
        self.response = response
        self.user = user
        self.doc = None
        self.story = []
        self.space_before_footer = 0.55 * inch

    def append_to_story(self, data):
        self.story.append(data)

    def build(self):
        self.doc.build(self.story, canvasmaker=NumberedCanvas)

    def init_doc(self, title):

        def proposal_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 10)
            PAGE_WIDTH = defaultPageSize[0]
            footer_text = "%s %s - %s, %s %s" % (self.user.first_name,
                                                 self.user.last_name,
                                                 self.user.get_profile().address.street.replace("\n", ", ").replace("\r", ""),
                                                 self.user.get_profile().address.zipcode,
                                                 self.user.get_profile().address.city)
            if self.user.get_profile().address.country:
                footer_text = footer_text + u", %s" % (self.user.get_profile().address.country)

            canvas.drawCentredString(PAGE_WIDTH / 2.0, 0.5 * inch, footer_text)
            extra_info = u"SIRET : %s" % (self.user.get_profile().company_id)
            if self.user.get_profile().vat_number:
                extra_info = u"%s - N° TVA : %s" % (extra_info, self.user.get_profile().vat_number)
            canvas.drawCentredString(PAGE_WIDTH / 2.0, 0.35 * inch, extra_info)
            canvas.restoreState()

        self.doc = BaseDocTemplate(self.response, title=title, leftMargin=0.5 * inch, rightMargin=0.5 * inch)
        frameT = Frame(self.doc.leftMargin, self.doc.bottomMargin, self.doc.width, self.doc.height + 0.5 * inch, id='normal')
        self.doc.addPageTemplates([PageTemplate(id='all', frames=frameT, onPage=proposal_footer), ])

    def add_headers(self, proposal, customer, document_date):

        data = []
        user_header_content = """
        %s %s<br/>
        %s<br/>
        %s %s<br/>
        %s<br/>
        SIRET : %s<br/>
        """
        user_header_content = user_header_content % (self.user.first_name,
                                                     self.user.last_name,
                                                     self.user.get_profile().address.street.replace("\n", "<br/>"),
                                                     self.user.get_profile().address.zipcode,
                                                     self.user.get_profile().address.city,
                                                     self.user.get_profile().address.country or '',
                                                     self.user.get_profile().company_id)

        if self.user.get_profile().phonenumber:
            user_header_content = "%s%s<br/>" % (user_header_content, self.user.get_profile().phonenumber)
        if self.user.get_profile().professional_email:
            user_header_content = "%s%s<br/>" % (user_header_content, self.user.get_profile().professional_email)

        customer_header_content = """
        <br/><br/><br/><br/>
        %s<br/>
        %s<br/>
        %s %s<br/>
        %s<br/>
        """

        if self.user.get_profile().logo_file:
            user_header = Image("%s%s" % (settings.FILE_UPLOAD_DIR, self.user.get_profile().logo_file))
        else:
            user_header = Paragraph(user_header_content, self.styleH)

        data.append([user_header,
                    '',
                    Paragraph(customer_header_content % (customer.name,
                                                         customer.address.street.replace("\n", "<br/>"),
                                                         customer.address.zipcode,
                                                         customer.address.city,
                                                         customer.address.country or ''), self.styleCustomer)])

        t1 = Table(data, [3.5 * inch, 0.7 * inch, 3.1 * inch], [1.9 * inch])

        table_style = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ]

        if self.user.get_profile().logo_file:
            table_style.append(('TOPPADDING', (0, 0), (0, 0), 0))
            table_style.append(('LEFTPADDING', (0, 0), (0, 0), 0))

        t1.setStyle(TableStyle(table_style))

        self.story.append(t1)

        self.story.append(Spacer(self.doc.width, 0.25 * inch))

        data = []
        msg = u"Dispensé d'immatriculation au registre du commerce et des sociétés (RCS) et au répertoire des métiers (RM)"
        data.append([Paragraph(msg, self.styleN),
                    '',
                    Paragraph("<br/>" + _("Date : %s") % (localize(document_date)), self.styleH2)])

        t2 = Table(data, [3.5 * inch, 0.3 * inch, 3.5 * inch], [0.7 * inch])
        t2.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ]))

        self.story.append(t2)

        self.story.append(Spacer(self.doc.width, 0.25 * inch))

    def add_title(self, title):
        self.story.append(Paragraph(title, self.styleTitle))

        spacer = Spacer(self.doc.width, 0.1 * inch)
        self.story.append(spacer)

    def add_row_detail(self, data, row, label_width):
        extra_rows = 0
        if row.detail:
            for line in row.detail.split("\n"):
                para = Paragraph(line, self.styleDetail)
                para.width = label_width
                splitted_para = para.breakLines(label_width)
                for detail_row in splitted_para.lines:
                    detail = " ".join(detail_row[1])
                    data.append((detail,))
                    extra_rows += 1
        return extra_rows

    def add_row_table(self, data, row_count, extra_style=[]):
        if row_count <= 16:
            max_row_count = 16
        else:
            first_page_count = 21
            normal_page_count = 33
            last_page_count = 27
            max_row_count = first_page_count + ((row_count - first_page_count) // normal_page_count * normal_page_count) + last_page_count
            if row_count - first_page_count - ((row_count - first_page_count) // normal_page_count * normal_page_count) > last_page_count:
                max_row_count = max_row_count + normal_page_count

        for i in range(max_row_count - row_count):
            if self.user.get_profile().vat_number:
                data.append(['', '', '', '', ''])
            else:
                data.append(['', '', '', ''])

        if self.user.get_profile().vat_number:
            row_table = Table(data, [4.2 * inch, 0.8 * inch, 0.9 * inch, 0.8 * inch, 0.5 * inch], (max_row_count + 1) * [0.3 * inch])
        else:
            row_table = Table(data, [4.7 * inch, 0.8 * inch, 0.9 * inch, 0.8 * inch], (max_row_count + 1) * [0.3 * inch])
        row_style = [('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                     ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                     ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                     ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
                     ('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
                     ('BOX', (0, 1), (0, -1), 0.25, colors.black),
                     ('BOX', (1, 1), (1, -1), 0.25, colors.black),
                     ('BOX', (2, 1), (2, -1), 0.25, colors.black),
                     ('BOX', (3, 1), (3, -1), 0.25, colors.black)]

        row_style += extra_style

        if self.user.get_profile().vat_number:
            row_style.append(('BOX', (4, 1), (4, -1), 0.25, colors.black))

        row_table.setStyle(TableStyle(row_style))

        self.story.append(row_table)

    def get_label(self, row):
        return row.label

    def add_rows(self, rows):
        row_count = 0
        extra_rows = 0
        extra_style = []
        data = []
        data.append([ugettext('Label'), ugettext('Quantity'), ugettext('Unit price'), ugettext('Total excl tax')])
        if self.user.get_profile().vat_number:
            data[0].append(ugettext('VAT'))
            label_width = 4.0 * inch
        else:
            label_width = 4.5 * inch
        for row in rows:
            row_count += 1
            label = self.get_label(row)
            para = Paragraph(label, ProposalTemplate.styleLabel)
            para.width = label_width
            splitted_para = para.breakLines(label_width)
            label = " ".join(splitted_para.lines[0][1])
            quantity = row.quantity
            quantity = quantity.quantize(Decimal(1)) if quantity == quantity.to_integral() else quantity.normalize()
            unit_price = row.unit_price
            unit_price = unit_price.quantize(Decimal(1)) if unit_price == unit_price.to_integral() else unit_price.normalize()
            total = row.quantity * row.unit_price
            total = total.quantize(Decimal(1)) if total == total.to_integral() else total.normalize()
            data_row = [label, localize(quantity), "%s %s" % (localize(unit_price), "€".decode('utf-8')), "%s %s" % (localize(total), "€".decode('utf-8'))]
            if self.user.get_profile().vat_number:
                if row.vat_rate:
                    data_row.append("%s%%" % (localize(row.vat_rate)))
                else:
                    data_row.append('-')
            data.append(data_row)

            for extra_row in splitted_para.lines[1:]:
                label = " ".join(extra_row[1])
                if self.user.get_profile().vat_number:
                    data.append([label, '', '', '', ''])
                else:
                    data.append([label, '', '', ''])
                extra_rows += 1

            extra_detail_rows = self.add_row_detail(data, row, label_width)
            if extra_detail_rows:
                extra_style.append(('FONT',
                                    (0, row_count + extra_rows + 1),
                                    (0, row_count + extra_rows + extra_detail_rows),
                                     self.styleDetail.fontName))
                extra_style.append(('TEXTCOLOR',
                                    (0, row_count + extra_rows + 1),
                                    (0, row_count + extra_rows + extra_detail_rows),
                                     self.styleDetail.textColor))
            extra_rows += extra_detail_rows

        self.add_row_table(data, row_count + extra_rows, extra_style)
        self.story.append(Spacer(self.doc.width, self.space_before_footer))

    def get_total_amount(self, amount, rows):
        amount = amount.quantize(Decimal(1)) if amount == amount.to_integral() else amount.normalize()

        if self.user.get_profile().vat_number:
            total_amount = [Paragraph(_("Total excl tax : %(amount)s %(currency)s") % {'amount': localize(amount), 'currency' : "€".decode('utf-8')}, ProposalTemplate.styleN)]
            vat_amounts = {}
            for row in rows:
                vat_rate = row.vat_rate or 0
                vat_amount = row.amount * vat_rate / 100
                if vat_rate:
                    if vat_rate in vat_amounts:
                        vat_amounts[vat_rate] = vat_amounts[vat_rate] + vat_amount
                    else:
                        vat_amounts[vat_rate] = vat_amount
            for vat_rate, vat_amount in vat_amounts.items():
                vat_amount = round(vat_amount, 2)
                #vat_amount = vat_amount.quantize(Decimal(1)) if vat_amount == vat_amount.to_integral() else vat_amount.normalize()
                total_amount.append(Paragraph(_("VAT %(vat_rate)s%% : %(vat_amount)s %(currency)s") % {'vat_rate': localize(vat_rate),
                                                                                                       'vat_amount': localize(vat_amount),
                                                                                                       'currency' : "€".decode('utf-8')},
                                              ProposalTemplate.styleN))

            incl_tax_amount = amount + sum(vat_amounts.values())
            #incl_tax_amount = incl_tax_amount.quantize(Decimal(1)) if incl_tax_amount == incl_tax_amount.to_integral() else incl_tax_amount.normalize()
            incl_tax_amount = round(incl_tax_amount, 2)
            total_amount.append(Spacer(1, 0.25 * inch))
            total_amount.append(Paragraph(_("TOTAL incl tax : %(amount)s %(currency)s") % {'amount': localize(incl_tax_amount), 'currency' : "€".decode('utf-8')}, ProposalTemplate.styleTotal))
        else:
            total_amount = [Paragraph(_("TOTAL excl tax : %(amount)s %(currency)s") % {'amount': localize(amount), 'currency' : "€".decode('utf-8')}, ProposalTemplate.styleTotal),
                            Spacer(1, 0.25 * inch),
                            Paragraph(u"TVA non applicable, art. 293 B du CGI", ProposalTemplate.styleN)]

        return total_amount
