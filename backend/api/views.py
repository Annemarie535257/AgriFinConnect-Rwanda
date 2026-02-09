import json
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .explanations import eligibility_reason, recommend_amount_explanation, risk_score_description
from .ml_service import predict_eligibility, predict_risk, recommend_amount as recommend_loan_amount
from .models import UserProfile
from .serializers import LoginSerializer, RegisterSerializer

User = get_user_model()

# Swagger: generic JSON body for ML endpoints
_ml_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    description='JSON with feature keys (e.g. Age, AnnualIncome, CreditScore, LoanAmount, LoanDuration, EmploymentStatus, EducationLevel, etc.). See ML model feature list.',
)
_eligibility_response = openapi.Response('approved (bool), prediction (0/1)', openapi.Schema(type=openapi.TYPE_OBJECT, properties={'approved': openapi.Schema(type=openapi.TYPE_BOOLEAN), 'prediction': openapi.Schema(type=openapi.TYPE_INTEGER)}))
_risk_response = openapi.Response('risk_score (float)', openapi.Schema(type=openapi.TYPE_OBJECT, properties={'risk_score': openapi.Schema(type=openapi.TYPE_NUMBER)}))
_amount_response = openapi.Response('recommended_amount (float)', openapi.Schema(type=openapi.TYPE_OBJECT, properties={'recommended_amount': openapi.Schema(type=openapi.TYPE_NUMBER)}))
_chat_request = openapi.Schema(type=openapi.TYPE_OBJECT, required=['message'], properties={'message': openapi.Schema(type=openapi.TYPE_STRING), 'language': openapi.Schema(type=openapi.TYPE_STRING, enum=['en', 'fr', 'rw'])})
_chat_response = openapi.Response('reply (string)', openapi.Schema(type=openapi.TYPE_OBJECT, properties={'reply': openapi.Schema(type=openapi.TYPE_STRING)}))


def _get_payload(request):
    """Get JSON body from request (works for both DRF Request and Django request)."""
    if hasattr(request, 'data') and request.data is not None:
        return request.data if isinstance(request.data, dict) else {}
    try:
        return json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, TypeError):
        return {}


@swagger_auto_schema(method='post', operation_description='Model 1: Loan eligibility (approval/denial) prediction. POST JSON with features.', request_body=_ml_request_body, responses={200: _eligibility_response, 400: 'Error', 503: 'Models not loaded'}, tags=['ML Models'])
@api_view(['POST'])
@permission_classes([AllowAny])
def eligibility(request):
    """POST /api/eligibility/ — Model 1: loan approval prediction."""
    payload = _get_payload(request)
    try:
        approved = predict_eligibility(payload)
        reason = eligibility_reason(payload, approved)
        return Response({
            'approved': approved,
            'prediction': 1 if approved else 0,
            'reason': reason,
            'description': 'Approved means the model predicts the application would be accepted; denied means it would likely be rejected. The reason is derived from your application features (e.g. credit score, income, debt-to-income, employment, payment history).',
        })
    except FileNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', operation_description='Model 2: Default risk score (credit risk assessment). POST JSON with features.', request_body=_ml_request_body, responses={200: _risk_response, 400: 'Error', 503: 'Models not loaded'}, tags=['ML Models'])
@api_view(['POST'])
@permission_classes([AllowAny])
def risk(request):
    """POST /api/risk/ — Model 2: default risk score."""
    payload = _get_payload(request)
    try:
        risk_score = predict_risk(payload)
        risk_info = risk_score_description(risk_score)
        return Response({
            'risk_score': risk_score,
            'score': risk_score,
            'interpretation': risk_info['interpretation'],
            'description': risk_info['description'],
            'score_meaning': risk_info['score_meaning'],
        })
    except FileNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', operation_description='Model 3: Recommended loan amount for approved profile. POST JSON with features.', request_body=_ml_request_body, responses={200: _amount_response, 400: 'Error', 503: 'Models not loaded'}, tags=['ML Models'])
@api_view(['POST'])
@permission_classes([AllowAny])
def recommend_amount(request):
    """POST /api/recommend-amount/ — Model 3: recommended loan amount."""
    payload = _get_payload(request)
    try:
        amount = recommend_loan_amount(payload)
        amount_info = recommend_amount_explanation(payload, amount)
        return Response({
            'recommended_amount': amount,
            'recommendedAmount': amount,
            'amount': amount,
            'prediction': amount,
            'explanation': amount_info['explanation'],
            'basis': amount_info['basis'],
        })
    except FileNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', operation_description='Multilingual chatbot (Kinyarwanda, English, French). POST message + language. Uses saved T5 model when available.', request_body=_chat_request, responses={200: _chat_response}, tags=['Chatbot'])
@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    """POST /api/chat/ — Chatbot using saved T5 model (saved-model/); falls back to placeholder if unavailable."""
    from api.chatbot_service import generate_reply
    payload = _get_payload(request)
    message = (payload.get('message') or '').strip()
    language = payload.get('language', 'en')
    if not message:
        return Response({'reply': 'Please send a message.', 'response': 'Please send a message.'})
    reply = generate_reply(message)
    if reply is None:
        # Fallback when model not loaded or generation failed
        from api.chatbot_service import get_load_error
        err_msg = get_load_error()
        replies = {
            'en': (
                "Thank you for your message. The chatbot model is not available right now. "
                "To apply for a loan, use the Loan Eligibility and Loan Amount Recommendation tools. "
                "We support Kinyarwanda, English, and French."
            ),
            'fr': (
                "Merci pour votre message. Le modèle du chatbot n'est pas disponible. "
                "Pour demander un prêt, utilisez les outils d'éligibilité et de recommandation ci-dessus."
            ),
            'rw': (
                "Murakoze kubutumwa. Modèle y'ikibazo ntabwo iri. "
                "Kugira ngo usabe inguzanyo, koresha ibikoresho by'emera no gutoranya inguzanyo hejuru."
            ),
        }
        reply = replies.get(language, replies['en'])
        payload = {'reply': reply, 'response': reply}
        if getattr(settings, 'DEBUG', False) and err_msg:
            payload['chatbot_load_error'] = err_msg
        return Response(payload)
    return Response({'reply': reply, 'response': reply})


# ----- Auth APIs (documented in Swagger) -----

def _user_role(user):
    """Return role: from UserProfile, or 'admin' if staff/superuser."""
    try:
        return user.agrifin_profile.role
    except UserProfile.DoesNotExist:
        return 'admin' if (user.is_staff or user.is_superuser) else 'farmer'


@swagger_auto_schema(method='post', operation_description='Register a new farmer or microfinance user. Admin is backend-created; use login only for admin.', tags=['Auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_register(request):
    """
    Register a new farmer or microfinance user.
    Admin users are created in the backend; use login only for admin.
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'role': user.agrifin_profile.role,
        },
    }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='post', operation_description='Login for all roles (farmer, microfinance, admin). Admin is backend-created.', tags=['Auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    """
    Login for all roles (farmer, microfinance, admin).
    Admin is created in the backend; use email/password to login.
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    role = _user_role(user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'email': getattr(user, 'email', user.username),
            'username': user.username,
            'role': role,
        },
    })
