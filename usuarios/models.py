from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('comum', 'Comum'),
        ('funcionario', 'Funcionário'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefone = models.CharField(max_length=20, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True, unique=True)
    foto = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, default='comum')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
        ordering = ['user__first_name']
    
    def __str__(self):
        return f"Perfil de {self.user.get_full_name() or self.user.username}"
    
    def get_tipo_display(self):
        return dict(self.TIPO_USUARIO_CHOICES).get(self.tipo_usuario, self.tipo_usuario)