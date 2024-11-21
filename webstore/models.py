from django.db import models
from django.contrib.auth.models import User
import datetime
import uuid


class LoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.datetime.today)

    @staticmethod
    def getLoginAttempts(user_id, minutes):
        current_time = datetime.datetime.today()
        time_threshold = current_time - datetime.timedelta(minutes=minutes)
        # attempts = LoginAttempt.objects.filter(
        #     user=user_id, date__gt=time_threshold)

        attempts = LoginAttempt.objects.filter(
            user=user_id, date__range=[time_threshold, current_time])
        return len(attempts)


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.IntegerField()


class Item(models.Model):
    item_id = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60)
    price = models.IntegerField(default=0)

    @staticmethod
    def getItem(item_id):
        return Item.objects.filter(id=item_id).first()


class Order(models.Model):
    # account = models.ForeignKey(account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    order_id = models.UUIDField(default=uuid.uuid4, editable=False)
    quantity = models.IntegerField(default=1)
    date = models.DateField(default=datetime.datetime.today)

    @staticmethod
    def getAllOrders(user_id):
        return Order.objects.filter(user=user_id).order_by('order_id', '-date')

    @staticmethod
    def getAllOrdersGrouped(user_id):
        orders = Order.getAllOrders(user_id)
        grouped_orders = {}
        for order in orders:
            if order.order_id not in grouped_orders:
                grouped_orders[order.order_id] = {
                    'order_id': order.order_id,
                    'date': order.date,
                    'total': Order.getOrderTotal(user_id, order.order_id),
                    'order_list': []
                }
            grouped_orders[order.order_id]['order_list'].append(order)
        return list(grouped_orders.values())

    @staticmethod
    def getOrder(user_id, order_id):
        return Order.objects.filter(user=user_id, order_id=order_id)

    @staticmethod
    def getOrderTotal(user_id, order_id):
        orders = Order.objects.filter(
            user=user_id, order_id=order_id).order_by('-date')
        total = sum(order.item.price * order.quantity for order in orders)
        return total


class Cart(models.Model):
    # account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    @staticmethod
    def getCart(user_id):
        return Cart.objects.filter(user=user_id)
