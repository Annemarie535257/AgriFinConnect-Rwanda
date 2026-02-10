import json
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .explanations import eligibility_reason, recommend_amount_explanation, risk_score_description
from .ml_service import predict_eligibility, predict_risk, recommend_amount as recommend_loan_amount
from .models import (
    GetStartedEvent,
    PasswordResetToken,
    UserProfile,
    FarmerProfile,
    AgriculturalRecord,
    LoanApplication,
    Loan,
    Repayment,
)
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


@csrf_exempt
@swagger_auto_schema(method='post', operation_description='Register a new farmer or microfinance user. Admin is backend-created; use login only for admin.', tags=['Auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_register(request):
    """
    Register a new farmer or microfinance user.
    Admin users are created in the backend; use login only for admin.
    """
    data = request.data if request.data else _get_payload(request)
    serializer = RegisterSerializer(data=data)
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


@csrf_exempt
@swagger_auto_schema(method='post', operation_description='Login for all roles (farmer, microfinance, admin). Admin is backend-created.', tags=['Auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    """
    Login for all roles (farmer, microfinance, admin).
    Admin is created in the backend; use email/password to login.
    """
    data = request.data if request.data else _get_payload(request)
    serializer = LoginSerializer(data=data)
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


_forgot_password_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email'],
    properties={'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL)},
)
_reset_password_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['token', 'new_password'],
    properties={
        'token': openapi.Schema(type=openapi.TYPE_STRING),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING, minLength=8),
    },
)


@swagger_auto_schema(method='post', operation_description='Request password reset. Sends email with reset link.', request_body=_forgot_password_body, tags=['Auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_forgot_password(request):
    """POST /api/auth/forgot-password/ — Request password reset. Sends email with reset link."""
    payload = _get_payload(request)
    email = (payload.get('email') or '').strip().lower()
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(username__iexact=email)
    except User.DoesNotExist:
        return Response({'message': 'If an account exists with this email, a reset link has been sent.'})
    prt = PasswordResetToken.create_for_user(user)
    frontend_url = getattr(settings, 'PASSWORD_RESET_FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password?token={prt.token}"
    try:
        from django.core.mail import send_mail
        send_mail(
            subject='AgriFinConnect Rwanda — Reset your password',
            message=f'Click the link below to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour.\n\nIf you did not request this, ignore this email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email or user.username],
            fail_silently=True,
        )
    except Exception:
        pass
    resp = {'message': 'If an account exists with this email, a reset link has been sent.'}
    if getattr(settings, 'DEBUG', False):
        resp['reset_url'] = reset_url
    return Response(resp)


@swagger_auto_schema(method='post', operation_description='Set new password using reset token.', request_body=_reset_password_body, tags=['Auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_reset_password(request):
    """POST /api/auth/reset-password/ — Set new password using token from forgot-password email."""
    payload = _get_payload(request)
    token = (payload.get('token') or '').strip()
    new_password = payload.get('new_password', '')
    if not token:
        return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if len(new_password) < 8:
        return Response({'error': 'Password must be at least 8 characters.'}, status=status.HTTP_400_BAD_REQUEST)
    user = PasswordResetToken.get_valid_user(token)
    if user is None:
        return Response({'error': 'Invalid or expired reset link. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password has been reset. You can now sign in.'})


# ----- Activity tracking (Get Started) + Admin API -----

def _get_client_ip(request):
    """Extract client IP from request (handles proxies)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip() or None
    addr = request.META.get('REMOTE_ADDR')
    return addr if addr else None


def _is_admin(user):
    """Return True if user has admin role."""
    role = _user_role(user)
    return role == 'admin'


_activity_log_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['event_type'],
    properties={
        'event_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['modal_opened', 'register_clicked', 'login_clicked']),
        'role': openapi.Schema(type=openapi.TYPE_STRING, description='farmers, microfinances, or admin'),
    },
)


@csrf_exempt
@swagger_auto_schema(method='post', operation_description='Log Get Started activity (no auth). Visitors trigger when opening modal or clicking Register/Login.', request_body=_activity_log_body, tags=['Activity'])
@api_view(['POST'])
@permission_classes([AllowAny])
def activity_log(request):
    """POST /api/activity/log/ — Log Get Started event (modal opened, register clicked, login clicked). No auth required."""
    payload = request.data if (request.data and isinstance(request.data, dict)) else _get_payload(request)
    event_type = payload.get('event_type', 'modal_opened')
    if event_type not in ('modal_opened', 'register_clicked', 'login_clicked'):
        return Response({'error': 'Invalid event_type'}, status=status.HTTP_400_BAD_REQUEST)
    role = payload.get('role', '')
    ip = None
    try:
        ip = _get_client_ip(request)
    except Exception:
        pass
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    GetStartedEvent.objects.create(
        event_type=event_type,
        role=role,
        ip_address=ip,
        user_agent=user_agent,
    )
    return Response({'ok': True}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='get', operation_description='List Get Started activity (admin only). Requires auth token with admin role.', tags=['Admin'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_activity_list(request):
    """GET /api/admin/activity/ — List Get Started events. Admin token required."""
    if not _is_admin(request.user):
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    limit = min(int(request.query_params.get('limit', 100)), 500)
    events = GetStartedEvent.objects.all()[:limit]
    data = [
        {
            'id': e.id,
            'event_type': e.event_type,
            'role': e.role,
            'ip_address': str(e.ip_address) if e.ip_address else None,
            'user_agent': e.user_agent or None,
            'created_at': e.created_at.isoformat(),
        }
        for e in events
    ]
    return Response({'events': data, 'count': len(data)})


# ----- Dashboard APIs: Farmer, MFI, Admin -----

def _is_farmer(user):
    return _user_role(user) == 'farmer'


def _is_microfinance(user):
    return _user_role(user) == 'microfinance'


def _application_to_ml_payload(app):
    """Build ML model payload from LoanApplication."""
    from .ml_service import DEFAULT_NUMERIC, CATEGORICAL_OPTIONS
    payload = dict(DEFAULT_NUMERIC)
    payload.update({
        'Age': int(app.age),
        'AnnualIncome': float(app.annual_income),
        'CreditScore': int(app.credit_score),
        'LoanAmount': float(app.loan_amount_requested),
        'LoanDuration': int(app.loan_duration_months),
        'EmploymentStatus': app.employment_status or 'Self-Employed',
        'EducationLevel': app.education_level or 'High School',
        'MaritalStatus': app.marital_status or 'Married',
        'LoanPurpose': app.loan_purpose or 'Other',
        'HomeOwnershipStatus': 'Own',  # Default for farmers
    })
    # Ensure categorical values are valid
    for k, opts in CATEGORICAL_OPTIONS.items():
        if payload.get(k) not in opts:
            payload[k] = opts[0]
    return payload


# ----- Farmer APIs -----

@swagger_auto_schema(method='get', operation_description='Get farmer profile. Farmer only.', tags=['Farmer'])
@swagger_auto_schema(method='patch', operation_description='Update farmer profile.', tags=['Farmer'])
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def farmer_profile(request):
    """GET/PATCH /api/farmer/profile/ — Get or update farmer profile."""
    if not _is_farmer(request.user):
        return Response({'error': 'Farmer access required'}, status=status.HTTP_403_FORBIDDEN)
    profile, _ = FarmerProfile.objects.get_or_create(user=request.user)
    if request.method == 'GET':
        return Response({
            'id': profile.id,
            'location': profile.location,
            'phone': profile.phone,
            'cooperative_name': profile.cooperative_name,
            'created_at': profile.created_at.isoformat(),
        })
    # PATCH
    data = _get_payload(request)
    if 'location' in data:
        profile.location = str(data['location'])[:200]
    if 'phone' in data:
        profile.phone = str(data['phone'])[:20]
    if 'cooperative_name' in data:
        profile.cooperative_name = str(data['cooperative_name'])[:200]
    profile.save()
    return Response({
        'id': profile.id,
        'location': profile.location,
        'phone': profile.phone,
        'cooperative_name': profile.cooperative_name,
        'updated_at': profile.updated_at.isoformat(),
    })


@swagger_auto_schema(method='get', operation_description='List farmer loan applications.', tags=['Farmer'])
@swagger_auto_schema(method='post', operation_description='Submit new loan application. Runs ML models.', tags=['Farmer'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def farmer_applications(request):
    """GET /api/farmer/applications/ — List my applications. POST — Submit new with ML evaluation."""
    if not _is_farmer(request.user):
        return Response({'error': 'Farmer access required'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'POST':
        data = _get_payload(request)
        app = LoanApplication(
            user=request.user,
            age=int(data.get('age', 35)),
            annual_income=float(data.get('annual_income', 0)),
            credit_score=int(data.get('credit_score', 600)),
            loan_amount_requested=float(data.get('loan_amount_requested', 0)),
            loan_duration_months=int(data.get('loan_duration_months', 24)),
            employment_status=str(data.get('employment_status', 'Self-Employed'))[:30],
            education_level=str(data.get('education_level', 'High School'))[:30],
            marital_status=str(data.get('marital_status', 'Married'))[:20],
            loan_purpose=str(data.get('loan_purpose', 'Other'))[:50],
        )
        payload = _application_to_ml_payload(app)
        try:
            app.eligibility_approved = predict_eligibility(payload)
            app.eligibility_reason = eligibility_reason(payload, app.eligibility_approved)
            app.risk_score = predict_risk(payload)
            app.recommended_amount = recommend_loan_amount(payload) if app.eligibility_approved else None
        except FileNotFoundError:
            return Response({'error': 'ML models not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        app.save()
        return Response({
            'id': app.id,
            'status': app.status,
            'eligibility_approved': app.eligibility_approved,
            'eligibility_reason': app.eligibility_reason,
            'risk_score': app.risk_score,
            'recommended_amount': float(app.recommended_amount) if app.recommended_amount else None,
            'created_at': app.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
    # GET
    apps = LoanApplication.objects.filter(user=request.user).order_by('-created_at')[:50]
    data = [
        {
            'id': a.id,
            'loan_amount_requested': float(a.loan_amount_requested),
            'loan_duration_months': a.loan_duration_months,
            'status': a.status,
            'eligibility_approved': a.eligibility_approved,
            'risk_score': a.risk_score,
            'recommended_amount': float(a.recommended_amount) if a.recommended_amount else None,
            'created_at': a.created_at.isoformat(),
        }
        for a in apps
    ]
    return Response({'applications': data, 'count': len(data)})


@swagger_auto_schema(method='get', operation_description='List farmer approved loans.', tags=['Farmer'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farmer_loans(request):
    """GET /api/farmer/loans/ — List my approved loans."""
    if not _is_farmer(request.user):
        return Response({'error': 'Farmer access required'}, status=status.HTTP_403_FORBIDDEN)
    apps = LoanApplication.objects.filter(user=request.user, status='approved')
    loan_ids = [a.id for a in apps]
    loans = Loan.objects.filter(application_id__in=loan_ids).select_related('application')
    data = [
        {
            'id': lo.id,
            'application_id': lo.application_id,
            'amount': float(lo.amount),
            'interest_rate': float(lo.interest_rate),
            'duration_months': lo.duration_months,
            'monthly_payment': float(lo.monthly_payment),
            'created_at': lo.created_at.isoformat(),
        }
        for lo in loans
    ]
    return Response({'loans': data, 'count': len(data)})


@swagger_auto_schema(method='get', operation_description='List repayments for farmer loans.', tags=['Farmer'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farmer_repayments(request):
    """GET /api/farmer/repayments/ — List repayments for my loans."""
    if not _is_farmer(request.user):
        return Response({'error': 'Farmer access required'}, status=status.HTTP_403_FORBIDDEN)
    apps = LoanApplication.objects.filter(user=request.user, status='approved')
    loan_ids = [a.id for a in apps]
    loans = Loan.objects.filter(application_id__in=loan_ids)
    repayments = Repayment.objects.filter(loan__in=loans).select_related('loan').order_by('-due_date')[:100]
    data = [
        {
            'id': r.id,
            'loan_id': r.loan_id,
            'amount': float(r.amount),
            'due_date': str(r.due_date),
            'status': r.status,
            'paid_at': r.paid_at.isoformat() if r.paid_at else None,
        }
        for r in repayments
    ]
    return Response({'repayments': data, 'count': len(data)})


# ----- MFI APIs -----

@swagger_auto_schema(method='get', operation_description='List all loan applications for review. MFI only.', tags=['MFI'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mfi_applications(request):
    """GET /api/mfi/applications/ — List applications for MFI review."""
    if not _is_microfinance(request.user):
        return Response({'error': 'Microfinance access required'}, status=status.HTTP_403_FORBIDDEN)
    status_filter = request.query_params.get('status', 'pending')
    qs = LoanApplication.objects.filter(status=status_filter).select_related('user').order_by('-created_at')[:100]
    data = [
        {
            'id': a.id,
            'user_id': a.user_id,
            'user_email': a.user.username,
            'user_name': getattr(a.user, 'first_name', '') or '',
            'loan_amount_requested': float(a.loan_amount_requested),
            'loan_duration_months': a.loan_duration_months,
            'employment_status': a.employment_status,
            'annual_income': float(a.annual_income),
            'credit_score': a.credit_score,
            'eligibility_approved': a.eligibility_approved,
            'eligibility_reason': a.eligibility_reason,
            'risk_score': a.risk_score,
            'recommended_amount': float(a.recommended_amount) if a.recommended_amount else None,
            'status': a.status,
            'created_at': a.created_at.isoformat(),
        }
        for a in qs
    ]
    return Response({'applications': data, 'count': len(data)})


@swagger_auto_schema(method='post', operation_description='Approve or reject loan application. MFI only.', tags=['MFI'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mfi_review_application(request, pk):
    """POST /api/mfi/applications/<id>/review/ — Approve or reject."""
    if not _is_microfinance(request.user):
        return Response({'error': 'Microfinance access required'}, status=status.HTTP_403_FORBIDDEN)
    data = _get_payload(request)
    action = data.get('action', '')  # 'approve' or 'reject'
    if action not in ('approve', 'reject'):
        return Response({'error': 'action must be approve or reject'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        app = LoanApplication.objects.get(pk=pk, status='pending')
    except LoanApplication.DoesNotExist:
        return Response({'error': 'Application not found or already reviewed'}, status=status.HTTP_404_NOT_FOUND)
    from django.utils import timezone
    app.reviewed_by = request.user
    app.reviewed_at = timezone.now()
    if action == 'approve':
        app.status = 'approved'
        app.rejection_reason = ''
        amount = float(data.get('amount') or app.recommended_amount or app.loan_amount_requested)
        interest_rate = float(data.get('interest_rate', 0.12))
        duration = int(data.get('duration_months') or app.loan_duration_months)
        monthly = amount * (interest_rate / 12) * (1 + interest_rate / 12) ** duration / ((1 + interest_rate / 12) ** duration - 1) if duration else 0
        loan = Loan.objects.create(
            application=app,
            amount=amount,
            interest_rate=interest_rate,
            duration_months=duration,
            monthly_payment=round(monthly, 2),
        )
        # Create repayment schedule
        from datetime import timedelta
        from decimal import Decimal
        due = timezone.now().date()
        for i in range(duration):
            due += timedelta(days=30)
            Repayment.objects.create(loan=loan, amount=Decimal(str(round(monthly, 2))), due_date=due)
    else:
        app.status = 'rejected'
        app.rejection_reason = str(data.get('rejection_reason', ''))[:500]
    app.save()
    return Response({
        'id': app.id,
        'status': app.status,
        'reviewed_at': app.reviewed_at.isoformat(),
        'rejection_reason': app.rejection_reason if app.status == 'rejected' else None,
    })


@swagger_auto_schema(method='get', operation_description='Portfolio summary: approved loans and repayment stats. MFI only.', tags=['MFI'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mfi_portfolio(request):
    """GET /api/mfi/portfolio/ — Portfolio and repayment performance."""
    if not _is_microfinance(request.user):
        return Response({'error': 'Microfinance access required'}, status=status.HTTP_403_FORBIDDEN)
    total_loans = Loan.objects.count()
    from django.db.models import Sum
    total_disbursed = Loan.objects.aggregate(s=Sum('amount'))['s'] or 0
    repayments = Repayment.objects.select_related('loan').all()
    paid = sum(1 for r in repayments if r.status == 'paid')
    overdue = sum(1 for r in repayments if r.status == 'overdue')
    pending = sum(1 for r in repayments if r.status == 'pending')
    return Response({
        'total_loans': total_loans,
        'total_amount_disbursed': float(total_disbursed),
        'repayments': {'paid': paid, 'overdue': overdue, 'pending': pending, 'total': repayments.count()},
    })


# ----- Admin APIs (extended) -----

@swagger_auto_schema(method='get', operation_description='List users. Admin only.', tags=['Admin'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_users_list(request):
    """GET /api/admin/users/ — List users by role."""
    if not _is_admin(request.user):
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    role_filter = request.query_params.get('role', '')
    qs = UserProfile.objects.select_related('user').all()
    if role_filter in ('farmer', 'microfinance', 'admin'):
        qs = qs.filter(role=role_filter)
    limit = min(int(request.query_params.get('limit', 50)), 200)
    qs = qs[:limit]
    data = [
        {
            'id': p.user_id,
            'email': p.user.username,
            'name': getattr(p.user, 'first_name', '') or '',
            'role': p.role,
        }
        for p in qs
    ]
    return Response({'users': data, 'count': len(data)})


@swagger_auto_schema(method='get', operation_description='System stats for admin dashboard.', tags=['Admin'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_stats(request):
    """GET /api/admin/stats/ — Dashboard statistics."""
    if not _is_admin(request.user):
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    from django.db.models import Count
    farmers = UserProfile.objects.filter(role='farmer').count()
    mfi = UserProfile.objects.filter(role='microfinance').count()
    apps_pending = LoanApplication.objects.filter(status='pending').count()
    apps_approved = LoanApplication.objects.filter(status='approved').count()
    apps_rejected = LoanApplication.objects.filter(status='rejected').count()
    return Response({
        'users': {'farmers': farmers, 'microfinance': mfi},
        'applications': {'pending': apps_pending, 'approved': apps_approved, 'rejected': apps_rejected},
    })


