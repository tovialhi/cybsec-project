import requests
from django.http import JsonResponse
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import ipaddress
import socket
from urllib.parse import urlparse
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import csrf_protect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Account, Item, Cart, Order, LoginAttempt
from django.db.models import Q
from django.db import connection, transaction
from django.contrib import messages
import json
import uuid
import sqlite3


def createItems():
    Item.objects.create(name="Bread", price=2)
    Item.objects.create(name="Tea", price=3)
    Item.objects.create(name="Coffee", price=9)
    Item.objects.create(name="The object", price=99999)


def validatePassword(password):
    if not password or len(password) < 8 or len(password) > 16:
        return False

    digit_found = False
    special_char_found = False
    uppercase_found = False
    lowercase_found = False
    password_special_characters = set("!@#$^&*()_+[]{}|;:,.<>?/")
    for char in password:
        if char.isdigit():
            digit_found = True
        elif char in password_special_characters:
            special_char_found = True
        elif char.isupper():
            uppercase_found = True
        elif char.islower():
            lowercase_found = True
    return digit_found and special_char_found and uppercase_found and lowercase_found


def createUser(request):
    userName = request.POST.get('username', None)
    userPass = request.POST.get('password', None)
    userMail = request.POST.get('email', None)

    # FLAW: Identification and Authentication Failures
    # FIX: Identification and Authentication Failures (weak password)
    # if not validatePassword(userPass):
    #     return None

    if userName and userPass and userMail:
        user = User.objects.filter(username=userName, email=userMail).first()
        if not user:
            user = User.objects.create_user(username=userName,
                                            email=userMail,
                                            password=userPass)
            acc = Account.objects.create(user=user, balance=1000)
            return acc
        else:
            acc = Account.objects.filter(user=user).first()
            return acc
    return None


@login_required
# @csrf_protect
def newitemView(request):
    # FLAW: Broken Access Control
    # FIX: Broken Access Control
    # if not request.user.is_superuser:
    #     return redirect('/')

    if request.method == 'POST':
        name = request.POST.get('name', None)
        price = request.POST.get('price', None)
        if name and price:
            Item.objects.create(name=name, price=price)

    return render(request, 'newitem.html')


def loginView(request):
    if request.method == 'POST':
        userName = request.POST.get('username', None)
        userPass = request.POST.get('password', None)
        user = User.objects.filter(username=userName).first()
        auth_user = authenticate(
            username=userName, password=userPass)

        # FLAW: Identification and Authentication Failures
        # FIX: Brute force login
        # attempts = LoginAttempt.getLoginAttempts(user, 1)
        # if attempts > 5:
        #     return render(request, 'login.html', {"message": "Too many failed login attempts"})

        if auth_user:
            login(request, auth_user)
            return redirect('/')
        if user:
            LoginAttempt.objects.create(user=user)
            return render(request, 'login.html', {"message": "Wrong password"})
    return render(request, 'login.html', {"message": ""})


def signupView(request):
    if request.method == 'POST':
        acc = createUser(request)
        if acc:
            return redirect('/login')
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
    cart_items = Cart.getCart(request.user)
    return sum(cartItem.quantity * cartItem.item.price for cartItem in cart_items)


@login_required
def emptyCart(request):
    cart_items = Cart.objects.filter(user=request.user)
    for item in cart_items:
        item.delete()


@login_required
@transaction.atomic
def makeOrder(request):
    cart_items = Cart.getCart(request.user)
    if cart_items:
        orderId = uuid.uuid4()
        for cartItem in cart_items:
            Order.objects.create(user=request.user, item=cartItem.item,
                                 order_id=orderId, quantity=cartItem.quantity)
        emptyCart(request)
        return orderId
    return None


@login_required
@transaction.atomic
def buyCart(request):
    account = Account.objects.filter(user=request.user).first()
    total_price = getCartSum(request)

    if total_price > 0 and account.balance >= total_price:
        orderId = makeOrder(request)
        if orderId != None:
            account.balance -= total_price
            account.save()
            order_items = Order.getOrder(request.user, orderId)
            context = {
                "order_id": orderId,
                "order_items": order_items,
                "total_price": total_price,
            }
            return render(request, "ordersuccess.html", context)
    return render(request, "orderfailed.html", {"balance": account.balance})


@login_required
# @csrf_protect
def addItemView(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        item = Item.getItem(item_id)
        add_to_cart(request, item)
    return redirect('/')


@login_required
# @csrf_protect
def removeItemView(request):
    if request.method == 'POST':
        item_id = request.POST.get('id')
        remove_from_cart(request, item_id)
    return redirect('/cart')


@login_required
def cartView(request):
    cart_items = Cart.getCart(request.user)
    total_price = getCartSum(request)

    context = {
        "cart_items": cart_items,
        "total_price": total_price,
    }

    return render(request, "cart.html", context)


@login_required
# @csrf_protect
def checkoutView(request):
    return buyCart(request)


@login_required
def ordersView(request):
    orders = Order.getAllOrdersGrouped(request.user)

    account = Account.objects.filter(user=request.user).first()
    context = {
        'orders': orders,
        'account': {
            'username': account.user.username,
            'email': account.user.email,
            'balance': account.balance
        }
    }
    return render(request, 'orders.html', context)


def validate_image_url(url):
    parsed_url = urlparse(url)
    if not url or parsed_url.scheme not in ('http', 'https'):
        return False
    try:
        parsed_url = urlparse(url)
        ip = socket.gethostbyname(parsed_url.hostname)
        if ipaddress.ip_address(ip).is_private:
            return False
        allowed_domains = ["i.imgur.com", "flickr.com", 'images.unsplash.com',
                           'cdn.pixabay.com',]
        if parsed_url.hostname not in allowed_domains:
            return False
    except Exception:
        return False
    return True


def validate_image_get(image_url):
    valid = validate_image_url(image_url)
    if not valid:
        return None, {'message': 'Not a valid image url'}
    response = requests.get(image_url, timeout=5)
    try:
        image = Image.open(BytesIO(response.content))
        if image.format not in ['JPEG', 'PNG', 'GIF']:
            return None, {'message': 'Not a valid image format'}
        image.load()
        image.verify()
    except Exception:
        return None, {'message': 'Invalid image'}
    return response, None


@login_required
def upload_profile_picture(request, image_url):
    message = {'message': 'Not a valid profile picture'}

    # FLAW: SSRF
    response = requests.get(image_url)

    # FIX: SSRF
    # response, message = validate_image_get(image_url)
    # if response and response.status_code == 200:

    if response.status_code == 200:
        account = Account.objects.filter(user=request.user).first()
        account.picture.save(
            f'profile_pic_{request.user.username}.jpg', ContentFile(response.content))
        return True, {'message': 'Profile picture updated successfully'}
    return False, message


@login_required
# @csrf_protect
def profilepicView(request):
    account = Account.objects.filter(user=request.user).first()
    if request.method == 'POST':
        picUrl = request.POST.get('url')
        message = {}

        success, message = upload_profile_picture(request, picUrl)

        context = {
            'items': Item.objects.all(),
            'account': {
                'username': account.user.username,
                'email': account.user.email,
                'balance': account.balance,
                'picture': account.picture
            },
            'message': message['message']
        }
        return render(request, 'index.html', context)
    return redirect("/")


@login_required
# @csrf_protect
def filterView(request):
    account = Account.objects.filter(user=request.user).first()
    itemFilter = request.POST.get('filter')

    # FLAW: SQL injection
    query = "SELECT * FROM webstore_item WHERE name LIKE '%" + itemFilter + "%'"
    items = Item.objects.raw(query)

    # FIX : SQL injection
    # items = Item.objects.filter(
    #     name=itemFilter) if itemFilter else Item.objects.all()

    context = {
        'items': items,
        'account': {
            'username': account.user.username,
            'email': account.user.email,
            'balance': account.balance,
            'picture': account.picture
        }
    }
    return render(request, 'index.html', context)


@login_required
def homePageView(request):
    if not request.user.is_authenticated:
        return redirect('login/')

    account = Account.objects.filter(user=request.user).first()

    if not account:
        return redirect('login/')

    allItems = Item.objects.all()
    if len(allItems) == 0:
        createItems()
        allItems = Item.objects.all()
    context = {
        'items': allItems,
        'account': {
            'username': account.user.username,
            'email': account.user.email,
            'balance': account.balance,
            'picture': account.picture
        }
    }
    return render(request, 'index.html', context)
