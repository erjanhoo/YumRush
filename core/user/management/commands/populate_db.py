from django.core.management.base import BaseCommand
from user.models import MyUser
from product.models import Company, Category, Product
from decimal import Decimal
from django.core.files.base import ContentFile
import requests


class Command(BaseCommand):
    help = 'Populate database with sample data'

    def download_image(self, url):
        """Download image from URL and return ContentFile"""
        try:
            self.stdout.write(f'Downloading image from: {url}')
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f'✓ Downloaded successfully'))
                return ContentFile(response.content)
            else:
                self.stdout.write(self.style.ERROR(f'✗ Failed with status {response.status_code}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error downloading: {str(e)}'))
        return None

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database population...')

        # Create Companies
        companies_data = [
            {
                "name": "McDonald's",
                "phone_number": "+1234567890",
                "description": "Fast food chain",
                "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/McDonald%27s_Golden_Arches.svg/200px-McDonald%27s_Golden_Arches.svg.png"
            },
            {
                "name": "KFC",
                "phone_number": "+1234567891",
                "description": "Fried chicken specialists",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/b/bf/KFC_logo.svg/200px-KFC_logo.svg.png"
            },
            {
                "name": "Pizza Hut",
                "phone_number": "+1234567892",
                "description": "Pizza restaurant",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d2/Pizza_Hut_logo.svg/200px-Pizza_Hut_logo.svg.png"
            },
        ]

        companies = {}
        for data in companies_data:
            logo_url = data.pop('logo_url', None)
            company, created = Company.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created and logo_url:
                logo_content = self.download_image(logo_url)
                if logo_content:
                    company.logo.save(f"{data['name'].lower().replace(' ', '_')}_logo.png", logo_content, save=True)
            companies[data['name']] = company
            if created:
                self.stdout.write(f'Created company: {company.name}')

        # Create Categories
        categories_data = [
            {"name": "Burgers", "description": "Delicious burgers"},
            {"name": "Pizza", "description": "Fresh pizzas"},
            {"name": "Chicken", "description": "Crispy chicken"},
            {"name": "Drinks", "description": "Refreshing drinks"},
            {"name": "Desserts", "description": "Sweet treats"},
        ]

        categories = {}
        for data in categories_data:
            category, created = Category.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            categories[data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create Products
        products_data = [
            # McDonald's
            {
                "name": "Big Mac",
                "company": "McDonald's",
                "category": "Burgers",
                "original_price": Decimal("5.99"),
                "discounted_price": Decimal("4.99"),
                "description": "Two all-beef patties, special sauce, lettuce, cheese",
                "ingredients": "Beef, lettuce, cheese, pickles, onions, sauce, sesame bun",
                "grams": 215,
                "image_url": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=400"
            },
            {
                "name": "McChicken",
                "company": "McDonald's",
                "category": "Chicken",
                "original_price": Decimal("4.99"),
                "discounted_price": Decimal("3.99"),
                "description": "Crispy chicken sandwich",
                "ingredients": "Chicken, lettuce, mayo, bun",
                "grams": 185,
                "image_url": "https://images.unsplash.com/photo-1513639776629-7b61b0ac49cb?w=400"
            },
            {
                "name": "French Fries",
                "company": "McDonald's",
                "category": "Burgers",
                "original_price": Decimal("2.99"),
                "discounted_price": Decimal("2.49"),
                "description": "Golden crispy fries",
                "ingredients": "Potatoes, salt, oil",
                "grams": 150,
                "image_url": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400"
            },
            # KFC
            {
                "name": "Original Recipe Chicken",
                "company": "KFC",
                "category": "Chicken",
                "original_price": Decimal("8.99"),
                "discounted_price": Decimal("7.99"),
                "description": "Colonel's original recipe fried chicken",
                "ingredients": "Chicken, 11 herbs and spices",
                "grams": 300,
                "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400"
            },
            {
                "name": "Zinger Burger",
                "company": "KFC",
                "category": "Burgers",
                "original_price": Decimal("6.99"),
                "discounted_price": Decimal("5.99"),
                "description": "Spicy crispy chicken burger",
                "ingredients": "Chicken, lettuce, mayo, bun",
                "grams": 220,
                "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400"
            },
            # Pizza Hut
            {
                "name": "Pepperoni Pizza",
                "company": "Pizza Hut",
                "category": "Pizza",
                "original_price": Decimal("12.99"),
                "discounted_price": Decimal("10.99"),
                "description": "Classic pepperoni pizza",
                "ingredients": "Dough, tomato sauce, mozzarella, pepperoni",
                "grams": 450,
                "image_url": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400"
            },
            {
                "name": "Margherita Pizza",
                "company": "Pizza Hut",
                "category": "Pizza",
                "original_price": Decimal("10.99"),
                "discounted_price": Decimal("9.99"),
                "description": "Classic cheese pizza",
                "ingredients": "Dough, tomato sauce, mozzarella, basil",
                "grams": 400,
                "image_url": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400"
            },
            # Drinks
            {
                "name": "Coca Cola",
                "company": "McDonald's",
                "category": "Drinks",
                "original_price": Decimal("1.99"),
                "discounted_price": Decimal("1.49"),
                "description": "Refreshing cola drink",
                "ingredients": "Carbonated water, sugar, caffeine",
                "grams": 500,
                "image_url": "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400"
            },
            {
                "name": "Pepsi",
                "company": "KFC",
                "category": "Drinks",
                "original_price": Decimal("1.99"),
                "discounted_price": Decimal("1.49"),
                "description": "Refreshing cola drink",
                "ingredients": "Carbonated water, sugar, caffeine",
                "grams": 500,
                "image_url": "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=400"
            },
        ]

        for data in products_data:
            company = companies[data.pop('company')]
            category = categories[data.pop('category')]
            image_url = data.pop('image_url', None)
            
            product, created = Product.objects.get_or_create(
                name=data['name'],
                company=company,
                defaults={
                    **data,
                    'category': category,
                    'is_available': True
                }
            )
            if created:
                if image_url:
                    image_content = self.download_image(image_url)
                    if image_content:
                        product.image.save(f"{data['name'].lower().replace(' ', '_')}.jpg", image_content, save=True)
                self.stdout.write(f'Created product: {product.name} ({company.name})')

        # Create manager accounts for each company
        for company_name, company in companies.items():
            username = company_name.lower().replace("'", "").replace(" ", "_")
            manager, created = MyUser.objects.get_or_create(
                email=f"{username}@example.com",
                defaults={
                    'username': f"{username}_manager",
                    'role': 'manager',
                    'company': company
                }
            )
            if created:
                manager.set_password('manager123')
                manager.save()
                self.stdout.write(f'Created manager: {manager.email} (password: manager123)')

        # Create a regular user
        user, created = MyUser.objects.get_or_create(
            email='user@example.com',
            defaults={
                'username': 'testuser',
                'role': 'user',
                'balance': Decimal('100.00')
            }
        )
        if created:
            user.set_password('user123')
            user.save()
            self.stdout.write('Created test user: user@example.com (password: user123)')

        # Create a courier
        courier, created = MyUser.objects.get_or_create(
            email='courier@example.com',
            defaults={
                'username': 'testcourier',
                'role': 'courier',
                'phone_number': '+1234567890'
            }
        )
        if created:
            courier.set_password('courier123')
            courier.save()
            self.stdout.write('Created test courier: courier@example.com (password: courier123)')

        self.stdout.write(self.style.SUCCESS('\n✅ Database population completed!'))
        self.stdout.write('\nTest Accounts Created:')
        self.stdout.write('- User: user@example.com / user123')
        self.stdout.write('- Courier: courier@example.com / courier123')
        self.stdout.write('- Manager (McDonald\'s): mcdonalds@example.com / manager123')
        self.stdout.write('- Manager (KFC): kfc@example.com / manager123')
        self.stdout.write('- Manager (Pizza Hut): pizza_hut@example.com / manager123')
