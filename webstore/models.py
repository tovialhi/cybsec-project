from django.db import models
from django.contrib.auth.models import User
import datetime
import uuid

class Account(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	balance = models.IntegerField()

class Item(models.Model):
    name = models.CharField(max_length=60) 
    price = models.IntegerField(default=0) 

class Order(models.Model):
#account = models.ForeignKey(account, on_delete=models.CASCADE) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    order_id = models.UUIDField(default=uuid.uuid4, editable=False)
    quantity = models.IntegerField(default=1) 
    date = models.DateField(default=datetime.datetime.today)

    @staticmethod
    def getAllOrders(user_id): 
        return Order.objects.filter(user=user_id).order_by('-date')

    @staticmethod
    def getOrder(user_id, order_id): 
        return Order.objects.filter(user=user_id, id=order_id).order_by('-date')

    @staticmethod
    def getOrderTotal(user_id, order_id): 
        orders = Order.objects.filter(user=user_id, id=order_id).order_by('-date')
        total = sum(order.item.price for order in orders)
        return total

class Cart(models.Model):
#account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE) 
    quantity = models.IntegerField(default=1)


