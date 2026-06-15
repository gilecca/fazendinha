from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Category, ProducerProfile, Product, Cart, Review

User = get_user_model()

CATEGORIES = [
    ('Queijo', 'queijo'),
    ('Café', 'cafe'),
    ('Hortaliças', 'hortalicas'),
    ('Doces', 'doces'),
    ('Leite', 'leite'),
    ('Frutas', 'frutas'),
]

PRODUCERS = [
    {
        'username': 'fazenda_bela',
        'password': 'fazenda123',
        'first_name': 'Maria',
        'last_name': 'Silva',
        'email': 'maria@fazendabela.com',
        'phone': '(31) 99999-1111',
        'city': 'Ouro Preto',
        'farm_name': 'Fazenda Bela Vista',
        'description': 'Produzimos com amor queijos artesanais e laticínios de alta qualidade há 30 anos. Nossa fazenda fica no coração de Minas Gerais, com vacas criadas soltas e alimentadas com pastagem natural.',
        'address': 'Estrada Rural, km 5',
        'city_farm': 'Ouro Preto',
        'state': 'MG',
    },
    {
        'username': 'sitio_verde',
        'password': 'fazenda123',
        'first_name': 'João',
        'last_name': 'Pereira',
        'email': 'joao@sitiverde.com',
        'phone': '(31) 99999-2222',
        'city': 'Lavras',
        'farm_name': 'Sítio Verde Esperança',
        'description': 'Orgânicos certificados! Cultivamos frutas, hortaliças e doces artesanais sem agrotóxicos. Venha nos visitar e conhecer nossa produção sustentável.',
        'address': 'Rua das Flores, 100',
        'city_farm': 'Lavras',
        'state': 'MG',
    },
]

CONSUMERS = [
    {'username': 'ana_consumidora', 'password': 'teste123', 'first_name': 'Ana', 'last_name': 'Costa',
     'email': 'ana@email.com', 'phone': '(31) 98888-0001', 'city': 'Belo Horizonte'},
    {'username': 'carlos_compras', 'password': 'teste123', 'first_name': 'Carlos', 'last_name': 'Oliveira',
     'email': 'carlos@email.com', 'phone': '(31) 98888-0002', 'city': 'Contagem'},
]

PRODUCTS = [
    # Fazenda Bela Vista
    {'producer_idx': 0, 'category': 'queijo', 'name': 'Queijo Minas Artesanal',
     'description': 'Queijo minas artesanal curado por 30 dias, sabor suave e textura firme. Produzido com leite fresco das nossas vacas.',
     'price': '32.90', 'weight': '500g', 'stock': 20, 'is_featured': True},
    {'producer_idx': 0, 'category': 'queijo', 'name': 'Queijo Colonial Defumado',
     'description': 'Queijo defumado artesanalmente com madeira de goiabeira. Aroma incrível e sabor marcante.',
     'price': '45.00', 'weight': '400g', 'stock': 15, 'is_featured': False},
    {'producer_idx': 0, 'category': 'leite', 'name': 'Leite Integral Fresco',
     'description': 'Leite integral pasteurizado, colhido pela manhã e entregue no mesmo dia. Cremoso e nutritivo.',
     'price': '7.50', 'weight': '1 litro', 'stock': 50, 'is_featured': True, 'is_promotion': True, 'promotion_price': '6.00'},
    {'producer_idx': 0, 'category': 'doces', 'name': 'Doce de Leite Cremoso',
     'description': 'Doce de leite feito em tacho de cobre, receita de família. Textura cremosa e sabor incomparável.',
     'price': '18.00', 'weight': '350g', 'stock': 30, 'is_featured': True},

    # Sítio Verde
    {'producer_idx': 1, 'category': 'cafe', 'name': 'Café Especial Orgânico',
     'description': 'Café especial cultivado em altitude, torra média. Notas de caramelo e frutas vermelhas. Certificado orgânico.',
     'price': '38.00', 'weight': '250g', 'stock': 25, 'is_featured': True},
    {'producer_idx': 1, 'category': 'hortalicas', 'name': 'Cesta de Hortaliças Orgânicas',
     'description': 'Cesta semanal com alface, rúcula, espinafre, cenoura e beterraba. Tudo orgânico e colhido na manhã do dia.',
     'price': '35.00', 'weight': 'Cesta mista', 'stock': 10, 'is_featured': True, 'is_promotion': True, 'promotion_price': '28.00'},
    {'producer_idx': 1, 'category': 'frutas', 'name': 'Banana Prata da Serra',
     'description': 'Bananas prata cultivadas nas montanhas, sem agrotóxicos. Doces e nutritivas.',
     'price': '12.00', 'weight': '1 kg', 'stock': 40, 'is_featured': False},
    {'producer_idx': 1, 'category': 'doces', 'name': 'Geleia de Jabuticaba',
     'description': 'Geleia artesanal de jabuticaba colhida no sítio. Sabor intenso, sem conservantes artificiais.',
     'price': '22.00', 'weight': '300g', 'stock': 18, 'is_featured': True},
    {'producer_idx': 1, 'category': 'frutas', 'name': 'Manga Tommy Orgânica',
     'description': 'Mangas Tommy cultivadas sem agrotóxicos. Carnudas, doces e suculentas. Da época!',
     'price': '15.00', 'weight': '1 kg', 'stock': 20, 'is_promotion': True, 'promotion_price': '10.00'},
]


class Command(BaseCommand):
    help = 'Popula o banco com dados de exemplo para demonstração'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando seed de dados...')

        # Categorias
        cat_map = {}
        for name, slug in CATEGORIES:
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name})
            cat_map[slug] = cat
            self.stdout.write(f'  Categoria: {name}')

        # Produtores
        producers = []
        for p in PRODUCERS:
            user, created = User.objects.get_or_create(
                username=p['username'],
                defaults={
                    'first_name': p['first_name'], 'last_name': p['last_name'],
                    'email': p['email'], 'phone': p['phone'],
                    'city': p['city'], 'user_type': 'producer',
                }
            )
            if created:
                user.set_password(p['password'])
                user.save()
            Cart.objects.get_or_create(user=user)
            profile, _ = ProducerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'farm_name': p['farm_name'], 'description': p['description'],
                    'address': p['address'], 'city': p['city_farm'], 'state': p['state'],
                }
            )
            producers.append(profile)
            self.stdout.write(f'  Produtor: {p["farm_name"]}')

        # Consumidores
        for c in CONSUMERS:
            user, created = User.objects.get_or_create(
                username=c['username'],
                defaults={
                    'first_name': c['first_name'], 'last_name': c['last_name'],
                    'email': c['email'], 'phone': c['phone'],
                    'city': c['city'], 'user_type': 'consumer',
                }
            )
            if created:
                user.set_password(c['password'])
                user.save()
            Cart.objects.get_or_create(user=user)
            self.stdout.write(f'  Consumidor: {c["first_name"]} {c["last_name"]}')

        # Produtos
        for p in PRODUCTS:
            producer = producers[p['producer_idx']]
            category = cat_map[p['category']]
            product, _ = Product.objects.get_or_create(
                name=p['name'],
                producer=producer,
                defaults={
                    'category': category, 'description': p['description'],
                    'price': p['price'], 'weight': p['weight'],
                    'stock': p['stock'],
                    'is_featured': p.get('is_featured', False),
                    'is_promotion': p.get('is_promotion', False),
                    'promotion_price': p.get('promotion_price'),
                    'is_available': True,
                }
            )
            self.stdout.write(f'  Produto: {p["name"]}')

        # Avaliacoes de exemplo
        consumer1 = User.objects.filter(username='ana_consumidora').first()
        if consumer1 and producers:
            Review.objects.get_or_create(
                reviewer=consumer1, producer=producers[0],
                defaults={'quality': 5, 'delivery': 4, 'service': 5,
                          'comment': 'Queijo maravilhoso! Chegou super fresco e bem embalado. Com certeza vou comprar mais!'}
            )
            Review.objects.get_or_create(
                reviewer=consumer1, producer=producers[1],
                defaults={'quality': 5, 'delivery': 5, 'service': 5,
                          'comment': 'Produtos organicos de qualidade excepcional! A cesta de hortalicas e incrivel, tudo fresquinho!'}
            )

        self.stdout.write(self.style.SUCCESS('\nDados criados com sucesso!'))
        self.stdout.write('\nLogins de acesso:')
        self.stdout.write('  Produtor 1: fazenda_bela / fazenda123')
        self.stdout.write('  Produtor 2: sitio_verde  / fazenda123')
        self.stdout.write('  Consumidor: ana_consumidora / teste123')
        self.stdout.write('  Admin:      admin / admin123')
