from project.utils.pdf import ProposalTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

class InvoiceTemplate(ProposalTemplate):

    def __init__(self, response, user):
        super(InvoiceTemplate, self).__init__(response, user)
        self.space_before_footer = 0.35 * inch

    def get_label(self, row):
        label = row.label
        if row.proposal and row.proposal.reference:
            label = u"%s - [%s]" % (label, row.proposal.reference)
        return label
