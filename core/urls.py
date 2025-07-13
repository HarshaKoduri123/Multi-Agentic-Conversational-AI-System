from django.urls import path
from . import views

urlpatterns = [
    path('chat', views.chat),
    path('upload_docs', views.upload_docs),
    path('crm/create_user', views.create_user),
    path('crm/update_user', views.update_user),
    path('crm/conversations/<str:user_id>', views.get_conversations),
    path('reset', views.reset_memory),
    path('crm/delete_user', views.delete_user),
]
