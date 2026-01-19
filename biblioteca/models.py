from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, timedelta

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class Autor(models.Model):
    nome = models.CharField(max_length=200)
    nacionalidade = models.CharField(max_length=100, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    biografia = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class Livro(models.Model):
    STATUS_CHOICES = [
        ('disponivel', 'Disponível'),
        ('emprestado', 'Emprestado'),
        ('reservado', 'Reservado'),
        ('manutencao', 'Em Manutenção'),
    ]
    
    titulo = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE, related_name='livros')
    isbn = models.CharField('ISBN', max_length=13, unique=True)
    editora = models.CharField(max_length=100)
    ano_publicacao = models.IntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(date.today().year)
        ]
    )
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    descricao = models.TextField(blank=True, null=True)
    quantidade_total = models.PositiveIntegerField(default=1)
    quantidade_disponivel = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel')
    capa = models.ImageField(upload_to='livros/capas/', blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'
        ordering = ['titulo']
    
    def __str__(self):
        return f"{self.titulo} - {self.autor.nome}"
    
    def pode_ser_emprestado(self):
        return self.quantidade_disponivel > 0 and self.status == 'disponivel'
    
    def atualizar_status(self):
        if self.quantidade_disponivel == 0:
            self.status = 'emprestado'
        elif self.status == 'emprestado' and self.quantidade_disponivel > 0:
            self.status = 'disponivel'
        self.save()

class Emprestimo(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('devolvido', 'Devolvido'),
        ('atrasado', 'Atrasado'),
        ('renovado', 'Renovado'),
    ]
    
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='emprestimos')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emprestimos')
    data_emprestimo = models.DateField(auto_now_add=True)
    data_devolucao_prevista = models.DateField()
    data_devolucao_real = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    multa = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    observacoes = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        ordering = ['-data_emprestimo']
    
    def __str__(self):
        return f"Empréstimo #{self.id} - {self.livro.titulo}"
    
    def calcular_multa(self):
        if self.status in ['ativo', 'renovado'] and date.today() > self.data_devolucao_prevista:
            dias_atraso = (date.today() - self.data_devolucao_prevista).days
            self.multa = dias_atraso * 2.00  # R$ 2,00 por dia de atraso
            self.status = 'atrasado'
            self.save()
        return self.multa
    
    def devolver(self):
        self.data_devolucao_real = date.today()
        self.status = 'devolvido'
        self.save()
        
        # Atualizar livro
        self.livro.quantidade_disponivel += 1
        self.livro.atualizar_status()
    
    def renovar(self, dias=7):
        if self.status == 'ativo':
            self.data_devolucao_prevista += timedelta(days=dias)
            self.status = 'renovado'
            self.save()
            return True
        return False
    
    def esta_atrasado(self):
        return date.today() > self.data_devolucao_prevista and self.status in ['ativo', 'renovado']

class Reserva(models.Model):
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('cancelada', 'Cancelada'),
        ('concluida', 'Concluída'),
        ('expirada', 'Expirada'),
    ]
    
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='reservas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    data_reserva = models.DateTimeField(auto_now_add=True)
    data_expiracao = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativa')
    observacoes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-data_reserva']
        unique_together = ['livro', 'usuario', 'status']
    
    def __str__(self):
        return f"Reserva #{self.id} - {self.livro.titulo}"
    
    def esta_expirada(self):
        return date.today() > self.data_expiracao and self.status == 'ativa'
    
    def cancelar(self):
        self.status = 'cancelada'
        self.save()
    
    def concluir(self):
        self.status = 'concluida'
        self.save()