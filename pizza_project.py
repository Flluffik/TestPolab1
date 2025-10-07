import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from abc import ABC, ABCMeta, abstractmethod
import threading
import asyncio

# Настройка базы данных SQLite с использованием SQLAlchemy
Base = declarative_base()

class PizzaModel(Base):
    __tablename__ = 'pizzas'
    id = Column(Integer, primary_key=True)
    dough = Column(String)
    sauce = Column(String)
    toppings = Column(String)
    price = Column(Float)

engine = create_engine('sqlite:///pizzas.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Комбинированный метакласс для автоматической регистрации пицц и поддержки абстрактных классов
class CombinedMeta(ABCMeta, type):
    pass

# Абстрактный класс для пиццы
class PizzaBase(ABC, metaclass=CombinedMeta):
    def __init__(self, dough="обычное тесто", sauce="томатный", toppings=None, price=0):
        if toppings is None:
            toppings = []
        self._dough = dough
        self._sauce = sauce
        self._toppings = toppings
        self._price = price

    @abstractmethod
    def prepare(self):
        pass

    @abstractmethod
    def bake(self):
        pass

    @abstractmethod
    def cut(self):
        pass

    @abstractmethod
    def box(self):
        pass

# Классы исключений
class PizzaError(Exception):
    pass

class InvalidPizzaError(PizzaError):
    def __init__(self, message="Неверный выбор пиццы"):
        self.message = message
        super().__init__(self.message)

# Класс-миксин для управления скидками
class DiscountMixin:
    discount_code = None

    def apply_discount(self, code):
        if code == "itmo":
            self.discount_code = code
        else:
            raise PizzaError("Такого промокода не существует")
        return True

    def get_discounted_price(self, price):
        if self.discount_code == "itmo":
            return price * 0.9  # Скидка 10%
        return price

# Декораторы для логирования и проверки предусловий/постусловий
def log_call(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

def ensure_positive_price(func):
    def wrapper(self, *args, **kwargs):
        if self.price < 0:
            raise ValueError("Цена не может быть отрицательной")
        return func(self, *args, **kwargs)
    return wrapper

class Pizza(PizzaBase, DiscountMixin):
    def __init__(self, dough="обычное тесто", sauce="томатный", toppings=None, price=0):
        super().__init__(dough, sauce, toppings, price)
        self.save_to_db()

    def save_to_db(self):
        pizza = PizzaModel(dough=self.dough, sauce=self.sauce, toppings=', '.join(self.toppings), price=self.price)
        session.add(pizza)
        session.commit()

    @property
    def dough(self):
        return self._dough

    @dough.setter
    def dough(self, value):
        self._dough = value

    @property
    def sauce(self):
        return self._sauce

    @sauce.setter
    def sauce(self, value):
        self._sauce = value

    @property
    def toppings(self):
        return self._toppings

    @toppings.setter
    def toppings(self, value):
        self._toppings = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value < 0:
            raise ValueError("Цена не может быть отрицательной")
        self._price = value

    @ensure_positive_price
    def prepare(self):
        return f"Подготовка пиццы с {self.dough}, {self.sauce} соусом и начинками: {', '.join(self.toppings)}"

    def bake(self):
        return "Выпечка пиццы..."

    def cut(self):
        return "Нарезка пиццы..."

    def box(self):
        return "Упаковка пиццы..."

    def __add__(self, other):
        if isinstance(other, Pizza):
            new_toppings = self.toppings + other.toppings
            return Pizza(self.dough, self.sauce, new_toppings, self.price)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Pizza):
            new_toppings = [topping for topping in self.toppings if topping not in other.toppings]
            return Pizza(self.dough, self.sauce, new_toppings, self.price)
        return NotImplemented

    def __str__(self):
        return f"{self.__class__.__name__} на {self.dough}, соус {self.sauce}, начинки: {', '.join(self.toppings)} - {self.price} руб."

class ПиццаПепперони(Pizza):
    def __init__(self, dough="тонком тесте"):
        super().__init__(dough=dough, sauce="томатный", toppings=["пепперони", "сыр"], price=590)

    def __str__(self):
        return f"Пицца Пепперони на {self.dough}, соус {self.sauce}, начинки: {', '.join(self.toppings)} - {self.price} руб."


class ПиццаБарбекю(Pizza):
    def __init__(self, dough="обычном тесте"):
        super().__init__(dough=dough, sauce="барбекю", toppings=["курица", "лук", "сыр"], price=690)

    def __str__(self):
        return f"Пицца Барбекю на {self.dough}, соус {self.sauce}, начинки: {', '.join(self.toppings)} - {self.price} руб."


class ПиццаДарыМоря(Pizza):
    def __init__(self, dough="толстом тесте"):
        super().__init__(dough=dough, sauce="белый", toppings=["креветки", "мидии", "сыр"], price=790)

    def __str__(self):
        return f"Пицца Дары Моря на {self.dough}, соус {self.sauce}, начинки: {', '.join(self.toppings)} - {self.price} руб."


class Order:
    def __init__(self):
        self.pizzas = []
        self.discount_code = None

    def add_pizza(self, pizza):
        self.pizzas.append(pizza)

    def remove_pizza(self, index):
        if 0 <= index < len(self.pizzas):
            removed_pizza = self.pizzas.pop(index)
            print(f"Пицца {removed_pizza} удалена из заказа.")
        else:
            raise InvalidPizzaError("Некорректный индекс пиццы.")

    def apply_discount(self, code):
        if not self.discount_code and code == "itmo":
            self.discount_code = code
            for pizza in self.pizzas:
                pizza.apply_discount(code)
            return True
        else:
            raise PizzaError("Такого промокода не существует")
        return False

    def total_price(self):
        total = sum(pizza.get_discounted_price(pizza.price) for pizza in self.pizzas)
        return total

    def summary(self):
        pizza_list = "\n".join([f"{i + 1}. {pizza}" for i, pizza in enumerate(self.pizzas)])
        return f"Сводка заказа:\n{pizza_list}\nОбщая стоимость: {self.total_price():.2f} руб."

    def prepare_order(self):
        steps = []
        for pizza in self.pizzas:
            steps.append(pizza.prepare())
            steps.append(pizza.bake())
            steps.append(pizza.cut())
            steps.append(pizza.box())
        return steps

    def async_prepare_order(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [self.async_prepare_pizza(pizza) for pizza in self.pizzas]
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()

    async def async_prepare_pizza(self, pizza):
        print(await self.async_operation(pizza.prepare))
        print(await self.async_operation(pizza.bake))
        print(await self.async_operation(pizza.cut))
        print(await self.async_operation(pizza.box))

    async def async_operation(self, func):
        await asyncio.sleep(1)
        return func()


class Terminal:
    def __init__(self):
        self.order = Order()

    def display_menu(self):
        print("1. Пицца Пепперони - 590 руб.")
        print("2. Пицца Барбекю - 690 руб.")
        print("3. Пицца Дары Моря - 790 руб.")
        print("4. Просмотреть заказ")
        print("5. Подтвердить заказ")
        print("6. Выход")

    def choose_dough(self):
        while True:
            print("Выберите тип теста:")
            print("1. Тонкое тесто")
            print("2. Обычное тесто")
            print("3. Толстое тесто")
            dough_choice = input("Введите номер выбора: ")
            dough_dict = {
                "1": "тонком тесте",
                "2": "обычном тесте",
                "3": "толстом тесте"
            }
            if dough_choice in dough_dict:
                return dough_dict[dough_choice]
            else:
                print("Неверный выбор, пожалуйста, попробуйте снова.")

    def edit_order(self):
        while True:
            print(self.order.summary())
            print("1. Удалить пиццу")
            print("2. Назад")
            choice = input("Выберите опцию: ")
            if choice == "1":
                index = int(input("Введите номер пиццы для удаления: ")) - 1
                try:
                    self.order.remove_pizza(index)
                except InvalidPizzaError as e:
                    print(e)
            elif choice == "2":
                break
            else:
                print("Неверный выбор, пожалуйста, попробуйте снова.")

    def confirm_order(self):
        while True:
            print(self.order.summary())
            while True:
                code = input("Введите промокод (или нажмите Enter для продолжения без промокода): ")
                if not code:
                    break
                try:
                    self.order.apply_discount(code)
                    print(f"Стоимость заказа после применения промокода: {self.order.total_price():.2f} руб.")
                    break
                except PizzaError as e:
                    print(e)
            choice = input("Хотите удалить какую-либо пиццу из заказа? (да/нет): ")
            if choice.lower() == "да":
                index = int(input("Введите номер пиццы для удаления: ")) - 1
                try:
                    self.order.remove_pizza(index)
                except InvalidPizzaError as e:
                    print(e)
            elif choice.lower() == "нет":
                break
            else:
                print("Неверный выбор, пожалуйста, попробуйте снова.")
        print("Заказ подтвержден. Подготовка ваших пицц...")
        self.order.async_prepare_order()
        print("Ваш заказ готов!")

    def take_order(self):
        while True:
            self.display_menu()
            choice = input("Выберите опцию: ")
            if choice == "1":
                dough = self.choose_dough()
                self.order.add_pizza(ПиццаПепперони(dough))
                print(f"Добавлена Пицца Пепперони на {dough} в заказ.")
            elif choice == "2":
                dough = self.choose_dough()
                self.order.add_pizza(ПиццаБарбекю(dough))
                print(f"Добавлена Пицца Барбекю на {dough} в заказ.")
            elif choice == "3":
                dough = self.choose_dough()
                self.order.add_pizza(ПиццаДарыМоря(dough))
                print(f"Добавлена Пицца Дары Моря на {dough} в заказ.")
            elif choice == "4":
                self.edit_order()
            elif choice == "5":
                self.confirm_order()
                break
            elif choice == "6":
                print("До свидания!")
                break
            else:
                print("Неверный выбор, пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    terminal = Terminal()
    terminal.take_order()
