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
                "logo_url": "https://images.unsplash.com/photo-1619454016518-697bc231e7cb?w=200"
            },
            {
                "name": "KFC",
                "phone_number": "+1234567891",
                "description": "Fried chicken specialists",
                "logo_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=200"
            },
            {
                "name": "Pizza Hut",
                "phone_number": "+1234567892",
                "description": "Pizza restaurant",
                "logo_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=200"
            },
            {
                "name": "Subway",
                "phone_number": "+1234567893",
                "description": "Fresh sandwiches and salads",
                "logo_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=200"
            },
            {
                "name": "Starbucks",
                "phone_number": "+1234567894",
                "description": "Coffee and pastries",
                "logo_url": "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=200"
            },
            {
                "name": "Taco Bell",
                "phone_number": "+1234567895",
                "description": "Mexican-inspired fast food",
                "logo_url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=200"
            },
            {
                "name": "Burger King",
                "phone_number": "+1234567896",
                "description": "Flame-grilled burgers",
                "logo_url": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=200"
            },
            {
                "name": "Domino's Pizza",
                "phone_number": "+1234567897",
                "description": "Pizza delivery experts",
                "logo_url": "https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=200"
            },
        ]

        companies = {}
        for data in companies_data:
            logo_url = data.pop('logo_url', None)
            company, created = Company.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            
            # Force re-download logos
            if logo_url:
                if company.logo:
                    company.logo.delete(save=False)
                logo_content = self.download_image(logo_url)
                if logo_content:
                    company.logo.save(f"{data['name'].lower().replace(' ', '_')}_logo.jpg", logo_content, save=True)
                    self.stdout.write(f'Added logo to: {company.name}')
            
            companies[data['name']] = company
            if created:
                self.stdout.write(f'Created company: {company.name}')
            else:
                self.stdout.write(f'Company exists: {company.name}')

        # Create Categories
        categories_data = [
            {
                "name": "Burgers",
                "description": "Delicious burgers",
                "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400"
            },
            {
                "name": "Pizza",
                "description": "Fresh pizzas",
                "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400"
            },
            {
                "name": "Chicken",
                "description": "Crispy chicken",
                "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400"
            },
            {
                "name": "Drinks",
                "description": "Refreshing drinks",
                "image_url": "https://images.unsplash.com/photo-1437418747212-8d9709afab22?w=400"
            },
            {
                "name": "Desserts",
                "description": "Sweet treats",
                "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400"
            },
            {
                "name": "Sandwiches",
                "description": "Fresh sandwiches",
                "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400"
            },
            {
                "name": "Tacos",
                "description": "Mexican tacos",
                "image_url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400"
            },
            {
                "name": "Coffee",
                "description": "Hot and cold coffee",
                "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400"
            },
            {
                "name": "Salads",
                "description": "Healthy salads",
                "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400"
            },
            {
                "name": "Sides",
                "description": "Side dishes",
                "image_url": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400"
            },
        ]

        categories = {}
        for data in categories_data:
            image_url = data.pop('image_url', None)
            category, created = Category.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            
            # Force re-download images
            if image_url:
                if category.image:
                    category.image.delete(save=False)
                image_content = self.download_image(image_url)
                if image_content:
                    category.image.save(f"{data['name'].lower()}.jpg", image_content, save=True)
                    self.stdout.write(f'Added image to category: {category.name}')
            
            categories[data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category exists: {category.name}')

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
            # Subway
            {
                "name": "Italian BMT",
                "company": "Subway",
                "category": "Sandwiches",
                "original_price": Decimal("7.99"),
                "discounted_price": Decimal("6.99"),
                "description": "Classic Italian sub with meats and cheese",
                "ingredients": "Salami, pepperoni, ham, lettuce, tomatoes, onions, bread",
                "grams": 280,
                "image_url": "https://images.unsplash.com/photo-1553909489-cd47e0907980?w=400"
            },
            {
                "name": "Veggie Delite",
                "company": "Subway",
                "category": "Sandwiches",
                "original_price": Decimal("5.99"),
                "discounted_price": Decimal("4.99"),
                "description": "Fresh vegetable sandwich",
                "ingredients": "Lettuce, tomatoes, cucumbers, peppers, onions, bread",
                "grams": 230,
                "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400"
            },
            {
                "name": "Chicken Teriyaki",
                "company": "Subway",
                "category": "Sandwiches",
                "original_price": Decimal("8.49"),
                "discounted_price": Decimal("7.49"),
                "description": "Grilled chicken with teriyaki glaze",
                "ingredients": "Chicken, teriyaki sauce, lettuce, tomatoes, bread",
                "grams": 265,
                "image_url": "https://images.unsplash.com/photo-1551782450-17144efb9c50?w=400"
            },
            # Starbucks
            {
                "name": "Caffe Latte",
                "company": "Starbucks",
                "category": "Coffee",
                "original_price": Decimal("4.99"),
                "discounted_price": Decimal("4.49"),
                "description": "Smooth espresso with steamed milk",
                "ingredients": "Espresso, milk, foam",
                "grams": 350,
                "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400"
            },
            {
                "name": "Cappuccino",
                "company": "Starbucks",
                "category": "Coffee",
                "original_price": Decimal("4.49"),
                "discounted_price": Decimal("3.99"),
                "description": "Rich espresso with foamed milk",
                "ingredients": "Espresso, milk, foam",
                "grams": 300,
                "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400"
            },
            {
                "name": "Chocolate Croissant",
                "company": "Starbucks",
                "category": "Desserts",
                "original_price": Decimal("3.99"),
                "discounted_price": Decimal("3.49"),
                "description": "Buttery croissant with chocolate filling",
                "ingredients": "Flour, butter, chocolate, sugar",
                "grams": 120,
                "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400"
            },
            {
                "name": "Blueberry Muffin",
                "company": "Starbucks",
                "category": "Desserts",
                "original_price": Decimal("3.49"),
                "discounted_price": Decimal("2.99"),
                "description": "Fresh baked muffin with blueberries",
                "ingredients": "Flour, blueberries, sugar, eggs, butter",
                "grams": 140,
                "image_url": "https://images.unsplash.com/photo-1607958996333-41aef7caefaa?w=400"
            },
            # Taco Bell
            {
                "name": "Crunchy Taco",
                "company": "Taco Bell",
                "category": "Tacos",
                "original_price": Decimal("1.99"),
                "discounted_price": Decimal("1.49"),
                "description": "Crispy taco with seasoned beef",
                "ingredients": "Beef, lettuce, cheese, taco shell",
                "grams": 85,
                "image_url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400"
            },
            {
                "name": "Burrito Supreme",
                "company": "Taco Bell",
                "category": "Tacos",
                "original_price": Decimal("4.99"),
                "discounted_price": Decimal("4.49"),
                "description": "Large burrito with beef and beans",
                "ingredients": "Beef, beans, cheese, sour cream, tortilla",
                "grams": 248,
                "image_url": "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400"
            },
            {
                "name": "Quesadilla",
                "company": "Taco Bell",
                "category": "Tacos",
                "original_price": Decimal("5.49"),
                "discounted_price": Decimal("4.99"),
                "description": "Grilled tortilla with melted cheese",
                "ingredients": "Chicken, cheese, tortilla, sauce",
                "grams": 190,
                "image_url": "https://images.unsplash.com/photo-1618040996337-56904b7850b9?w=400"
            },
            # Burger King
            {
                "name": "Whopper",
                "company": "Burger King",
                "category": "Burgers",
                "original_price": Decimal("6.49"),
                "discounted_price": Decimal("5.49"),
                "description": "Flame-grilled burger with fresh toppings",
                "ingredients": "Beef, lettuce, tomato, pickles, onions, ketchup, mayo, bun",
                "grams": 290,
                "image_url": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=400"
            },
            {
                "name": "Chicken Nuggets",
                "company": "Burger King",
                "category": "Chicken",
                "original_price": Decimal("5.99"),
                "discounted_price": Decimal("4.99"),
                "description": "Crispy chicken nuggets",
                "ingredients": "Chicken, breading, oil",
                "grams": 200,
                "image_url": "https://images.unsplash.com/photo-1562967914-608f82629710?w=400"
            },
            {
                "name": "Onion Rings",
                "company": "Burger King",
                "category": "Sides",
                "original_price": Decimal("3.49"),
                "discounted_price": Decimal("2.99"),
                "description": "Crispy fried onion rings",
                "ingredients": "Onions, batter, oil",
                "grams": 140,
                "image_url": "https://images.unsplash.com/photo-1639024471283-03518883512d?w=400"
            },
            # Domino's Pizza
            {
                "name": "Hawaiian Pizza",
                "company": "Domino's Pizza",
                "category": "Pizza",
                "original_price": Decimal("13.99"),
                "discounted_price": Decimal("11.99"),
                "description": "Pizza with ham and pineapple",
                "ingredients": "Dough, tomato sauce, mozzarella, ham, pineapple",
                "grams": 460,
                "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400"
            },
            {
                "name": "BBQ Chicken Pizza",
                "company": "Domino's Pizza",
                "category": "Pizza",
                "original_price": Decimal("14.99"),
                "discounted_price": Decimal("12.99"),
                "description": "Pizza with BBQ sauce and chicken",
                "ingredients": "Dough, BBQ sauce, mozzarella, chicken, onions",
                "grams": 480,
                "image_url": "https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=400"
            },
            {
                "name": "Garlic Bread",
                "company": "Domino's Pizza",
                "category": "Sides",
                "original_price": Decimal("4.99"),
                "discounted_price": Decimal("3.99"),
                "description": "Warm garlic bread with butter",
                "ingredients": "Bread, garlic, butter, herbs",
                "grams": 180,
                "image_url": "https://images.unsplash.com/photo-1573140401552-3fab0b24306f?w=400"
            },
            # More items
            {
                "name": "Caesar Salad",
                "company": "Subway",
                "category": "Salads",
                "original_price": Decimal("6.99"),
                "discounted_price": Decimal("5.99"),
                "description": "Fresh romaine with caesar dressing",
                "ingredients": "Romaine lettuce, parmesan, croutons, caesar dressing",
                "grams": 220,
                "image_url": "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400"
            },
            {
                "name": "Ice Cream Sundae",
                "company": "McDonald's",
                "category": "Desserts",
                "original_price": Decimal("2.99"),
                "discounted_price": Decimal("2.49"),
                "description": "Vanilla ice cream with topping",
                "ingredients": "Ice cream, chocolate sauce, whipped cream",
                "grams": 180,
                "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400"
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
            
            # Force re-download images by clearing and re-saving
            if image_url:
                if product.image:
                    product.image.delete(save=False)  # Delete old file
                image_content = self.download_image(image_url)
                if image_content:
                    product.image.save(f"{data['name'].lower().replace(' ', '_')}.jpg", image_content, save=True)
                    self.stdout.write(f'Added image to: {product.name}')
            
            if created:
                self.stdout.write(f'Created product: {product.name} ({company.name})')
            else:
                self.stdout.write(f'Product exists: {product.name} ({company.name})')

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
