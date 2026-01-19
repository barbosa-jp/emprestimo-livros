from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('cadastrar/', views.cadastrar, name='cadastrar'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
]