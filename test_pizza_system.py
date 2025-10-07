import pytest
import asyncio
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pizza_project import Pizza, ПиццаПепперони, ПиццаБарбекю, ПиццаДарыМоря, Order, InvalidPizzaError, PizzaError


class TestPizzaCreation:

    def test_pepperoni_pizza_creation(self):
        dough = "тонком тесте"

        pizza = ПиццаПепперони(dough)

        assert pizza.dough == dough
        assert pizza.sauce == "томатный"
        assert "пепперони" in pizza.toppings
        assert "сыр" in pizza.toppings
        assert pizza.price == 590

    def test_barbecue_pizza_creation(self):
        dough = "обычном тесте"

        pizza = ПиццаБарбекю(dough)

        assert pizza.dough == dough
        assert pizza.sauce == "барбекю"
        assert "курица" in pizza.toppings
        assert "лук" in pizza.toppings
        assert "сыр" in pizza.toppings
        assert pizza.price == 690

    def test_seafood_pizza_creation(self):
        dough = "толстом тесте"

        pizza = ПиццаДарыМоря(dough)

        assert pizza.dough == dough
        assert pizza.sauce == "белый"
        assert "креветки" in pizza.toppings
        assert "мидии" in pizza.toppings
        assert "сыр" in pizza.toppings
        assert pizza.price == 790


class TestPizzaOperations:

    def test_pizza_addition(self):

        pizza1 = ПиццаПепперони()
        pizza2 = ПиццаБарбекю()

        result = pizza1 + pizza2

        assert len(result.toppings) == len(pizza1.toppings) + len(pizza2.toppings)
        assert "пепперони" in result.toppings
        assert "курица" in result.toppings

    def test_pizza_subtraction(self):
        pizza1 = ПиццаПепперони()
        pizza2 = Pizza(toppings=["сыр"])

        result = pizza1 - pizza2

        assert "сыр" not in result.toppings
        assert "пепперони" in result.toppings

    def test_negative_price_validation(self):
        pizza = ПиццаПепперони()

        with pytest.raises(ValueError, match="Цена не может быть отрицательной"):
            pizza.price = -100


class TestDiscountSystem:

    def test_valid_discount_application(self):
        pizza = ПиццаПепперони()

        result = pizza.apply_discount("itmo")

        assert result == True
        assert pizza.discount_code == "itmo"

    def test_invalid_discount_application(self):
        pizza = ПиццаПепперони()

        with pytest.raises(PizzaError, match="Такого промокода не существует"):
            pizza.apply_discount("invalid_code")

    def test_discounted_price_calculation(self):
        pizza = ПиццаПепперони()
        pizza.apply_discount("itmo")

        discounted_price = pizza.get_discounted_price(pizza.price)

        expected_price = 590 * 0.9  # 10% скидка
        assert discounted_price == expected_price


class TestOrderManagement:

    def setUp(self):
        self.order = Order()
        self.pizza1 = ПиццаПепперони()
        self.pizza2 = ПиццаБарбекю()

    def test_add_pizza_to_order(self):
        order = Order()
        pizza = ПиццаПепперони()

        order.add_pizza(pizza)

        assert len(order.pizzas) == 1
        assert order.pizzas[0] == pizza

    def test_remove_pizza_from_order(self):
        order = Order()
        pizza1 = ПиццаПепперони()
        pizza2 = ПиццаБарбекю()
        order.add_pizza(pizza1)
        order.add_pizza(pizza2)

        order.remove_pizza(0)

        assert len(order.pizzas) == 1
        assert order.pizzas[0] == pizza2

    def test_remove_pizza_invalid_index(self):

        order = Order()
        pizza = ПиццаПепперони()
        order.add_pizza(pizza)

        with pytest.raises(InvalidPizzaError, match="Некорректный индекс пиццы"):
            order.remove_pizza(5)

    def test_total_price_calculation(self):
        order = Order()
        pizza1 = ПиццаПепперони()
        pizza2 = ПиццаБарбекю()
        order.add_pizza(pizza1)
        order.add_pizza(pizza2)

        total = order.total_price()

        expected_total = 590 + 690
        assert total == expected_total

    def test_total_price_with_discount(self):
        order = Order()
        pizza1 = ПиццаПепперони()
        pizza2 = ПиццаБарбекю()
        order.add_pizza(pizza1)
        order.add_pizza(pizza2)

        order.apply_discount("itmo")
        total = order.total_price()

        expected_total = (590 + 690) * 0.9
        assert total == expected_total


class TestOrderPreparation:

    def test_prepare_order_steps(self):
        order = Order()
        pizza = ПиццаПепперони()
        order.add_pizza(pizza)

        steps = order.prepare_order()

        assert len(steps) == 4  # prepare, bake, cut, box
        assert "Подготовка пиццы" in steps[0]
        assert "Выпечка пиццы" in steps[1]
        assert "Нарезка пиццы" in steps[2]
        assert "Упаковка пиццы" in steps[3]

    @pytest.mark.asyncio
    async def test_async_preparation(self):
        order = Order()
        pizza = ПиццаПепперони()
        order.add_pizza(pizza)

        with patch.object(order, 'async_operation') as mock_async:
            mock_async.return_value = "Mocked operation"

            await order.async_prepare_pizza(pizza)

            assert mock_async.call_count == 4


class TestDatabaseOperations:

    def test_pizza_save_to_db(self):

        test_engine = create_engine('sqlite:///:memory:')
        from pizza_project import Base, PizzaModel, Session
        Base.metadata.create_all(test_engine)
        TestSession = sessionmaker(bind=test_engine)
        test_session = TestSession()

        pizza = ПиццаПепперони()


        with patch('pizza_project.session', test_session):
            pizza.save_to_db()

            saved_pizza = test_session.query(PizzaModel).first()
            assert saved_pizza is not None
            assert saved_pizza.dough == pizza.dough
            assert saved_pizza.sauce == pizza.sauce
            assert saved_pizza.price == pizza.price

        test_session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])