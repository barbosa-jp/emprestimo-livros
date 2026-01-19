from django.urls import path
from . import views

app_name = 'biblioteca'

urlpatterns = [
    # Páginas principais
    path('', views.home, name='home'),
    
    # Livros
    path('livros/', views.listar_livros, name='listar_livros'),
    path('livros/<int:livro_id>/', views.detalhes_livro, name='detalhes_livro'),
    
    # Empréstimos
    path('emprestimos/solicitar/<int:livro_id>/', views.solicitar_emprestimo, name='solicitar_emprestimo'),
    path('meus-emprestimos/', views.meus_emprestimos, name='meus_emprestimos'),
    path('emprestimos/devolver/<int:emprestimo_id>/', views.devolver_emprestimo, name='devolver_emprestimo'),
    path('emprestimos/renovar/<int:emprestimo_id>/', views.renovar_emprestimo, name='renovar_emprestimo'),
    
    # Reservas
    path('reservas/fazer/<int:livro_id>/', views.fazer_reserva, name='fazer_reserva'),
    path('minhas-reservas/', views.minhas_reservas, name='minhas_reservas'),
    path('reservas/cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
]