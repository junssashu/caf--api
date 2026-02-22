from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from core.models import Settings
from pdv.models import PointDeVente
from recouvrements.models import LigneRecouvrement, Recouvrement

TAUX = Decimal('0.02')


def make_aware(dt_str):
    return timezone.make_aware(datetime.fromisoformat(dt_str))


class Command(BaseCommand):
    help = 'Seed database with initial data'

    def add_arguments(self, parser):
        parser.add_argument('--no-input', action='store_true')

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write(self.style.WARNING('Database already seeded. Skipping.'))
            return

        self.stdout.write('Seeding database...')

        # Settings
        Settings.objects.get_or_create(id=1, defaults={'taux_commission': Decimal('2.00')})

        # Users
        users = {}
        user_data = [
            ('user-admin-1', 'Coulibaly Amadou', '0700000001', 'admin123', 'admin', None, True, '2025-06-01'),
            ('user-agent-1', 'Kone Mariame', '0700000010', 'agent123', 'agent', 'Cocody', True, '2025-06-15'),
            ('user-agent-2', 'Toure Ibrahim', '0700000011', 'agent123', 'agent', 'Yopougon', True, '2025-07-01'),
            ('user-agent-3', 'Diallo Fatou', '0700000012', 'agent123', 'agent', 'Plateau', True, '2025-07-15'),
            ('user-agent-4', 'Ouattara Seydou', '0700000013', 'agent123', 'agent', 'Marcory', True, '2025-08-01'),
            ('user-agent-5', 'Bamba Aissatou', '0700000014', 'agent123', 'agent', 'Abobo', False, '2025-08-15'),
        ]
        for uid, nom, tel, pwd, role, zone, active, created in user_data:
            u = User(
                nom=nom, telephone=tel, role=role, zone=zone,
                is_active=active,
            )
            u.set_password(pwd)
            u.save()
            # Override created_at
            User.objects.filter(pk=u.pk).update(created_at=make_aware(created))
            users[uid] = u
        self.stdout.write(f'  Created {len(users)} users')

        # PDVs
        pdvs = {}
        pdv_data = [
            ('pdv-01', 'CAF-100001', 'Boutique Chez Tanti Marie', 'Rue des Jardins, Cocody Angre', 'Abidjan', 'Cocody', 'Yao Marie-Claire', '0505000001', 'ACTIF', 'user-agent-1', '2025-07-01'),
            ('pdv-02', 'CAF-100002', 'Phone City Electronics', 'Boulevard Latrille, Cocody 2 Plateaux', 'Abidjan', 'Cocody', 'Aka Jean-Philippe', '0505000002', 'ACTIF', 'user-agent-1', '2025-07-10'),
            ('pdv-03', 'CAF-100003', 'Kiosque Mobile Plus', 'Carrefour Palmeraie, Cocody Riviera', 'Abidjan', 'Cocody', 'Dje Brigitte', '0505000003', 'EN_ATTENTE', 'user-agent-1', '2026-01-20'),
            ('pdv-04', 'CAF-100004', 'ETS Diallo & Fils', 'Rue du Marche, Yopougon Selmer', 'Abidjan', 'Yopougon', 'Diallo Moussa', '0505000004', 'ACTIF', 'user-agent-2', '2025-07-20'),
            ('pdv-05', 'CAF-100005', 'Cyber Cafe Le Phare', 'Avenue de la Mairie, Yopougon Toits Rouges', 'Abidjan', 'Yopougon', 'Koffi Emmanuel', '0505000005', 'ACTIF', 'user-agent-2', '2025-08-01'),
            ('pdv-06', 'CAF-100006', 'Telecoms Express Yop', 'Carrefour Siporex, Yopougon', 'Abidjan', 'Yopougon', 'Traore Adama', '0505000006', 'ACTIF', 'user-agent-2', '2025-08-15'),
            ('pdv-07', 'CAF-100007', 'Multi-Services Plateau', 'Avenue Chardy, Plateau', 'Abidjan', 'Plateau', 'Boni Christophe', '0505000007', 'ACTIF', 'user-agent-3', '2025-08-01'),
            ('pdv-08', 'CAF-100008', 'Boutique Telecom Adjame', 'Marche Gouro, Adjame', 'Abidjan', 'Adjame', 'Sanogo Lamine', '0505000008', 'ACTIF', 'user-agent-3', '2025-08-10'),
            ('pdv-09', 'CAF-100009', 'Digital Center Treichville', 'Rue 12, Treichville', 'Abidjan', 'Treichville', 'Konan Affoue', '0505000009', 'INACTIF', 'user-agent-3', '2025-08-20'),
            ('pdv-10', 'CAF-100010', 'Espace MoMo Marcory', 'Zone 4, Boulevard de Marseille', 'Abidjan', 'Marcory', 'Dosso Karidja', '0505000010', 'ACTIF', 'user-agent-4', '2025-09-01'),
            ('pdv-11', 'CAF-100011', 'Orange Shop Koumassi', 'Carrefour Koumassi Remblai', 'Abidjan', 'Koumassi', 'Yapi Franck', '0505000011', 'ACTIF', 'user-agent-4', '2025-09-10'),
            ('pdv-12', 'CAF-100012', 'Kiosque Chez Papa Kone', 'Marcory Anoumabo, Rue Principale', 'Abidjan', 'Marcory', 'Kone Vassiriki', '0505000012', 'ACTIF', 'user-agent-4', '2025-09-20'),
            ('pdv-13', 'CAF-100013', 'Transfert Rapide Abobo', 'Abobo Baoule, Face Mairie', 'Abidjan', 'Abobo', 'Cisse Mamadou', '0505000013', 'INACTIF', 'user-agent-5', '2025-09-01'),
            ('pdv-14', 'CAF-100014', 'Papeterie Moderne Abobo', 'Abobo Gare, Avenue Principale', 'Abidjan', 'Abobo', 'Fofana Issouf', '0505000014', 'INACTIF', 'user-agent-5', '2025-09-15'),
            ('pdv-15', 'CAF-100015', 'Station Mobile Abobo PK', 'Abobo PK18, Carrefour', 'Abidjan', 'Abobo', 'Berthe Rokia', '0505000015', 'ACTIF', 'user-agent-5', '2025-10-01'),
        ]
        for pid, code, nom, adresse, ville, commune, prop_nom, prop_tel, st, agent_key, created in pdv_data:
            p = PointDeVente.objects.create(
                code=code, nom=nom, adresse=adresse, ville=ville, commune=commune,
                proprietaire_nom=prop_nom, proprietaire_telephone=prop_tel,
                status=st, agent=users[agent_key],
            )
            PointDeVente.objects.filter(pk=p.pk).update(created_at=make_aware(created))
            pdvs[pid] = p
        self.stdout.write(f'  Created {len(pdvs)} PDVs')

        # Recouvrements
        rec_data = [
            # (code, pdv_key, agent_key, lignes, methode, status, reference, notes, created, validated)
            ('CAF-200001', 'pdv-01', 'user-agent-1',
             [('Eau minerale 1.5L', 'BOISSONS', 500, 20), ('Coca-Cola 33cl', 'BOISSONS', 300, 30)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90001', 'Livraison boissons reguliere', '2026-01-19', '2026-01-19'),
            ('CAF-200002', 'pdv-01', 'user-agent-1',
             [('Riz parfume 5kg', 'ALIMENTATION', 3500, 10), ('Huile de palme 1L', 'ALIMENTATION', 1200, 15)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80001', None, '2026-01-21', '2026-01-21'),
            ('CAF-200003', 'pdv-02', 'user-agent-1',
             [('T-shirt coton homme', 'HABILLEMENT', 2500, 10)],
             'ESPECES', 'VALIDE', None, 'Lot de t-shirts pour boutique', '2026-01-23', '2026-01-23'),
            ('CAF-200004', 'pdv-02', 'user-agent-1',
             [('Ecouteurs Bluetooth', 'ELECTRONIQUE', 5000, 20), ('Chargeur telephone universel', 'ELECTRONIQUE', 2000, 25)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90002', None, '2026-01-26', '2026-01-27'),
            ('CAF-200005', 'pdv-01', 'user-agent-1',
             [('Biere Flag 65cl', 'BOISSONS', 700, 24)],
             'ESPECES', 'EN_ATTENTE', None, 'Casier de bieres', '2026-02-14', None),
            ('CAF-200006', 'pdv-02', 'user-agent-1',
             [('Sac de ciment 50kg', 'AUTRE', 5500, 50), ('Fer a beton 10mm', 'AUTRE', 3000, 30)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90003', 'Materiaux de construction', '2026-02-16', '2026-02-16'),
            # Agent 2
            ('CAF-200007', 'pdv-04', 'user-agent-2',
             [('Tomates fraiches 1kg', 'ALIMENTATION', 800, 25), ('Oignons 1kg', 'ALIMENTATION', 600, 20), ('Piment frais 1kg', 'ALIMENTATION', 1000, 10)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80002', None, '2026-01-20', '2026-01-20'),
            ('CAF-200008', 'pdv-05', 'user-agent-2',
             [('Coque telephone Samsung', 'ELECTRONIQUE', 1500, 30), ('Protection ecran iPhone', 'ELECTRONIQUE', 2000, 20)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90004', None, '2026-01-22', '2026-01-22'),
            ('CAF-200009', 'pdv-06', 'user-agent-2',
             [('Savon de Marseille', 'AUTRE', 500, 30)],
             'ESPECES', 'VALIDE', None, 'Lot de savons pour boutique', '2026-01-25', '2026-01-25'),
            ('CAF-200010', 'pdv-04', 'user-agent-2',
             [('Jus de bissap 1L', 'BOISSONS', 1000, 50), ('Jus de gingembre 1L', 'BOISSONS', 1000, 50), ('Eau minerale 0.5L pack', 'BOISSONS', 1500, 40)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80003', 'Grosse commande boissons', '2026-01-28', '2026-01-29'),
            ('CAF-200011', 'pdv-05', 'user-agent-2',
             [('Chaussures sport homme', 'HABILLEMENT', 8000, 10)],
             'MTN_MOMO', 'REJETE', 'MTN-TXN-90005', 'Transaction echouee - solde insuffisant', '2026-02-01', None),
            ('CAF-200012', 'pdv-06', 'user-agent-2',
             [('Attieke 500g', 'ALIMENTATION', 300, 50), ('Poisson braise', 'ALIMENTATION', 1500, 20)],
             'ESPECES', 'VALIDE', None, 'Commande restaurant maquis', '2026-02-03', '2026-02-03'),
            ('CAF-200013', 'pdv-04', 'user-agent-2',
             [('Pagne wax 6 yards', 'HABILLEMENT', 15000, 5), ('Tissu basin riche', 'HABILLEMENT', 12000, 3)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90006', None, '2026-02-10', '2026-02-10'),
            ('CAF-200014', 'pdv-05', 'user-agent-2',
             [('Telephone portable basique', 'ELECTRONIQUE', 15000, 8)],
             'ORANGE_MONEY', 'EN_ATTENTE', 'OM-TXN-80004', None, '2026-02-17', None),
            # Agent 3
            ('CAF-200015', 'pdv-07', 'user-agent-3',
             [('Lait concentre sucre', 'ALIMENTATION', 600, 100), ('Sucre en morceaux 1kg', 'ALIMENTATION', 800, 50), ('The Lipton boite 100', 'ALIMENTATION', 2500, 20)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80005', 'Approvisionnement epicerie Plateau', '2026-01-19', '2026-01-19'),
            ('CAF-200016', 'pdv-08', 'user-agent-3',
             [('Fanta orange 1.5L', 'BOISSONS', 600, 30), ('Sprite 1.5L', 'BOISSONS', 600, 20)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90007', None, '2026-01-24', '2026-01-24'),
            ('CAF-200017', 'pdv-07', 'user-agent-3',
             [('Robe pagne femme', 'HABILLEMENT', 5000, 6)],
             'ESPECES', 'VALIDE', None, None, '2026-01-27', '2026-01-27'),
            ('CAF-200018', 'pdv-08', 'user-agent-3',
             [('Cle USB 32Go', 'ELECTRONIQUE', 3000, 20), ('Carte memoire 64Go', 'ELECTRONIQUE', 5000, 15), ('Cable HDMI 2m', 'ELECTRONIQUE', 2500, 10)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80006', None, '2026-01-30', '2026-01-31'),
            ('CAF-200019', 'pdv-07', 'user-agent-3',
             [('Sandales en cuir', 'HABILLEMENT', 4000, 5)],
             'ESPECES', 'REJETE', None, 'Montant incorrect - client conteste', '2026-02-04', None),
            ('CAF-200020', 'pdv-08', 'user-agent-3',
             [('Malt Guinness 33cl', 'BOISSONS', 500, 48), ('Youki soda 1L', 'BOISSONS', 400, 36)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90008', None, '2026-02-07', '2026-02-07'),
            ('CAF-200021', 'pdv-07', 'user-agent-3',
             [('Savon noir artisanal', 'AUTRE', 800, 10)],
             'ESPECES', 'VALIDE', None, 'Produits artisanaux', '2026-02-12', '2026-02-12'),
            # Agent 4
            ('CAF-200022', 'pdv-10', 'user-agent-4',
             [('Sac de riz 25kg', 'ALIMENTATION', 12000, 20), ('Bidon huile 5L', 'ALIMENTATION', 5000, 15)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90009', 'Grossiste alimentation', '2026-01-20', '2026-01-20'),
            ('CAF-200023', 'pdv-11', 'user-agent-4',
             [('Javel 1L', 'AUTRE', 500, 40), ('Detergent en poudre 1kg', 'AUTRE', 1500, 20)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80007', None, '2026-01-23', '2026-01-23'),
            ('CAF-200024', 'pdv-12', 'user-agent-4',
             [('Banane plantain 1kg', 'ALIMENTATION', 400, 30)],
             'ESPECES', 'VALIDE', None, 'Marche de gros', '2026-01-26', '2026-01-26'),
            ('CAF-200025', 'pdv-10', 'user-agent-4',
             [('Ventilateur de table', 'ELECTRONIQUE', 12000, 10), ('Multiprise 5 prises', 'ELECTRONIQUE', 3000, 15)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80008', None, '2026-01-30', '2026-01-30'),
            ('CAF-200026', 'pdv-11', 'user-agent-4',
             [('Chemise homme manches courtes', 'HABILLEMENT', 3500, 15), ('Pantalon jean homme', 'HABILLEMENT', 6000, 10)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90010', None, '2026-02-02', '2026-02-02'),
            ('CAF-200027', 'pdv-12', 'user-agent-4',
             [('Beurre de karite 500g', 'AUTRE', 1500, 5)],
             'ESPECES', 'VALIDE', None, 'Produits cosmetiques naturels', '2026-02-05', '2026-02-05'),
            ('CAF-200028', 'pdv-10', 'user-agent-4',
             [('Sardines en conserve', 'ALIMENTATION', 500, 100), ('Pate tomate 400g', 'ALIMENTATION', 800, 50), ('Cube Maggi (carton)', 'ALIMENTATION', 3000, 30)],
             'MTN_MOMO', 'EN_ATTENTE', 'MTN-TXN-90011', 'En attente validation superviseur', '2026-02-15', None),
            ('CAF-200029', 'pdv-11', 'user-agent-4',
             [('Coca-Cola 1.5L', 'BOISSONS', 600, 25)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80009', 'Livraison boissons', '2026-02-11', '2026-02-11'),
            # Agent 5
            ('CAF-200030', 'pdv-15', 'user-agent-5',
             [('Mangues fraiches 1kg', 'ALIMENTATION', 500, 30), ('Ananas Victoria', 'ALIMENTATION', 800, 20)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80010', None, '2026-01-19', '2026-01-19'),
            ('CAF-200031', 'pdv-13', 'user-agent-5',
             [('Lampe torche LED', 'ELECTRONIQUE', 2500, 10), ('Piles AA (pack 4)', 'ELECTRONIQUE', 800, 30)],
             'MTN_MOMO', 'REJETE', 'MTN-TXN-90012', 'PDV desactive - transaction annulee', '2026-01-22', None),
            ('CAF-200032', 'pdv-15', 'user-agent-5',
             [('Igname 1kg', 'ALIMENTATION', 600, 15)],
             'ESPECES', 'VALIDE', None, 'Derniere transaction avant desactivation agent', '2026-01-25', '2026-01-25'),
            # Additional
            ('CAF-200033', 'pdv-01', 'user-agent-1',
             [('Poulet congele 1kg', 'ALIMENTATION', 2000, 30), ('Poisson congele 1kg', 'ALIMENTATION', 2500, 20)],
             'ORANGE_MONEY', 'VALIDE', 'OM-TXN-80011', None, '2026-02-08', '2026-02-08'),
            ('CAF-200034', 'pdv-04', 'user-agent-2',
             [('Claquettes homme', 'HABILLEMENT', 2000, 10)],
             'ESPECES', 'VALIDE', None, 'Chaussures legeres', '2026-02-06', '2026-02-06'),
            ('CAF-200035', 'pdv-07', 'user-agent-3',
             [('Lait en poudre Nido 400g', 'ALIMENTATION', 3500, 20), ('Cafe soluble 200g', 'ALIMENTATION', 2000, 15), ('Chocolat en poudre 500g', 'ALIMENTATION', 2500, 10)],
             'MTN_MOMO', 'VALIDE', 'MTN-TXN-90013', 'Epicerie fine Plateau', '2026-02-13', '2026-02-13'),
            ('CAF-200036', 'pdv-12', 'user-agent-4',
             [('Rallonge electrique 5m', 'ELECTRONIQUE', 3500, 12)],
             'ORANGE_MONEY', 'EN_ATTENTE', 'OM-TXN-80012', 'Verification en cours', '2026-02-18', None),
        ]

        rec_count = 0
        for code, pdv_key, agent_key, lignes, methode, st, ref, notes, created, validated in rec_data:
            # Compute montant
            computed_lignes = []
            montant = 0
            for nom_produit, categorie, prix, qte in lignes:
                sous_total = prix * qte
                montant += sous_total
                computed_lignes.append((nom_produit, categorie, prix, qte, sous_total))

            commission = round(montant * float(TAUX))

            rec = Recouvrement.objects.create(
                code=code,
                point_de_vente=pdvs[pdv_key],
                agent=users[agent_key],
                montant=montant,
                taux_commission=TAUX,
                commission=commission,
                methode_paiement=methode,
                status=st,
                reference=ref,
                notes=notes,
                validated_at=make_aware(validated) if validated else None,
            )
            Recouvrement.objects.filter(pk=rec.pk).update(created_at=make_aware(created))

            for nom_produit, categorie, prix, qte, sous_total in computed_lignes:
                LigneRecouvrement.objects.create(
                    recouvrement=rec,
                    nom_produit=nom_produit,
                    categorie=categorie,
                    prix_unitaire=prix,
                    quantite=qte,
                    sous_total=sous_total,
                )
            rec_count += 1

        self.stdout.write(f'  Created {rec_count} recouvrements')
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
