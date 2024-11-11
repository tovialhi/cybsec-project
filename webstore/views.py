from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Account, Item, Cart, Order
from django.db.models import Q
from django.contrib import messages
import json
import uuid


def createItems():
    # items = []
    Item.objects.create(name="Bread", price=2)
    Item.objects.create(name="Tea", price=3)
    Item.objects.create(name="Coffee", price=9)
    # acc = Account.objects.create(user=user, balance=1000)
    # return items

def createUser(request):
    userName = request.POST.get('username', None)
    userPass = request.POST.get('password', None)
    userMail = request.POST.get('email', None)

    if userName and userPass and userMail:
        #user = User.objects.get_or_create(userName, userMail)
        user = User.objects.filter(username=userName, email=userMail)
        if not user:
            user = User.objects.create_user(username=userName,
                                     email=userMail,
                                     password=userPass)
            #user.set_password(userPass)
            acc = Account.objects.create(user=user, balance=1000)
            return acc
        else:
            acc = Account.objects.filter(user=user).first()
            return acc

    return None

def signupView(request):
    if request.method == 'POST':
        acc = createUser(request)
        if acc:
            return redirect('/login')
            #return render(request,'login.html', {'account': acc})
    return render(request, 'signup.html')


@login_required
def add_to_cart(request, item_id):
    itemCart = Cart.objects.filter(user=request.user, item=item_id).first()

    if itemCart:
        itemCart.quantity += 1
        itemCart.save()
        messages.success(request, "Item added to your cart.")
    else:
        Cart.objects.create(user=request.user, item=item_id)
        messages.success(request, "Item added to your cart.")

@login_required
def remove_from_cart(request, item_id):
    itemCart = Cart.objects.filter(user=request.user, item=item_id).first()

    if itemCart and itemCart.user == request.user:
        if itemCart.quantity > 1:
            itemCart.quantity -= 1
            itemCart.save()
        else:
            itemCart.delete()
            messages.success(request, "Item removed from your cart.")

@login_required
def getCartSum(request):
    # cart_items = Cart.objects.filter(user=request.user)
    cart_items = Cart.getCart(request.user)
    return sum(cartItem.quantity * cartItem.item.price for cartItem in cart_items)

@login_required
def emptyCart(user):
    cart_items = Cart.objects.filter(user=user)
    for item in cart_items: item.delete()

@login_required
def makeOrder(user):
    cart_items = Cart.objects.filter(user=user)
    if cart_items:
        orderId = uuid.uuid4()
        for cartItem in cart_items:
            Order.objects.create(user=request.user, item=cartItem.item, order_id=orderId, quantity=cartItem.quantity)
        emptyCart(request.user)
        return orderId
    return -1

@login_required
def buyCart(request):
    account = Account.objects.filter(user=request.user)
    total_price = getCartSum(request.user)

    if total_price > 0 and account.balance >= total_price:
        account.balance -= total_price
        orderId = makeOrder(request.user)
        account.save()
        context = {
            "items": Order.getOrder(request.user. orderId),
            "total_price": total_price,
        }
        return render(request, "ordersuccess.html", context)

    return render(request, "orderfailed.html", {"balance": account.balance})

@login_required
def addItemView(request):
    items = Item.objects.all()

    if request.method == 'POST':
        item_id = request.POST.get('id')
        item = Item.getItem(item_id)
        add_to_cart(request, item)
    return render(request, 'index.html', {'items' : items})

@login_required
def removeItemView(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        remove_from_cart(request, item_id)

    cart_items = Cart.getCart(request.user)
    total_price = getCartSum(request)
    context = {
        "cart_items": cart_items,
        "total_price": total_price,
    }
    return render(request, 'cart.html', context)

@login_required
def cartView(request):
    cart_items = Cart.getCart(request.user)
    total_price = getCartSum(request)

    context = {
        "cart_items": cart_items,
        "total_price": total_price,
    }

    return render(request, "cart.html", context)


@login_required # May be the fix idk, we'll see later
def homePageView(request):
    if not request.user.is_authenticated:
        return redirect('login/')

    allItems = Item.objects.all()
    if len(allItems) == 0:
        createItems()
    #accounts = Account.objects.filter(owner__username = request.user.username)
    return render(request, 'index.html', {'items': allItems})

