import os
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from product.models import Company, Category, Product
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample companies, categories, and products'

    def download_image(self, url, name):
        """Download image from URL"""
        try:
            self.stdout.write(f'Downloading image from {url}')
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return ContentFile(response.content, name=name)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to download {url}: {e}'))
            return None

    def handle(self, *args, **options):
        self.stdout.write('Starting database population...')

        # Create test users
        users_data = [
            {'email': 'user@test.com', 'username': 'testuser', 'password': 'user123', 'phone_number': '+1111111111', 'role': 'user'},
            {'email': 'manager@test.com', 'username': 'manager', 'password': 'manager123', 'phone_number': '+2222222222', 'role': 'manager'},
            {'email': 'courier@test.com', 'username': 'courier', 'password': 'courier123', 'phone_number': '+3333333333', 'role': 'courier'},
            {'email': 'admin@test.com', 'username': 'admin', 'password': 'admin123', 'phone_number': '+4444444444', 'role': 'admin'},
            {'email': 'john@test.com', 'username': 'john', 'password': 'john123', 'phone_number': '+5555555555', 'role': 'user'},
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['username'],
                    'phone_number': user_data['phone_number'],
                    'role': user_data['role'],
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))
            else:
                self.stdout.write(f'User exists: {user.username}')

        # Companies (Restaurants) data
        companies_data = [
            {
                'name': "McDonald's",
                'logo_url': 'https://images.unsplash.com/photo-1619454016518-697bc231e7aa?w=400',
                'rating': Decimal('4.5'),
                'description': 'Fast food restaurant chain serving burgers, fries, and more',
                'phone_number': '+1234567890',
                'address': '123 Main St, New York, NY'
            },
            {
                'name': 'KFC',
                'logo_url': 'https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400',
                'rating': Decimal('4.3'),
                'description': 'Fried chicken fast food chain',
                'phone_number': '+1234567891',
                'address': '456 Oak Ave, Los Angeles, CA'
            },
            {
                'name': 'Pizza Hut',
                'logo_url': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400',
                'rating': Decimal('4.4'),
                'description': 'Pizza restaurant chain with delivery and dine-in options',
                'phone_number': '+1234567892',
                'address': '789 Pizza Blvd, Chicago, IL'
            },
            {
                'name': 'Subway',
                'logo_url': 'https://images.unsplash.com/photo-1579888944880-d98341245702?w=400',
                'rating': Decimal('4.2'),
                'description': 'Submarine sandwich restaurant chain',
                'phone_number': '+1234567893',
                'address': '321 Sandwich St, Boston, MA'
            },
            {
                'name': 'Starbucks',
                'logo_url': 'https://images.unsplash.com/photo-1578374173705-aa0dc6aa9a7f?w=400',
                'rating': Decimal('4.6'),
                'description': 'Coffee shop and coffeehouse chain',
                'phone_number': '+1234567894',
                'address': '654 Coffee Rd, Seattle, WA'
            },
            {
                'name': 'Taco Bell',
                'logo_url': 'https://images.unsplash.com/photo-1580238053495-b9720401fd45?w=400',
                'rating': Decimal('4.1'),
                'description': 'Mexican-inspired fast food chain',
                'phone_number': '+1234567895',
                'address': '987 Taco Way, Austin, TX'
            },
            {
                'name': 'Burger King',
                'logo_url': 'https://images.unsplash.com/photo-1603064752734-4c48eff53d05?w=400',
                'rating': Decimal('4.3'),
                'description': 'Fast food burger restaurant chain',
                'phone_number': '+1234567896',
                'address': '147 Burger Lane, Miami, FL'
            },
            {
                'name': "Domino's Pizza",
                'logo_url': 'https://images.unsplash.com/photo-1604068549290-dea0e4a305ca?w=400',
                'rating': Decimal('4.5'),
                'description': 'Pizza delivery and carryout chain',
                'phone_number': '+1234567897',
                'address': '258 Delivery Dr, Detroit, MI'
            },
        ]

        companies = {}
        for company_data in companies_data:
            company, created = Company.objects.get_or_create(
                name=company_data['name'],
                defaults={
                    'rating': company_data['rating'],
                    'description': company_data['description'],
                    'phone_number': company_data['phone_number'],
                    'address': company_data['address'],
                }
            )
            
            # Always download and update logo
            if company.logo:
                company.logo.delete(save=False)
            
            logo_file = self.download_image(company_data['logo_url'], f"{company_data['name'].lower().replace(' ', '_')}.jpg")
            if logo_file:
                company.logo = logo_file
                company.save()
                self.stdout.write(self.style.SUCCESS(f'Created/Updated company: {company.name}'))
            
            companies[company.name] = company

        # Categories data
        categories_data = [
            {'name': 'Burgers', 'image_url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400', 'description': 'Delicious burgers'},
            {'name': 'Pizza', 'image_url': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400', 'description': 'Hot and fresh pizza'},
            {'name': 'Chicken', 'image_url': 'https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400', 'description': 'Fried and grilled chicken'},
            {'name': 'Drinks', 'image_url': 'https://images.unsplash.com/photo-1437418747212-8d9709afab22?w=400', 'description': 'Refreshing beverages'},
            {'name': 'Desserts', 'image_url': 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400', 'description': 'Sweet treats'},
            {'name': 'Sandwiches', 'image_url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400', 'description': 'Fresh sandwiches'},
            {'name': 'Tacos', 'image_url': 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400', 'description': 'Mexican tacos'},
            {'name': 'Coffee', 'image_url': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400', 'description': 'Hot and cold coffee'},
            {'name': 'Salads', 'image_url': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400', 'description': 'Fresh and healthy salads'},
            {'name': 'Sides', 'image_url': 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400', 'description': 'Side dishes and snacks'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            
            # Always download and update image
            if category.image:
                category.image.delete(save=False)
            
            image_file = self.download_image(cat_data['image_url'], f"{cat_data['name'].lower()}.jpg")
            if image_file:
                category.image = image_file
                category.save()
                self.stdout.write(self.style.SUCCESS(f'Created/Updated category: {category.name}'))
            
            categories[category.name] = category

        # Products data
        products_data = [
            # McDonald's
            {'name': 'Big Mac', 'company': "McDonald's", 'category': 'Burgers', 'price': Decimal('5.99'), 'discount': Decimal('4.99'), 'rating': Decimal('4.7'), 'image_url': 'https://images.unsplash.com/photo-1550547660-d9450f859349?w=400', 'description': 'Two all-beef patties, special sauce, lettuce, cheese, pickles, onions on a sesame seed bun', 'ingredients': 'Beef, lettuce, cheese, pickles, onions, special sauce', 'grams': 215},
            {'name': 'French Fries', 'company': "McDonald's", 'category': 'Sides', 'price': Decimal('2.99'), 'discount': Decimal('2.49'), 'rating': Decimal('4.5'), 'image_url': 'https://images.unsplash.com/photo-1576107232684-1279f390859f?w=400', 'description': 'Golden crispy french fries', 'ingredients': 'Potatoes, salt, oil', 'grams': 150},
            {'name': 'McFlurry Oreo', 'company': "McDonald's", 'category': 'Desserts', 'price': Decimal('3.99'), 'discount': Decimal('3.49'), 'rating': Decimal('4.6'), 'image_url': 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400', 'description': 'Vanilla soft serve with Oreo pieces', 'ingredients': 'Ice cream, Oreo cookies', 'grams': 200},
            {'name': 'Coca Cola', 'company': "McDonald's", 'category': 'Drinks', 'price': Decimal('1.99'), 'discount': Decimal('1.49'), 'rating': Decimal('4.3'), 'image_url': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400', 'description': 'Refreshing Coca Cola', 'ingredients': 'Carbonated water, sugar, caffeine', 'grams': 500},
            
            # KFC
            {'name': 'Original Recipe Chicken', 'company': 'KFC', 'category': 'Chicken', 'price': Decimal('8.99'), 'discount': Decimal('7.99'), 'rating': Decimal('4.8'), 'image_url': 'https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400', 'description': 'Crispy fried chicken with 11 herbs and spices', 'ingredients': 'Chicken, breading, spices', 'grams': 300},
            {'name': 'Coleslaw', 'company': 'KFC', 'category': 'Sides', 'price': Decimal('2.49'), 'discount': Decimal('1.99'), 'rating': Decimal('4.2'), 'image_url': 'https://images.unsplash.com/photo-1604909052743-94e838986d24?w=400', 'description': 'Fresh cabbage salad with creamy dressing', 'ingredients': 'Cabbage, mayonnaise, vinegar', 'grams': 150},
            {'name': 'Chicken Burger', 'company': 'KFC', 'category': 'Burgers', 'price': Decimal('6.99'), 'discount': Decimal('5.99'), 'rating': Decimal('4.6'), 'image_url': 'https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400', 'description': 'Crispy chicken fillet in a soft bun', 'ingredients': 'Chicken, lettuce, mayo, bun', 'grams': 250},
            
            # Pizza Hut
            {'name': 'Pepperoni Pizza', 'company': 'Pizza Hut', 'category': 'Pizza', 'price': Decimal('12.99'), 'discount': Decimal('10.99'), 'rating': Decimal('4.7'), 'image_url': 'https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400', 'description': 'Classic pepperoni pizza with mozzarella', 'ingredients': 'Dough, tomato sauce, mozzarella, pepperoni', 'grams': 800},
            {'name': 'Cheese Pizza', 'company': 'Pizza Hut', 'category': 'Pizza', 'price': Decimal('10.99'), 'discount': Decimal('9.49'), 'rating': Decimal('4.5'), 'image_url': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400', 'description': 'Simple cheese pizza with tomato sauce', 'ingredients': 'Dough, tomato sauce, mozzarella', 'grams': 700},
            {'name': 'Garlic Bread', 'company': 'Pizza Hut', 'category': 'Sides', 'price': Decimal('4.99'), 'discount': Decimal('3.99'), 'rating': Decimal('4.4'), 'image_url': 'https://images.unsplash.com/photo-1573140401552-3fab0b24f5cf?w=400', 'description': 'Crispy bread with garlic butter', 'ingredients': 'Bread, garlic, butter, parsley', 'grams': 200},
            
            # Subway
            {'name': 'Italian BMT', 'company': 'Subway', 'category': 'Sandwiches', 'price': Decimal('7.99'), 'discount': Decimal('6.99'), 'rating': Decimal('4.6'), 'image_url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400', 'description': 'Ham, salami, pepperoni with cheese and veggies', 'ingredients': 'Ham, salami, pepperoni, cheese, lettuce, tomato, bread', 'grams': 300},
            {'name': 'Veggie Delite', 'company': 'Subway', 'category': 'Sandwiches', 'price': Decimal('5.99'), 'discount': Decimal('4.99'), 'rating': Decimal('4.3'), 'image_url': 'https://images.unsplash.com/photo-1623428187969-5da2dcea5ebf?w=400', 'description': 'Fresh vegetables on wheat bread', 'ingredients': 'Lettuce, tomato, cucumber, peppers, bread', 'grams': 250},
            {'name': 'Chicken Teriyaki', 'company': 'Subway', 'category': 'Sandwiches', 'price': Decimal('8.49'), 'discount': Decimal('7.49'), 'rating': Decimal('4.7'), 'image_url': 'https://images.unsplash.com/photo-1553909489-ec2175ef3f52?w=400', 'description': 'Grilled chicken with teriyaki sauce', 'ingredients': 'Chicken, teriyaki sauce, lettuce, bread', 'grams': 280},
            
            # Starbucks
            {'name': 'Caffe Latte', 'company': 'Starbucks', 'category': 'Coffee', 'price': Decimal('4.99'), 'discount': Decimal('4.49'), 'rating': Decimal('4.8'), 'image_url': 'https://images.unsplash.com/photo-1561882468-9110e03e0f78?w=400', 'description': 'Espresso with steamed milk', 'ingredients': 'Espresso, milk', 'grams': 350},
            {'name': 'Cappuccino', 'company': 'Starbucks', 'category': 'Coffee', 'price': Decimal('4.49'), 'discount': Decimal('3.99'), 'rating': Decimal('4.7'), 'image_url': 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400', 'description': 'Espresso with foamed milk', 'ingredients': 'Espresso, milk, foam', 'grams': 300},
            {'name': 'Croissant', 'company': 'Starbucks', 'category': 'Desserts', 'price': Decimal('3.49'), 'discount': Decimal('2.99'), 'rating': Decimal('4.5'), 'image_url': 'https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400', 'description': 'Buttery flaky croissant', 'ingredients': 'Flour, butter, yeast', 'grams': 80},
            {'name': 'Caesar Salad', 'company': 'Starbucks', 'category': 'Salads', 'price': Decimal('7.99'), 'discount': Decimal('6.99'), 'rating': Decimal('4.4'), 'image_url': 'https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400', 'description': 'Fresh romaine lettuce with caesar dressing', 'ingredients': 'Lettuce, parmesan, croutons, caesar dressing', 'grams': 250},
            
            # Taco Bell
            {'name': 'Crunchy Taco', 'company': 'Taco Bell', 'category': 'Tacos', 'price': Decimal('1.99'), 'discount': Decimal('1.49'), 'rating': Decimal('4.4'), 'image_url': 'https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?w=400', 'description': 'Crispy taco with beef and cheese', 'ingredients': 'Beef, cheese, lettuce, taco shell', 'grams': 150},
            {'name': 'Burrito Supreme', 'company': 'Taco Bell', 'category': 'Tacos', 'price': Decimal('4.99'), 'discount': Decimal('4.29'), 'rating': Decimal('4.6'), 'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400', 'description': 'Flour tortilla filled with beef, beans, and cheese', 'ingredients': 'Beef, beans, cheese, sour cream, tortilla', 'grams': 300},
            {'name': 'Nachos Supreme', 'company': 'Taco Bell', 'category': 'Sides', 'price': Decimal('5.49'), 'discount': Decimal('4.79'), 'rating': Decimal('4.5'), 'image_url': 'https://images.unsplash.com/photo-1582169296194-e4d644c48063?w=400', 'description': 'Crispy nachos with cheese and toppings', 'ingredients': 'Chips, cheese, beef, sour cream, salsa', 'grams': 250},
            {'name': 'Mountain Dew', 'company': 'Taco Bell', 'category': 'Drinks', 'price': Decimal('1.99'), 'discount': Decimal('1.49'), 'rating': Decimal('4.2'), 'image_url': 'https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=400', 'description': 'Citrus flavored soda', 'ingredients': 'Carbonated water, sugar, citrus', 'grams': 500},
            
            # Burger King
            {'name': 'Whopper', 'company': 'Burger King', 'category': 'Burgers', 'price': Decimal('6.49'), 'discount': Decimal('5.49'), 'rating': Decimal('4.7'), 'image_url': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400', 'description': 'Flame-grilled beef burger with toppings', 'ingredients': 'Beef, lettuce, tomato, pickles, onions, mayo, bun', 'grams': 280},
            {'name': 'Chicken Nuggets', 'company': 'Burger King', 'category': 'Chicken', 'price': Decimal('4.99'), 'discount': Decimal('3.99'), 'rating': Decimal('4.4'), 'image_url': 'https://images.unsplash.com/photo-1562967914-608f82629710?w=400', 'description': 'Crispy chicken nuggets (10 pieces)', 'ingredients': 'Chicken, breading', 'grams': 200},
            {'name': 'Onion Rings', 'company': 'Burger King', 'category': 'Sides', 'price': Decimal('3.49'), 'discount': Decimal('2.99'), 'rating': Decimal('4.3'), 'image_url': 'https://images.unsplash.com/photo-1639024471283-03518883512d?w=400', 'description': 'Crispy fried onion rings', 'ingredients': 'Onions, batter, oil', 'grams': 150},
            
            # Domino's Pizza
            {'name': 'Margherita Pizza', 'company': "Domino's Pizza", 'category': 'Pizza', 'price': Decimal('11.99'), 'discount': Decimal('9.99'), 'rating': Decimal('4.6'), 'image_url': 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400', 'description': 'Classic pizza with fresh basil and mozzarella', 'ingredients': 'Dough, tomato, mozzarella, basil', 'grams': 750},
            {'name': 'BBQ Chicken Pizza', 'company': "Domino's Pizza", 'category': 'Pizza', 'price': Decimal('13.99'), 'discount': Decimal('11.99'), 'rating': Decimal('4.7'), 'image_url': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400', 'description': 'Pizza with BBQ sauce and grilled chicken', 'ingredients': 'Dough, BBQ sauce, chicken, cheese, onions', 'grams': 850},
            {'name': 'Chocolate Lava Cake', 'company': "Domino's Pizza", 'category': 'Desserts', 'price': Decimal('5.99'), 'discount': Decimal('4.99'), 'rating': Decimal('4.8'), 'image_url': 'https://images.unsplash.com/photo-1624353365286-3f8d62daad51?w=400', 'description': 'Warm chocolate cake with molten center', 'ingredients': 'Chocolate, flour, butter, sugar', 'grams': 120},
            {'name': 'Pepsi', 'company': "Domino's Pizza", 'category': 'Drinks', 'price': Decimal('1.99'), 'discount': Decimal('1.49'), 'rating': Decimal('4.1'), 'image_url': 'https://images.unsplash.com/photo-1629203849142-8c9c26b8f5d8?w=400', 'description': 'Refreshing cola beverage', 'ingredients': 'Carbonated water, sugar, caffeine', 'grams': 500},
        ]

        for prod_data in products_data:
            company = companies.get(prod_data['company'])
            category = categories.get(prod_data['category'])
            
            if not company or not category:
                self.stdout.write(self.style.WARNING(f'Skipping {prod_data["name"]} - missing company or category'))
                continue

            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                company=company,
                defaults={
                    'category': category,
                    'original_price': prod_data['price'],
                    'discounted_price': prod_data['discount'],
                    'rating': prod_data['rating'],
                    'description': prod_data['description'],
                    'ingredients': prod_data['ingredients'],
                    'grams': prod_data['grams'],
                }
            )
            
            # Always download and update image
            if product.image:
                product.image.delete(save=False)
            
            image_file = self.download_image(prod_data['image_url'], f"{prod_data['name'].lower().replace(' ', '_')}.jpg")
            if image_file:
                product.image = image_file
                product.save()
                self.stdout.write(self.style.SUCCESS(f'Created/Updated product: {product.name}'))

        self.stdout.write(self.style.SUCCESS('Database population completed!'))
