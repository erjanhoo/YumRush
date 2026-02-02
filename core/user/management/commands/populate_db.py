from django.core.management.base import BaseCommand
from user.models import MyUser
from product.models import Company, Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database population...')

        # Create Companies
        companies_data = [
            {"name": "McDonald's", "phone_number": "+1234567890", "description": "Fast food chain"},
            {"name": "KFC", "phone_number": "+1234567891", "description": "Fried chicken specialists"},
            {"name": "Pizza Hut", "phone_number": "+1234567892", "description": "Pizza restaurant"},
        ]

        companies = {}
        for data in companies_data:
            company, created = Company.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
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
                "grams": 215
            },
            {
                "name": "McChicken",
                "company": "McDonald's",
                "category": "Chicken",
                "original_price": Decimal("4.99"),
                "discounted_price": Decimal("3.99"),
                "description": "Crispy chicken sandwich",
                "ingredients": "Chicken, lettuce, mayo, bun",
                "grams": 185
            },
            {
                "name": "French Fries",
                "company": "McDonald's",
                "category": "Burgers",
                "original_price": Decimal("2.99"),
                "discounted_price": Decimal("2.49"),
                "description": "Golden crispy fries",
                "ingredients": "Potatoes, salt, oil",
                "grams": 150
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
                "grams": 300
            },
            {
                "name": "Zinger Burger",
                "company": "KFC",
                "category": "Burgers",
                "original_price": Decimal("6.99"),
                "discounted_price": Decimal("5.99"),
                "description": "Spicy crispy chicken burger",
                "ingredients": "Chicken, lettuce, mayo, bun",
                "grams": 220
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
                "grams": 450
            },
            {
                "name": "Margherita Pizza",
                "company": "Pizza Hut",
                "category": "Pizza",
                "original_price": Decimal("10.99"),
                "discounted_price": Decimal("9.99"),
                "description": "Classic cheese pizza",
                "ingredients": "Dough, tomato sauce, mozzarella, basil",
                "grams": 400
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
                "grams": 500
            },
            {
                "name": "Pepsi",
                "company": "KFC",
                "category": "Drinks",
                "original_price": Decimal("1.99"),
                "discounted_price": Decimal("1.49"),
                "description": "Refreshing cola drink",
                "ingredients": "Carbonated water, sugar, caffeine",
                "grams": 500
            },
        ]

        for data in products_data:
            company = companies[data.pop('company')]
            category = categories[data.pop('category')]
            
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
