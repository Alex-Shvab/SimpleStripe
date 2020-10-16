import stripe
from django.conf import settings
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView


class HomePageView(TemplateView):
    template_name = 'test_stripe/home.html'


@csrf_exempt
def stripe_config(request):
    """
    Create public key and sand it to client
    """
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_TEST_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)


@csrf_exempt
def create_checkout_session(request):
    """
    Create new Checkout Session and send ID
    """
    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # For full details see https://stripe.com/docs/api/checkout/sessions/create
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                line_items=[
                    {
                        'name': 'iPhone 12',
                        'quantity': 1,
                        'currency': 'usd',
                        'amount': '2000',
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})


@csrf_exempt
def stripe_webhook(request):
    """
    Prints a message every time a payment goes through successfully
    """
    stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    endpoint_secret = settings.DJSTRIPE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        print("Payment was successful.")
        # TODO: run some custom code here

    return HttpResponse(status=200)


class SuccessView(TemplateView):
    """ Redirect to a success page after a successful payment """
    template_name = 'test_stripe/success.html'


class CancelledView(TemplateView):
    """ Redirect to a cancellation page after a cancelled payment """
    template_name = 'test_stripe/cancelled.html'
