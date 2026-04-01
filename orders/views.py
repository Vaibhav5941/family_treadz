import stripe
import json
import datetime
import resend
import logging
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from store.models import Product
from xhtml2pdf import pisa

# Get logger
logger = logging.getLogger(__name__)
 
# Initialize Resend
resend.api_key = settings.RESEND_API_KEY
# def payments(request):
#     body = json.loads(request.body)
#     order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

#     # Store transaction details inside Payment model
#     payment = Payment(
#         user = request.user,
#         payment_id = body['transID'],
#         payment_method = body['payment_method'],
#         amount_paid = order.order_total,
#         status = body['status'],
#     )
#     payment.save()

#     order.payment = payment
#     order.is_ordered = True
#     order.save()

#     # Move the cart items to Order Product table
#     cart_items = CartItem.objects.filter(user=request.user)

#     for item in cart_items:
#         orderproduct = OrderProduct()
#         orderproduct.order_id = order.id
#         orderproduct.payment = payment
#         orderproduct.user_id = request.user.id
#         orderproduct.product_id = item.product_id
#         orderproduct.quantity = item.quantity
#         orderproduct.product_price = item.product.get_price()
#         orderproduct.ordered = True
#         orderproduct.save()

#         cart_item = CartItem.objects.get(id=item.id)
#         product_variation = cart_item.variations.all()
#         orderproduct = OrderProduct.objects.get(id=orderproduct.id)
#         orderproduct.variations.set(product_variation)
#         orderproduct.save()


#         # Reduce the quantity of the sold products
#         product = Product.objects.get(id=item.product_id)
#         product.stock -= item.quantity
#         product.save()

#     # Clear cart
#     CartItem.objects.filter(user=request.user).delete()

#     # Send order recieved email to customer
#     mail_subject = 'Thank you for your order!'
#     message = render_to_string('orders/order_recieved_email.html', {
#         'user': request.user,
#         'order': order,
#     })
#     to_email = request.user.email
#     send_email = EmailMessage(mail_subject, message, to=[to_email])
#     send_email.send()

#     # Send order number and transaction id back to sendData method via JsonResponse
#     data = {
#         'order_number': order.order_number,
#         'transID': payment.payment_id,
#     }
#     return JsonResponse(data)
def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.get_price()
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    CartItem.objects.filter(user=request.user).delete()

    mail_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    try:
        print(f"🔍 DEBUG: Sending order email via Resend (payments)")
        print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
        print(f"   To: {to_email}")
        
        # RESEND API - Instead of EmailMessage.send()
        response = resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": to_email,
            "subject": mail_subject,
            "html": message,
        })
        
        print(f"✅ Resend response: {response}")
        logger.info(f"Order email sent via Resend to {to_email}")
        
    except Exception as e:
        print(f"❌ Error sending order email: {str(e)}")
        logger.error(f"Error sending order email: {str(e)}")

    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)


def place_order(request, total=0, quantity=0,):
    current_user = request.user

    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.get_price() * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            # context = {
            #     'order': order,
            #     'cart_items': cart_items,
            #     'total': total,
            #     'tax': tax,
            #     'grand_total': grand_total,
            # }
            context = {
    'order': order,
    'cart_items': cart_items,
    'total': total,
    'tax': tax,
    'grand_total': grand_total,
    'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
}
            return render(request, 'orders/payments.html', context)
        else:
         # Form is invalid, redirect back to checkout with error
            messages.error(request, 'Please fill in all required fields correctly.')
            return redirect('checkout')
    else:
        # GET request - redirect to checkout
        return redirect('checkout')

# def order_complete(request):
#     order_number = request.GET.get('order_number')
#     transID = request.GET.get('payment_id')

#     try:
#         order = Order.objects.get(order_number=order_number, is_ordered=True)
#         ordered_products = OrderProduct.objects.filter(order_id=order.id)

#         subtotal = 0
#         for i in ordered_products:
#             subtotal += i.product_price * i.quantity

#         payment = Payment.objects.get(payment_id=transID)

#         context = {
#             'order': order,
#             'ordered_products': ordered_products,
#             'order_number': order.order_number,
#             'transID': payment.payment_id,
#             'payment': payment,
#             'subtotal': subtotal,
#         }
#         return render(request, 'orders/order_complete.html', context)
#     except (Payment.DoesNotExist, Order.DoesNotExist):
#         return redirect('home')
def order_complete(request):
    order_number = request.GET.get('order_number')
    session_id = request.GET.get('session_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(id=order.payment.id)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
# @login_required(login_url='login')
# def track_order(request):
#     if request.method == 'POST':
#         order_number = request.POST.get('order_number')
        
#         try:
#             # SECURITY FIX: Add user check to ensure users can only track their own orders
#             order = Order.objects.get(
#                 order_number=order_number, 
#                 is_ordered=True,
#                 user=request.user  # This is the critical addition
#             )
#             ordered_products = OrderProduct.objects.filter(order_id=order.id)
            
#             subtotal = 0
#             for i in ordered_products:
#                 subtotal += i.product_price * i.quantity
            
#             payment = Payment.objects.get(id=order.payment.id)
            
#             # Determine status color and progress
#             status_colors = {
#                 'New': '#FFC107',
#                 'Accepted': '#17A2B8',
#                 'Completed': '#28A745',
#                 'Cancelled': '#DC3545',
#             }
            
#             status_progress = {
#                 'New': 25,
#                 'Accepted': 50,
#                 'Completed': 100,
#                 'Cancelled': 0,
#             }
            
#             context = {
#                 'order': order,
#                 'ordered_products': ordered_products,
#                 'payment': payment,
#                 'subtotal': subtotal,
#                 'status_color': status_colors.get(order.status, '#6C757D'),
#                 'status_progress': status_progress.get(order.status, 0),
#                 'order_found': True,
#             }
#             return render(request, 'accounts/track_order.html', context)
        
#         except Order.DoesNotExist:
#             context = {
#                 'order_found': False,
#                 'error_message': 'Order not found. Please check your order number.',
#             }
#             return render(request, 'accounts/track_order.html', context)
    
#     context = {
#         'order_found': None,
#     }
#     return render(request, 'accounts/track_order.html', context)
@login_required(login_url='login')
def track_order(request):
    # Get all orders for the current user
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    
    order_data = []
    
    # Determine status color and progress
    status_colors = {
        'New': '#FFC107',
        'Accepted': '#17A2B8',
        'Completed': '#28A745',
        'Cancelled': '#DC3545',
    }
    
    status_progress = {
        'New': 25,
        'Accepted': 50,
        'Completed': 100,
        'Cancelled': 0,
    }
    
    for order in orders:
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        
        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity
        
        try:
            payment = Payment.objects.get(id=order.payment.id)
        except Payment.DoesNotExist:
            payment = None
        
        order_data.append({
            'order': order,
            'ordered_products': ordered_products,
            'payment': payment,
            'subtotal': subtotal,
            'status_color': status_colors.get(order.status, '#6C757D'),
            'status_progress': status_progress.get(order.status, 0),
        })
    
    context = {
        'order_data': order_data,
        'has_orders': len(order_data) > 0,
    }
    return render(request, 'accounts/track_order.html', context)


@require_http_methods(["POST"])
def create_checkout_session(request):
    try:
        data = json.loads(request.body)
        order_number = data.get('order_number')
        
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f'Order #{order_number}',
                    },
                    'unit_amount': int(float(order.order_total) * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/orders/order_complete/') + f'?order_number={order_number}&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=request.build_absolute_uri('/orders/place_order/'),
            metadata={'order_number': order_number}
        )
        
        return JsonResponse({'sessionId': session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle payment_intent.succeeded event
    if event['type'] == 'checkout.session.completed':
      session = event['data']['object']
      order_number = session['metadata']['order_number']
    
      try:
         order = Order.objects.get(order_number=order_number, is_ordered=False)
        
         payment = Payment(
            user = order.user,
            payment_id = session['payment_intent'],
            payment_method = 'Stripe',
            amount_paid = session['amount_total'] / 100,
            status = 'COMPLETED',
         )
         payment.save()
        
         order.payment = payment
         order.is_ordered = True
         order.save()
        
         cart_items = CartItem.objects.filter(user=order.user)
         for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = order.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.get_price()
            orderproduct.ordered = True
            orderproduct.save()
            
            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variations.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()
            
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()
         
         CartItem.objects.filter(user=order.user).delete()
        
         mail_subject = 'Thank you for your order!'
         message = render_to_string('orders/order_recieved_email.html', {
            'user': order.user,
            'order': order,
         })
         to_email = order.user.email
         try:
                print(f"🔍 DEBUG: Sending order email via Resend (webhook)")
                print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
                print(f"   To: {to_email}")
                
                # RESEND API - Instead of EmailMessage.send()
                response = resend.Emails.send({
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": to_email,
                    "subject": mail_subject,
                    "html": message,
                })
                
                print(f"✅ Resend response: {response}")
                logger.info(f"Order email sent via Resend to {to_email}")
                
            except Exception as e:
                print(f"❌ Error sending order email: {str(e)}")
                logger.error(f"Error sending order email: {str(e)}")
        
      except Order.DoesNotExist:
        pass
    
    return JsonResponse({'status': 'success'})    

