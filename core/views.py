from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .langchain_rag import load_csv_into_faiss
from .models import UserProfile, ConversationMessage
from .langchain_rag import get_chain
import json

# --- /chat ---


@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
        message = data.get("message")
       

        if not user_id or not message:
            return JsonResponse({"error": "user_id and message required."}, status=400)
        

        user = UserProfile.objects.get(id=user_id)
        

        # Save user message
        ConversationMessage.objects.create(user=user, role='user', content=message)

        # LangChain RAG
        chain = get_chain()
        response = chain.run(message)


        # Save AI message
        ConversationMessage.objects.create(user=user, role='ai', content=response)

        return JsonResponse({"response": response}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# --- /upload_docs ---
@csrf_exempt
@require_http_methods(["POST"])
def upload_docs(request):
    try:
        uploaded_file = next(iter(request.FILES.values()), None)
        

        if not uploaded_file:
            return JsonResponse({"error": "No file uploaded."}, status=400)

        filepath = f"temp_{uploaded_file.name}"
        with open(filepath, "wb+") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        load_csv_into_faiss(filepath)

        return JsonResponse({"message": "CSV loaded into LangChain RAG."}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# --- /crm/create_user ---
@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    try:
        data = json.loads(request.body)
        name = data.get("name")
        email = data.get("email")
        company = data.get("company", "")
        preferences = data.get("preferences", "")

        if not name or not email:
            return JsonResponse({"error": "Name and email required."}, status=400)

        user, created = UserProfile.objects.get_or_create(
            email=email,
            defaults={
                "name": name,
                "company": company,
                "preferences": preferences
            }
        )

        if not created:
            return JsonResponse({"message": "User already exists.", "user_id": user.id}, status=200)

        return JsonResponse({"message": "User created.", "user_id": user.id}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# --- /crm/update_user ---
@csrf_exempt
@require_http_methods(["PUT"])
def update_user(request):
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")

        if not user_id:
            return JsonResponse({"error": "User ID is required."}, status=400)

        user = UserProfile.objects.get(id=user_id)

        user.name = data.get("name", user.name)
        user.email = data.get("email", user.email)
        user.company = data.get("company", user.company)
        user.preferences = data.get("preferences", user.preferences)

        user.save()

        return JsonResponse({"message": "User updated successfully."}, status=200)

    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# --- /crm/delete_user ---
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_user(request):
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")

        if not user_id:
            return JsonResponse({"error": "User ID is required."}, status=400)

        user = UserProfile.objects.get(id=user_id)
        user.delete()

        return JsonResponse({"message": "User deleted successfully."}, status=200)

    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# --- /crm/conversations/<user_id> ---
@csrf_exempt
@require_http_methods(["GET"])
def get_conversations(request, user_id):
    try:
        user = UserProfile.objects.get(id=user_id)
        messages = ConversationMessage.objects.filter(user=user).order_by("timestamp")

        conversation_history = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            for msg in messages
        ]

        return JsonResponse({"user_id": user_id, "messages": conversation_history}, status=200)

    except UserProfile.DoesNotExist:
        return JsonResponse({"error": f"User with ID {user_id} not found."}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
# --- /reset ---
@csrf_exempt
@require_http_methods(["POST"])
def reset_memory(request):
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id", None)

        if user_id:
            # Example: Clear conversation messages for this user
            ConversationMessage.objects.filter(user_id=user_id).delete()
            return JsonResponse({"message": f"Conversation memory reset for user {user_id}."}, status=200)
        else:
            # Clear all conversation messages
            ConversationMessage.objects.all().delete()
            return JsonResponse({"message": "Conversation memory reset for all users."}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
