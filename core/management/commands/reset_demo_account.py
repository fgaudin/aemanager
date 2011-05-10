# coding=utf-8

import shutil
from django.core.management.base import BaseCommand
from autoentrepreneur.models import UserProfile, \
    AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC, \
    AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL, \
    AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY
from django.conf import settings
from django.contrib.auth.models import User
import datetime
from project.models import Project, PROJECT_STATE_FINISHED, \
    PROJECT_STATE_PROPOSAL_ACCEPTED, Proposal, \
    PROPOSAL_STATE_DRAFT, PROPOSAL_STATE_BALANCED, ProposalRow, \
    ROW_CATEGORY_SERVICE, PROJECT_STATE_STARTED, PROPOSAL_STATE_ACCEPTED, \
    PROJECT_STATE_PROSPECT
from contact.models import Contact, CONTACT_TYPE_COMPANY, Address, PhoneNumber, \
    PHONENUMBER_TYPE_WORK
from accounts.models import InvoiceRow, Invoice, INVOICE_STATE_PAID, \
    PAYMENT_TYPE_CHECK, Expense, PAYMENT_TYPE_BANK_CARD, INVOICE_STATE_SENT, \
    INVOICE_STATE_EDITED
from django.db import connection, transaction, models
from django.core.management.color import no_style

class Command(BaseCommand):
    help = "Reset data for demo account"

    def handle(self, *args, **options):
        if not settings.DEMO:
            self.stderr.write("Demo is set to False\n")

        for profile in UserProfile.objects.all():
            shutil.rmtree('%s%s' % (settings.FILE_UPLOAD_DIR,
                                    profile.uuid),
                                    True)
            profile.user.delete()

        # reset sql sequence
        cursor = connection.cursor()
        model_list = [models.get_model('auth', 'User'), models.get_model('core', 'OwnedObject'), ]
        style = no_style()

        queries = connection.ops.sequence_reset_sql(style, model_list)
        for query in queries:
            cursor.execute(query.encode('utf-8'))
        transaction.commit_unless_managed()

        now = datetime.datetime.now()

        user = User.objects.create_user('demo', 'demo@mapetiteautoentreprise.fr', 'demo')
        user.first_name = 'Jean'
        user.last_name = 'Dupont'
        user.save()

        profile = user.get_profile()
        profile.phonenumber = '0102030405'
        profile.professional_email = 'demo.pro@mapetiteautoentreprise.fr'
        profile.company_name = 'Ma Petite Auto-Entreprise'
        profile.company_id = '12345678912345'
        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.professional_category = AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL
        profile.creation_date = datetime.date(now.year - 1, 3, 1)
        profile.payment_option = AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY
        profile.save()

        address = profile.address
        address.street = '1 rue de la Paix'
        address.zipcode = '75001'
        address.city = 'Paris'
        address.save()

        customer1_address = Address.objects.create(owner=user,
                                                   street='714 rue de Sydney',
                                                   zipcode='92800',
                                                   city='Puteaux')
        customer1 = Contact.objects.create(owner=user,
                                           contact_type=CONTACT_TYPE_COMPANY,
                                           name='Bross & Clackwell',
                                           company_id='98765432198765',
                                           legal_form='SA',
                                           email='contact@brossandclackwell.com',

                                           representative='Laszlo Carreidas',
                                           representative_function='Gérant',
                                           address=customer1_address)
        customer1_phonenumber = PhoneNumber.objects.create(owner=user,
                                                           type=PHONENUMBER_TYPE_WORK,
                                                           number='0203040506',
                                                           default=True,
                                                           contact=customer1)

        customer2_address = Address.objects.create(owner=user,
                                                   street='32 rue du Pharaon',
                                                   zipcode='44000',
                                                   city='Nantes')
        customer2 = Contact.objects.create(owner=user,
                                           contact_type=CONTACT_TYPE_COMPANY,
                                           name='Flor Fina',
                                           company_id='88765432198765',
                                           legal_form='SARL',
                                           email='contact@florfinainc.com',

                                           representative='Philémon Siclone',
                                           representative_function='Gérant',
                                           address=customer2_address)
        customer2_phonenumber = PhoneNumber.objects.create(owner=user,
                                                           type=PHONENUMBER_TYPE_WORK,
                                                           number='0204040506',
                                                           default=True,
                                                           contact=customer2)

        customer3_address = Address.objects.create(owner=user,
                                                   street='6 rue des Carmes',
                                                   zipcode='75012',
                                                   city='Paris')
        customer3 = Contact.objects.create(owner=user,
                                           contact_type=CONTACT_TYPE_COMPANY,
                                           name='Paris Flash',
                                           company_id='78765432198765',
                                           legal_form='SARL',
                                           email='contact@parisflashpress.com',

                                           representative='Walter Rizotto',
                                           representative_function='Gérant',
                                           address=customer3_address)
        customer3_phonenumber = PhoneNumber.objects.create(owner=user,
                                                           type=PHONENUMBER_TYPE_WORK,
                                                           number='0105040506',
                                                           default=True,
                                                           contact=customer3)

        project1 = Project.objects.create(owner=user,
                                          name='Refonte site vitrine',
                                          customer=customer1,
                                          state=PROJECT_STATE_FINISHED)

        project2 = Project.objects.create(owner=user,
                                          name='Création site e-commerce',
                                          customer=customer1,
                                          state=PROJECT_STATE_STARTED)

        project3 = Project.objects.create(owner=user,
                                          name='Référencement',
                                          customer=customer2,
                                          state=PROJECT_STATE_PROPOSAL_ACCEPTED)

        project4 = Project.objects.create(owner=user,
                                          name='Création application métier',
                                          customer=customer3,
                                          state=PROJECT_STATE_PROSPECT)

        lorem_ipsum_proposal = """<h1>Conditions générales de ventes</h1><div>client : {{ client }}</div><h2>Lorem ipsum</h2><p>dolor sit amet, consectetur adipiscing elit. Praesent iaculis, elit at hendrerit ultricies, felis nunc commodo sem, sed dapibus diam mauris non enim. Proin sed erat massa, non laoreet nibh. Morbi id arcu sit amet metus accumsan ullamcorper ac sed lorem. Integer velit velit, pellentesque eu cursus vel, cursus nec lectus. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec eget turpis a sapien imperdiet adipiscing vel vitae sem. Sed egestas neque nec purus pulvinar non eleifend eros volutpat. Duis bibendum, lorem vitae tristique tincidunt, purus sem auctor nunc, porta malesuada erat eros et felis. Sed sem tellus, eleifend ut fermentum in, pulvinar elementum nunc. Phasellus mauris leo, rutrum ut vestibulum ac, porttitor a neque. Pellentesque ornare ultricies purus nec eleifend. Fusce mattis arcu ut eros dignissim tincidunt. Etiam tempus, nisl sit amet semper malesuada, augue ante semper turpis, eu ultricies magna leo non eros. In pellentesque, dui in congue fermentum, eros metus scelerisque quam, eu suscipit lacus urna in leo. Aliquam erat volutpat. Morbi in sollicitudin massa. Donec dictum, tellus ut tincidunt viverra, neque leo suscipit est, at luctus enim ante in metus. Nulla et justo nibh. Nunc non neque arcu, eget consectetur turpis. Quisque mattis aliquam lacus, sit amet consectetur enim feugiat sed.</p><h2>Donec turpis lectus</h2><p>auctor ac sagittis ac, rutrum id enim. Integer lobortis justo eu sapien viverra vel dapibus libero fermentum. Quisque sed nunc ipsum. Quisque vestibulum hendrerit sem vitae rhoncus. Nullam pharetra tortor et quam dignissim laoreet. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Sed tellus lectus, adipiscing at pellentesque sed, consectetur a ante. Curabitur aliquet nulla a ipsum convallis ac porta dui interdum. Etiam tristique metus in velit blandit id hendrerit magna rhoncus. Donec posuere orci ac diam faucibus rhoncus. Nulla facilisi. Proin imperdiet nisl quis ante laoreet sodales. Suspendisse potenti. Fusce rhoncus fermentum malesuada.</p><h2>Nullam tincidunt sapien</h2><p>et ligula gravida dignissim. Fusce condimentum aliquet mi in pellentesque. Vivamus elementum consequat mauris. Pellentesque a magna sed metus fringilla pharetra eu nec ante. Aliquam erat volutpat. Nam ac erat nec diam malesuada aliquet. Fusce ullamcorper nisl sed purus consectetur imperdiet. Vestibulum risus erat, pretium ut consequat et, iaculis vel orci. Integer vel diam velit, id mattis nunc. Pellentesque congue, turpis sed tempus consectetur, nulla lectus posuere velit, ac rhoncus metus nibh ut dolor. Donec in ante felis. Aliquam lacinia pellentesque dapibus. Praesent nulla metus, congue ac suscipit a, luctus pharetra orci. Mauris tincidunt egestas lectus, vitae suscipit dolor semper malesuada. Fusce imperdiet tincidunt convallis. Morbi sapien justo, pharetra a pharetra rhoncus, semper eu augue. Nulla eget nisl arcu, at cursus magna.</p><h2>Nullam auctor tempor</h2><p> magna nec dignissim. Pellentesque faucibus tellus a nisl faucibus ut consectetur felis bibendum. Morbi luctus pharetra pretium. Curabitur porttitor ipsum ut lectus pharetra eget consequat leo scelerisque. Mauris condimentum, urna in ultrices eleifend, lorem ligula pretium orci, ut condimentum urna orci ac nunc. Aliquam sit amet est et risus varius suscipit vitae ut ligula. Etiam orci tellus, laoreet non volutpat non, mollis nec nulla. Aenean pulvinar vestibulum aliquam. Proin eleifend dui urna, faucibus convallis quam. Sed aliquam leo et velit convallis rutrum. Ut in erat dolor. Nulla interdum tellus nec lacus porttitor malesuada. Nulla a lacus lectus, in congue nunc. Sed ac ipsum id mauris scelerisque hendrerit id aliquam odio. Duis faucibus orci sed arcu iaculis hendrerit. Aenean enim nunc, mollis ac sollicitudin eu, fringilla quis arcu. Sed facilisis, augue eu scelerisque hendrerit, libero justo suscipit orci, nec dapibus ligula eros sed orci.</p><h2>Sed vel ligula eget&nbsp;</h2><p>lacus imperdiet tempor. Quisque at massa a metus feugiat rhoncus eu eget erat. Sed posuere tempus augue laoreet tincidunt. Maecenas tempor, orci sed commodo volutpat, turpis magna euismod purus, id pulvinar ligula elit id eros. Ut laoreet magna eu leo interdum vel accumsan nisl congue. Vestibulum mollis risus quis sem iaculis sit amet dignissim elit commodo. Quisque a condimentum orci. Cras non interdum velit. Morbi feugiat sapien at augue vulputate tempus. Aliquam imperdiet sodales cursus. Donec nisl tellus, rhoncus nec sollicitudin sed, tristique a lacus. Fusce quis sollicitudin nibh. Pellentesque elementum metus et lacus bibendum tristique. Nulla auctor gravida nunc, sed sodales ante laoreet at. Morbi ut tellus in tellus malesuada porta. Nunc ligula erat, fermentum eu tempus sit amet, imperdiet sit amet lacus. Vestibulum quis mauris nec velit fermentum egestas a eu urna. Curabitur eros ipsum, lobortis nec faucibus sagittis, cursus id felis. Praesent vestibulum, diam vitae commodo lacinia, justo neque lobortis nulla, nec congue diam eros vel massa.</p>"""

        proposal1 = Proposal.objects.create(owner=user,
                                            reference='CRT_%i_001' % (now.year - 1),
                                            project=project1,
                                            update_date=datetime.date.today(),
                                            state=PROPOSAL_STATE_BALANCED,
                                            begin_date=datetime.date(now.year - 1, 6, 1),
                                            end_date=datetime.date(now.year - 1 , 6, 28),
                                            expiration_date=datetime.date(now.year - 1, 6, 1),
                                            contract_content=lorem_ipsum_proposal,
                                            amount=3000)

        proposal1_row1 = ProposalRow.objects.create(owner=user,
                                                    proposal=proposal1,
                                                    label='Charte graphique',
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=5,
                                                    unit_price='200')

        proposal1_row2 = ProposalRow.objects.create(owner=user,
                                                    proposal=proposal1,
                                                    label='Intégration et remplissage',
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=8,
                                                    unit_price='250')

        invoice1 = Invoice.objects.create(owner=user,
                                          customer=proposal1.project.customer,
                                          invoice_id=1,
                                          state=INVOICE_STATE_PAID,
                                          amount=4000,
                                          edition_date=datetime.date(now.year - 1, 6, 28),
                                          payment_date=datetime.date(now.year - 1, 7, 28),
                                          paid_date=datetime.date(now.year - 1, 7, 28),
                                          payment_type=PAYMENT_TYPE_CHECK,
                                          execution_begin_date=datetime.date(now.year - 1, 6, 1),
                                          execution_end_date=datetime.date(now.year - 1, 6, 28),
                                          penalty_date=datetime.date(now.year - 1, 7, 29),
                                          penalty_rate='1.95',
                                          discount_conditions='Néant')

        invoice1_row1 = InvoiceRow.objects.create(owner=user,
                                                  proposal=proposal1,
                                                  invoice=invoice1,
                                                  label='Charte graphique',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=5,
                                                  unit_price='200',
                                                  balance_payments=True)

        invoice1_row2 = InvoiceRow.objects.create(owner=user,
                                                  proposal=proposal1,
                                                  invoice=invoice1,
                                                  label='Intégration et remplissage',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=8,
                                                  unit_price='250',
                                                  balance_payments=True)

        proposal2 = Proposal.objects.create(owner=user,
                                            reference='CRT_%i_002' % (now.year - 1),
                                            project=project2,
                                            update_date=datetime.date.today(),
                                            state=PROPOSAL_STATE_ACCEPTED,
                                            begin_date=now - datetime.timedelta(90),
                                            end_date=now - datetime.timedelta(60),
                                            expiration_date=now - datetime.timedelta(90),
                                            contract_content=lorem_ipsum_proposal,
                                            amount=7000)

        proposal2_row1 = ProposalRow.objects.create(owner=user,
                                                    proposal=proposal2,
                                                    label='Charte graphique',
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=5,
                                                    unit_price='200')

        proposal2_row2 = ProposalRow.objects.create(owner=user,
                                                    proposal=proposal2,
                                                    label='Configuration modules',
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=15,
                                                    unit_price='300')

        proposal2_row3 = ProposalRow.objects.create(owner=user,
                                                    proposal=proposal2,
                                                    label='Installation serveur',
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=5,
                                                    unit_price='300')

        invoice2 = Invoice.objects.create(owner=user,
                                          customer=proposal2.project.customer,
                                          invoice_id=2,
                                          state=INVOICE_STATE_PAID,
                                          amount=2100,
                                          edition_date=now - datetime.timedelta(90),
                                          payment_date=now - datetime.timedelta(90),
                                          paid_date=now - datetime.timedelta(90),
                                          payment_type=PAYMENT_TYPE_CHECK,
                                          execution_begin_date=now - datetime.timedelta(90),
                                          execution_end_date=now - datetime.timedelta(60),
                                          penalty_date=now - datetime.timedelta(90),
                                          penalty_rate='1.95',
                                          discount_conditions='Néant')

        invoice2_row1 = InvoiceRow.objects.create(owner=user,
                                                  proposal=proposal2,
                                                  invoice=invoice2,
                                                  label='Accompte commande 30%',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=1,
                                                  unit_price='2100',
                                                  balance_payments=False)

        invoice3 = Invoice.objects.create(owner=user,
                                          customer=proposal2.project.customer,
                                          invoice_id=3,
                                          state=INVOICE_STATE_PAID,
                                          amount=1000,
                                          edition_date=now - datetime.timedelta(40),
                                          payment_date=now - datetime.timedelta(10),
                                          paid_date=now - datetime.timedelta(5),
                                          payment_type=PAYMENT_TYPE_CHECK,
                                          execution_begin_date=now - datetime.timedelta(90),
                                          execution_end_date=now - datetime.timedelta(60),
                                          penalty_date=now,
                                          penalty_rate='1.95',
                                          discount_conditions='Néant')


        invoice3_row1 = InvoiceRow.objects.create(owner=user,
                                                  proposal=proposal2,
                                                  invoice=invoice3,
                                                  label='Charte graphique',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=5,
                                                  unit_price='200',
                                                  balance_payments=False)

        invoice4 = Invoice.objects.create(owner=user,
                                          customer=proposal2.project.customer,
                                          invoice_id=4,
                                          state=INVOICE_STATE_SENT,
                                          amount=3900,
                                          edition_date=now - datetime.timedelta(30),
                                          payment_date=now - datetime.timedelta(1),
                                          payment_type=None,
                                          execution_begin_date=now - datetime.timedelta(90),
                                          execution_end_date=now - datetime.timedelta(60),
                                          penalty_date=now - datetime.timedelta(1),
                                          penalty_rate='1.95',
                                          discount_conditions='Néant')

        invoice4_row1 = InvoiceRow.objects.create(owner=user,
                                                  proposal=proposal2,
                                                  invoice=invoice4,
                                                  label='Configuration modules',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=15,
                                                  unit_price='300',
                                                  balance_payments=True)

        invoice4_row2 = InvoiceRow.objects.create(owner=user,
                                                  proposal=proposal2,
                                                  invoice=invoice4,
                                                  label='Installation serveur',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=5,
                                                  unit_price='300',
                                                  balance_payments=True)

        invoice4_row3 = InvoiceRow.objects.create(owner=user,
                                                  proposal=proposal2,
                                                  invoice=invoice4,
                                                  label='Accompte payé',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=1,
                                                  unit_price='-2100',
                                                  balance_payments=True)

        proposal3 = Proposal.objects.create(owner=user,
                                            reference='CRT_%i_001' % (now.year),
                                            project=project3,
                                            update_date=datetime.date.today(),
                                            state=PROPOSAL_STATE_ACCEPTED,
                                            begin_date=now + datetime.timedelta(10),
                                            end_date=now + datetime.timedelta(60),
                                            expiration_date=now + datetime.timedelta(10),
                                            contract_content=lorem_ipsum_proposal,
                                            amount=16000)

        proposal3_row1 = ProposalRow.objects.create(owner=user,
                                                    proposal=proposal3,
                                                    label="Préstation de conseil",
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=40,
                                                    unit_price='400')

        invoice5 = Invoice.objects.create(owner=user,
                                          customer=proposal3.project.customer,
                                          invoice_id=5,
                                          state=INVOICE_STATE_EDITED,
                                          amount=4500,
                                          edition_date=now - datetime.timedelta(1),
                                          payment_date=now + datetime.timedelta(30),
                                          execution_begin_date=now + datetime.timedelta(10),
                                          execution_end_date=now + datetime.timedelta(60),
                                          penalty_date=now + datetime.timedelta(30),
                                          penalty_rate='1.95',
                                          discount_conditions='Néant')

        invoice5_row1 = InvoiceRow.objects.create(owner=user,
                                                  proposal=proposal3,
                                                  invoice=invoice5,
                                                  label='Accompte commande 30%',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=1,
                                                  unit_price='4500',
                                                  balance_payments=False)

        proposal4 = Proposal.objects.create(owner=user,
                                            reference='CRT_%i_002' % (now.year),
                                            project=project4,
                                            update_date=datetime.date.today(),
                                            state=PROPOSAL_STATE_DRAFT,
                                            begin_date=now + datetime.timedelta(40),
                                            end_date=now + datetime.timedelta(90),
                                            expiration_date=now + datetime.timedelta(40),
                                            contract_content=lorem_ipsum_proposal,
                                            amount=5000)

        proposal4_row1 = ProposalRow.objects.create(owner=user,
                                                    proposal=proposal4,
                                                    label="Préstation d'audit",
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=10,
                                                    unit_price='500')

        expense = Expense.objects.create(owner=user,
                                         date=now - datetime.timedelta(45),
                                         reference='XYZ',
                                         supplier='GMG',
                                         amount=500,
                                         payment_type=PAYMENT_TYPE_BANK_CARD,
                                         description='Assurance pro')

        expense = Expense.objects.create(owner=user,
                                         date=now - datetime.timedelta(100),
                                         reference='ZYX',
                                         supplier='Matos.net',
                                         amount=700,
                                         payment_type=PAYMENT_TYPE_BANK_CARD,
                                         description='Achat pc')
