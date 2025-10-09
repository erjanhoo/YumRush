import os
import django
import sys
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random

# Настройка Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from user.models import MyUser
from product.models import Category, Product, Company
from order.models import Order, OrderItem, Cart, CartItem, Delivery

class DatabaseSeeder:
    def __init__(self):
        self.companies = []
        self.categories = []
        self.products = []
        self.users = []
        self.couriers = []

    def create_companies(self):
        """Создание компаний"""
        company_data = [
            {"name": "КFC", "description": "Сеть ресторанов быстрого питания"},
            {"name": "McDonald's", "description": "Международная сеть ресторанов быстрого питания"},
            {"name": "Burger King", "description": "Американская сеть ресторанов быстрого питания"},
            {"name": "Pizza Hut", "description": "Международная сеть пиццерий"},
            {"name": "Domino's", "description": "Американская компания по доставке пиццы"},
            {"name": "Subway", "description": "Сеть ресторанов быстрого питания"},
            {"name": "Starbucks", "description": "Международная сеть кофеен"},
            {"name": "Дядя Дёнер", "description": "Сеть кебабов и шаурмы"},
            {"name": "Теремок", "description": "Российская сеть блинных"},
            {"name": "Крошка Картошка", "description": "Сеть быстрого питания с печёной картошкой"}
        ]

        for data in company_data:
            company, created = Company.objects.get_or_create(
                name=data["name"],
                defaults={"description": data["description"]}
            )
            if created:
                self.companies.append(company)
                print(f"✓ Создана компания: {company.name}")

    def create_categories(self):
        """Создание категорий"""
        category_data = [
            {"name": "Бургеры", "description": "Классические и авторские бургеры"},
            {"name": "Пицца", "description": "Пиццы различных размеров и начинок"},
            {"name": "Напитки", "description": "Безалкогольные напитки, соки, кофе"},
            {"name": "Закуски", "description": "Картофель фри, наггетсы, салаты"},
            {"name": "Десерты", "description": "Мороженое, торты, печенье"},
            {"name": "Завтраки", "description": "Завтраки и утренние блюда"},
            {"name": "Супы", "description": "Горячие и холодные супы"},
            {"name": "Салаты", "description": "Свежие и теплые салаты"},
            {"name": "Шаурма", "description": "Шаурма, дёнер, кебабы"},
            {"name": "Роллы", "description": "Суши и роллы"}
        ]

        for data in category_data:
            category, created = Category.objects.get_or_create(
                name=data["name"],
                defaults={"description": data["description"]}
            )
            if created:
                self.categories.append(category)
                print(f"✓ Создана категория: {category.name}")

    def create_products(self):
        """Создание продуктов"""
        products_data = {
            "Бургеры": [
                {"name": "Биг Мак", "price": 299, "description": "Классический бургер с двойной котлетой"},
                {"name": "Чизбургер", "price": 129, "description": "Бургер с сыром и говяжьей котлетой"},
                {"name": "Роял Чизбургер", "price": 179, "description": "Большой чизбургер с беконом"},
                {"name": "Фиш Бургер", "price": 159, "description": "Бургер с рыбной котлетой"},
                {"name": "Чикен Бургер", "price": 189, "description": "Бургер с куриной котлетой"},
            ],
            "Пицца": [
                {"name": "Маргарита", "price": 599, "description": "Классическая пицца с томатами и моцареллой"},
                {"name": "Пепперони", "price": 699, "description": "Пицца с острой салями пепперони"},
                {"name": "Четыре сыра", "price": 799, "description": "Пицца с четырьмя видами сыра"},
                {"name": "Мясная", "price": 899, "description": "Пицца с говядиной, свининой и курицей"},
                {"name": "Гавайская", "price": 749, "description": "Пицца с ветчиной и ананасами"},
            ],
            "Напитки": [
                {"name": "Кока-Кола", "price": 89, "description": "Классическая газированная кола 0.5л"},
                {"name": "Фанта", "price": 89, "description": "Апельсиновая газировка 0.5л"},
                {"name": "Спрайт", "price": 89, "description": "Лимонно-лаймовая газировка 0.5л"},
                {"name": "Капучино", "price": 159, "description": "Кофе с молочной пенкой"},
                {"name": "Американо", "price": 119, "description": "Классический черный кофе"},
                {"name": "Сок яблочный", "price": 99, "description": "100% натуральный яблочный сок"},
            ],
            "Закуски": [
                {"name": "Картофель фри", "price": 129, "description": "Хрустящий картофель фри"},
                {"name": "Наггетсы", "price": 199, "description": "Куриные наггетсы 6 шт"},
                {"name": "Луковые кольца", "price": 149, "description": "Хрустящие луковые кольца"},
                {"name": "Сырные палочки", "price": 179, "description": "Моцарелла в панировке"},
            ],
            "Шаурма": [
                {"name": "Шаурма классическая", "price": 259, "description": "С курицей, овощами и соусом"},
                {"name": "Шаурма XL", "price": 349, "description": "Большая порция с двойным мясом"},
                {"name": "Дёнер", "price": 289, "description": "Турецкий дёнер с говядиной"},
                {"name": "Фалафель", "price": 229, "description": "Вегетарианская шаурма с фалафелем"},
            ]
        }

        for category_name, products in products_data.items():
            try:
                category = Category.objects.get(name=category_name)
                company = random.choice(self.companies) if self.companies else Company.objects.first()

                for product_data in products:
                    product, created = Product.objects.get_or_create(
                        name=product_data["name"],
                        defaults={
                            "original_price": Decimal(str(product_data["price"])),
                            "description": product_data["description"],
                            "category": category,
                            "company": company
                        }
                    )
                    if created:
                        self.products.append(product)
                        print(f"✓ Создан продукт: {product.name} - {product_data['price']}₽")
            except Category.DoesNotExist:
                print(f"⚠ Категория {category_name} не найдена")

    def create_users(self):
        """Создание пользователей"""
        users_data = [
            {"username": "user1", "email": "user1@test.com", "role": "user"},
            {"username": "user2", "email": "user2@test.com", "role": "user"},
            {"username": "user3", "email": "user3@test.com", "role": "user"},
            {"username": "courier1", "email": "courier1@test.com", "role": "courier"},
            {"username": "courier2", "email": "courier2@test.com", "role": "courier"},
            {"username": "admin", "email": "admin@test.com", "role": "admin"},
        ]

        for user_data in users_data:
            user, created = MyUser.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "role": user_data["role"],
                    "balance": Decimal(str(random.randint(500, 5000))),
                    "phone_number": f"+7900{random.randint(1000000, 9999999)}",
                }
            )
            if created:
                user.set_password("password123")
                user.save()

                if user.role == "courier":
                    self.couriers.append(user)
                else:
                    self.users.append(user)

                print(f"✓ Создан пользователь: {user.username} ({user.role}) - баланс: {user.balance}₽")

    def create_orders(self):
        """Создание заказов"""
        if not self.users or not self.products:
            print("⚠ Нет пользователей или продуктов для создания заказов")
            return

        statuses = ['new', 'assigned', 'in_progress', 'delivered']

        for i in range(15):  # Создаем 15 заказов
            user = random.choice(self.users)
            status = random.choice(statuses)

            # Создаем заказ
            order = Order.objects.create(
                user=user,
                status=status,
                total_price=Decimal('0'),
                created_at=timezone.now() - timedelta(days=random.randint(0, 30))
            )

            # Назначаем курьера если заказ не новый
            if status != 'new' and self.couriers:
                order.assigned_courier = random.choice(self.couriers)

            # Добавляем рейтинг для доставленных заказов
            if status == 'delivered':
                order.rating = random.randint(3, 5)

            # Добавляем товары в заказ
            total_price = Decimal('0')
            num_items = random.randint(1, 4)
            selected_products = random.sample(self.products, min(num_items, len(self.products)))

            for product in selected_products:
                quantity = random.randint(1, 3)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
                total_price += product.price * quantity

            order.total_price = total_price
            order.save()

            # Создаем информацию о доставке
            Delivery.objects.create(
                order=order,
                delivery_type=random.choice(['pickup', 'delivery']),
                receiver_name=user.username,  # changed from first_name + last_name to username
                receiver_phone_number=user.phone_number,
                delivery_address=f"ул. Тестовая, д. {random.randint(1, 100)}",
                description="Тестовый заказ",
                is_free_delivery=total_price > 1000
            )

            print(f"✓ Создан заказ #{order.id} для {user.username} на сумму {total_price}₽ (статус: {status})")

    def create_carts(self):
        """Создание корзин с товарами"""
        for user in self.users:
            # Создаем активную корзину для некоторых пользователей
            if random.choice([True, False]):
                cart, created = Cart.objects.get_or_create(
                    user=user,
                    is_active=True
                )

                if created:
                    # Добавляем товары в корзину
                    num_items = random.randint(1, 3)
                    selected_products = random.sample(self.products, min(num_items, len(self.products)))

                    for product in selected_products:
                        CartItem.objects.create(
                            cart=cart,
                            product=product,
                            quantity=random.randint(1, 2)
                        )

                    total_items = cart.items.count()
                    print(f"✓ Создана корзина для {user.username} с {total_items} товарами")

    def run_seeder(self):
        """Запуск всех сидеров"""
        print("🚀 Начинаем заполнение базы данных...")

        try:
            print("\n📦 Создание компаний...")
            self.create_companies()

            print("\n🏷 Создание категорий...")
            self.create_categories()

            print("\n🍔 Создание продуктов...")
            self.create_products()

            print("\n👥 Создание пользователей...")
            self.create_users()

            print("\n📋 Создание заказов...")
            self.create_orders()

            print("\n🛒 Создание корзин...")
            self.create_carts()

            print("\n✅ Заполнение базы данных завершено успешно!")
            print(f"📊 Статистика:")
            print(f"   - Компаний: {Company.objects.count()}")
            print(f"   - Категорий: {Category.objects.count()}")
            print(f"   - Продуктов: {Product.objects.count()}")
            print(f"   - Пользователей: {MyUser.objects.count()}")
            print(f"   - Заказов: {Order.objects.count()}")
            print(f"   - Активных корзин: {Cart.objects.filter(is_active=True).count()}")

        except Exception as e:
            print(f"❌ Ошибка при заполнении БД: {str(e)}")

if __name__ == "__main__":
    seeder = DatabaseSeeder()
    seeder.run_seeder()