from django.core.urlresolvers import reverse
from django.test import TestCase
from project.models import Project, PROJECT_STATE_PROSPECT, \
    PROJECT_STATE_CANCELED, PROJECT_STATE_PROPOSAL_SENT, \
    PROJECT_STATE_PROPOSAL_ACCEPTED, PROJECT_STATE_STARTED, \
    PROJECT_STATE_FINISHED, Proposal, PROPOSAL_STATE_DRAFT, ROW_CATEGORY_SERVICE, \
    PROPOSAL_STATE_SENT, ROW_CATEGORY_PRODUCT, ProposalRow, \
    ProposalAmountError
from accounts.models import Invoice, InvoiceRow, INVOICE_STATE_EDITED
import datetime

class ProjectTest(TestCase):
    fixtures = ['test_users', 'test_contacts']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testGetAdd(self):
        """
        Tests getting Add project page
        """
        response = self.client.get(reverse('project_add'))
        self.assertEqual(response.status_code, 200)

    def testPostAdd(self):
        """
        Tests posting to Add project page
        """
        response = self.client.post(reverse('project_add'),
                                    {'project-name': 'Project 1',
                                     'project-customer': 10,
                                     'project-state': PROJECT_STATE_PROSPECT})
        self.assertEqual(response.status_code, 302)
        result = Project.objects.filter(name='Project 1',
                                        customer__id=10,
                                        state=PROJECT_STATE_PROSPECT,
                                        owner__id=1)
        self.assertEqual(len(result), 1)

    def testGetEdit(self):
        """
        Tests getting Edit project page
        """
        p = Project.objects.create(name='Project 1',
                                   customer_id=10,
                                   state=PROJECT_STATE_PROSPECT,
                                   owner_id=1)

        response = self.client.get(reverse('project_edit', kwargs={'id': p.id}))
        self.assertEqual(response.status_code, 200)

    def testPostEdit(self):
        """
        Tests posting to Edit project page
        """
        p = Project.objects.create(name='Project 1',
                                   customer_id=10,
                                   state=PROJECT_STATE_PROSPECT,
                                   owner_id=1)

        response = self.client.post(reverse('project_edit', kwargs={'id': p.id}),
                                    {'project-name': 'Project 1 modified',
                                     'project-customer': 11,
                                     'project-state': PROJECT_STATE_CANCELED})
        self.assertEqual(response.status_code, 302)
        result = Project.objects.filter(name='Project 1 modified',
                                        customer__id=11,
                                        state=PROJECT_STATE_CANCELED,
                                        owner__id=1)
        self.assertEqual(len(result), 1)

    def testGetDelete(self):
        """
        Tests getting Delete project page
        """
        p = Project.objects.create(name='Project 1',
                                   customer_id=10,
                                   state=PROJECT_STATE_PROSPECT,
                                   owner_id=1)

        response = self.client.get(reverse('project_delete', kwargs={'id': p.id}))
        self.assertEqual(response.status_code, 200)

    def testPostDelete(self):
        """
        Tests posting to Delete project page
        """
        p = Project.objects.create(name='Project 1',
                                   customer_id=10,
                                   state=PROJECT_STATE_PROSPECT,
                                   owner_id=1)

        response = self.client.post(reverse('project_delete', kwargs={'id': p.id}),
                                    {'delete': 'Ok'})
        self.assertEqual(response.status_code, 302)
        result = Project.objects.all()
        self.assertEqual(len(result), 0)

    def testGetDetail(self):
        """
        Tests getting Detail project page
        """
        p = Project.objects.create(name='Project 1',
                                   customer_id=10,
                                   state=PROJECT_STATE_PROSPECT,
                                   owner_id=1)

        response = self.client.get(reverse('project_detail', kwargs={'id': p.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], p)

    def testRunningList(self):
        """
        Tests if only running projects are shown on running list
        """
        p1 = Project.objects.create(name='Project 1',
                                    customer_id=10,
                                    state=PROJECT_STATE_PROSPECT,
                                    owner_id=1)
        p2 = Project.objects.create(name='Project 2',
                                    customer_id=10,
                                    state=PROJECT_STATE_PROPOSAL_SENT,
                                    owner_id=1)
        p3 = Project.objects.create(name='Project 3',
                                    customer_id=10,
                                    state=PROJECT_STATE_PROPOSAL_ACCEPTED,
                                    owner_id=1)
        p4 = Project.objects.create(name='Project 4',
                                    customer_id=10,
                                    state=PROJECT_STATE_STARTED,
                                    owner_id=1)
        p5 = Project.objects.create(name='Project 5',
                                    customer_id=10,
                                    state=PROJECT_STATE_FINISHED,
                                    owner_id=1)
        p6 = Project.objects.create(name='Project 6',
                                    customer_id=10,
                                    state=PROJECT_STATE_CANCELED,
                                    owner_id=1)

        response = self.client.get(reverse('project_running_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context['projects'].object_list), set([p1, p2, p3, p4]))

    def testFinishedList(self):
        """
        Tests if only finished projects are shown on finished list
        """
        p1 = Project.objects.create(name='Project 1',
                                    customer_id=10,
                                    state=PROJECT_STATE_PROSPECT,
                                    owner_id=1)
        p2 = Project.objects.create(name='Project 2',
                                    customer_id=10,
                                    state=PROJECT_STATE_PROPOSAL_SENT,
                                    owner_id=1)
        p3 = Project.objects.create(name='Project 3',
                                    customer_id=10,
                                    state=PROJECT_STATE_PROPOSAL_ACCEPTED,
                                    owner_id=1)
        p4 = Project.objects.create(name='Project 4',
                                    customer_id=10,
                                    state=PROJECT_STATE_STARTED,
                                    owner_id=1)
        p5 = Project.objects.create(name='Project 5',
                                    customer_id=10,
                                    state=PROJECT_STATE_FINISHED,
                                    owner_id=1)
        p6 = Project.objects.create(name='Project 6',
                                    customer_id=10,
                                    state=PROJECT_STATE_CANCELED,
                                    owner_id=1)

        response = self.client.get(reverse('project_finished_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context['projects'].object_list), set([p5, p6]))

class ProposalTest(TestCase):
    fixtures = ['test_users', 'test_contacts', 'test_projects']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testGetAdd(self):
        """
        Tests getting Add proposal page
        """
        response = self.client.get(reverse('proposal_add', kwargs={'project_id': 30}))
        self.assertEqual(response.status_code, 200)

    def testPostAdd(self):
        """
        Tests posting to Add proposal page
        """
        response = self.client.post(reverse('proposal_add', kwargs={'project_id': 30}),
                                    {'proposal-state': PROPOSAL_STATE_DRAFT,
                                     'proposal-begin_date': '2010-8-1',
                                     'proposal-end_date': '2010-8-15',
                                     'proposal-contract_content': 'Content of contract',
                                     'proposal_rows-TOTAL_FORMS': 1,
                                     'proposal_rows-INITIAL_FORMS': 0,
                                     'proposal_rows-0-ownedobject_ptr': '',
                                     'proposal_rows-0-label': 'Day of work',
                                     'proposal_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'proposal_rows-0-quantity': 10,
                                     'proposal_rows-0-unit_price': 200.50 })
        self.assertEqual(response.status_code, 302)
        result = Proposal.objects.filter(project__id=30,
                                         state=PROPOSAL_STATE_DRAFT,
                                         begin_date=datetime.date(2010, 8, 1),
                                         end_date=datetime.date(2010, 8, 15),
                                         contract_content='Content of contract',
                                         amount=2005,
                                         owner__id=1)
        self.assertEqual(len(result), 1)
        proposal_rows = result[0].proposal_rows.all()
        self.assertEqual(len(proposal_rows), 1)
        proposal_rows = result[0].proposal_rows.filter(label='Day of work',
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=10,
                                                    unit_price='200.5')
        self.assertEqual(len(proposal_rows), 1)

    def testGetEdit(self):
        """
        Tests getting Edit proposal page
        """
        p = Proposal.objects.create(project_id=30,
                                    update_date=datetime.date.today(),
                                    state=PROPOSAL_STATE_DRAFT,
                                    begin_date=datetime.date(2010, 8, 1),
                                    end_date=datetime.date(2010, 8, 15),
                                    contract_content='Content of contract',
                                    amount=2005,
                                    owner_id=1)

        p_row = ProposalRow.objects.create(proposal_id=p.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=20,
                                           unit_price='200.5',
                                           owner_id=1)

        response = self.client.get(reverse('proposal_edit', kwargs={'id': p.id}))
        self.assertEqual(response.status_code, 200)

    def testPostEdit(self):
        """
        Tests posting to Edit proposal page
        """
        p = Proposal.objects.create(project_id=30,
                                    update_date=datetime.date.today(),
                                    state=PROPOSAL_STATE_DRAFT,
                                    begin_date=datetime.date(2010, 8, 1),
                                    end_date=datetime.date(2010, 8, 15),
                                    contract_content='Content of contract',
                                    amount=2005,
                                    owner_id=1)

        p_row = ProposalRow.objects.create(proposal_id=p.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=20,
                                           unit_price='200.5',
                                           owner_id=1)

        response = self.client.post(reverse('proposal_edit', kwargs={'id': p.id}),
                                    {'proposal-state': PROPOSAL_STATE_SENT,
                                     'proposal-amount': 104,
                                     'proposal-begin_date': '2010-8-2',
                                     'proposal-end_date': '2010-8-16',
                                     'proposal-contract_content': 'Contract content',
                                     'proposal_rows-TOTAL_FORMS': 1,
                                     'proposal_rows-INITIAL_FORMS': 1,
                                     'proposal_rows-0-ownedobject_ptr': p_row.id,
                                     'proposal_rows-0-label': 'My product',
                                     'proposal_rows-0-category': ROW_CATEGORY_PRODUCT,
                                     'proposal_rows-0-quantity': 10,
                                     'proposal_rows-0-unit_price': 10.40 })
        self.assertEqual(response.status_code, 302)
        result = Proposal.objects.filter(id=p.id,
                                         project__id=30,
                                         state=PROPOSAL_STATE_SENT,
                                         begin_date=datetime.date(2010, 8, 2),
                                         end_date=datetime.date(2010, 8, 16),
                                         contract_content='Contract content',
                                         amount=104,
                                         owner__id=1)
        self.assertEqual(len(result), 1)
        proposal_rows = result[0].proposal_rows.all()
        self.assertEqual(len(proposal_rows), 1)
        proposal_rows = result[0].proposal_rows.filter(label='My product',
                                                       category=ROW_CATEGORY_PRODUCT,
                                                       quantity=10,
                                                       unit_price='10.40')
        self.assertEqual(len(proposal_rows), 1)

    def testGetDelete(self):
        """
        Tests getting Delete proposal page
        """
        p = Proposal.objects.create(project_id=30,
                                    update_date=datetime.date.today(),
                                    state=PROPOSAL_STATE_DRAFT,
                                    begin_date=datetime.date(2010, 8, 1),
                                    end_date=datetime.date(2010, 8, 15),
                                    contract_content='Content of contract',
                                    amount=2005,
                                    owner_id=1)

        p_row = ProposalRow.objects.create(proposal_id=p.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=20,
                                           unit_price='200.5',
                                           owner_id=1)

        response = self.client.get(reverse('proposal_delete', kwargs={'id': p.id}))
        self.assertEqual(response.status_code, 200)

    def testPostDelete(self):
        """
        Tests posting to Delete proposal page
        """
        p = Proposal.objects.create(project_id=30,
                                    update_date=datetime.date.today(),
                                    state=PROPOSAL_STATE_DRAFT,
                                    begin_date=datetime.date(2010, 8, 1),
                                    end_date=datetime.date(2010, 8, 15),
                                    contract_content='Content of contract',
                                    amount=2005,
                                    owner_id=1)

        p_row = ProposalRow.objects.create(proposal_id=p.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=20,
                                           unit_price='200.5',
                                           owner_id=1)

        response = self.client.post(reverse('proposal_delete', kwargs={'id': p.id}),
                                    {'delete': 'Ok'})
        self.assertEqual(response.status_code, 302)
        result = Proposal.objects.all()
        self.assertEqual(len(result), 0)
        result = ProposalRow.objects.all()
        self.assertEqual(len(result), 0)

    def testGetDetail(self):
        """
        Tests getting Detail proposal page
        """
        p = Proposal.objects.create(project_id=30,
                                    update_date=datetime.date.today(),
                                    state=PROPOSAL_STATE_DRAFT,
                                    begin_date=datetime.date(2010, 8, 1),
                                    end_date=datetime.date(2010, 8, 15),
                                    contract_content='Content of contract',
                                    amount=2005,
                                    owner_id=1)

        p_row = ProposalRow.objects.create(proposal_id=p.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=20,
                                           unit_price='200.5',
                                           owner_id=1)

        response = self.client.get(reverse('proposal_detail', kwargs={'id': p.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['proposal'], p)

    def testRemainingToInvoice(self):
        """
        Tests computation of remaining to invoice
        """
        p = Proposal.objects.create(project_id=30,
                                    update_date=datetime.date.today(),
                                    state=PROPOSAL_STATE_DRAFT,
                                    begin_date=datetime.date(2010, 8, 1),
                                    end_date=datetime.date(2010, 8, 15),
                                    contract_content='Content of contract',
                                    amount=2005,
                                    owner_id=1)

        p_row = ProposalRow.objects.create(proposal_id=p.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=20,
                                           unit_price='200.5',
                                           owner_id=1)

        i = Invoice.objects.create(customer_id=p.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=p.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        self.assertEqual(p.get_remaining_to_invoice(), 1005)

    def testAmountGTEInvoices(self):
        """
        Tests that proposal amount can't be less than sum of
        invoices amount.
        """
        p = Proposal.objects.create(project_id=30,
                                    update_date=datetime.date.today(),
                                    state=PROPOSAL_STATE_DRAFT,
                                    begin_date=datetime.date(2010, 8, 1),
                                    end_date=datetime.date(2010, 8, 15),
                                    contract_content='Content of contract',
                                    amount=4000,
                                    owner_id=1)

        p_row = ProposalRow.objects.create(proposal_id=p.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=20,
                                           unit_price='200',
                                           owner_id=1)

        i = Invoice.objects.create(customer_id=p.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)

        i_row = InvoiceRow.objects.create(proposal_id=p.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        i2 = Invoice.objects.create(customer_id=p.project.customer_id,
                                    invoice_id=2,
                                    state=INVOICE_STATE_EDITED,
                                    amount='2000',
                                    edition_date=datetime.date(2010, 8, 31),
                                    payment_date=datetime.date(2010, 9, 30),
                                    paid_date=None,
                                    execution_begin_date=datetime.date(2010, 8, 1),
                                    execution_end_date=datetime.date(2010, 8, 7),
                                    penalty_date=datetime.date(2010, 10, 8),
                                    penalty_rate='1.5',
                                    discount_conditions='Nothing',
                                    owner_id=1)

        i2_row = InvoiceRow.objects.create(proposal_id=p.id,
                                           invoice_id=i2.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=10,
                                           unit_price='200',
                                           balance_payments=False,
                                           owner_id=1)

        p.amount = 2999
        self.assertRaises(ProposalAmountError, p.save)

        response = self.client.post(reverse('proposal_edit', kwargs={'id': p.id}),
                                    {'proposal-state': PROPOSAL_STATE_SENT,
                                     'proposal-amount': 2999,
                                     'proposal-begin_date': '2010-8-2',
                                     'proposal-end_date': '2010-8-16',
                                     'proposal-contract_content': 'Contract content',
                                     'proposal_rows-TOTAL_FORMS': 1,
                                     'proposal_rows-INITIAL_FORMS': 1,
                                     'proposal_rows-0-ownedobject_ptr': p_row.id,
                                     'proposal_rows-0-label': 'Day of work',
                                     'proposal_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'proposal_rows-0-quantity': 10,
                                     'proposal_rows-0-unit_price': 299.9 })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('amount' in response.context['proposalForm'].errors)

