from django.contrib import admin
from .models import Categoria, Autor, Livro, Emprestimo, Reserva

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao']
    search_fields = ['nome']
    list_per_page = 20

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'nacionalidade', 'data_nascimento']
    search_fields = ['nome', 'nacionalidade']
    list_filter = ['nacionalidade']
    list_per_page = 20

@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'categoria', 'quantidade_disponivel', 'status']
    list_filter = ['status', 'categoria', 'autor']
    search_fields = ['titulo', 'autor__nome', 'isbn']
    readonly_fields = ['data_cadastro', 'data_atualizacao']
    list_per_page = 30
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'autor', 'isbn', 'categoria')
        }),
        ('Detalhes', {
            'fields': ('editora', 'ano_publicacao', 'descricao')
        }),
        ('Estoque', {
            'fields': ('quantidade_total', 'quantidade_disponivel', 'status')
        }),
        ('Imagem', {
            'fields': ('capa',),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('data_cadastro', 'data_atualizacao'),
            'classes': ('collapse',)
        })
    )

@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ['id', 'livro', 'usuario', 'data_emprestimo', 'data_devolucao_prevista', 'status', 'multa']
    list_filter = ['status', 'data_emprestimo']
    search_fields = ['livro__titulo', 'usuario__username', 'usuario__first_name', 'usuario__last_name']
    readonly_fields = ['data_criacao', 'data_atualizacao']
    list_per_page = 50
    
    fieldsets = (
        ('Informações do Empréstimo', {
            'fields': ('livro', 'usuario', 'status')
        }),
        ('Datas', {
            'fields': ('data_emprestimo', 'data_devolucao_prevista', 'data_devolucao_real')
        }),
        ('Financeiro', {
            'fields': ('multa',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['marcar_como_devolvido', 'calcular_multas']

    def marcar_como_devolvido(self, request, queryset):
        for emprestimo in queryset:
            if emprestimo.status != 'devolvido':
                emprestimo.devolver()
        self.message_user(request, f"{queryset.count()} empréstimos marcados como devolvidos.")
    marcar_como_devolvido.short_description = "Marcar como devolvido"

    def calcular_multas(self, request, queryset):
        total_multa = 0
        for emprestimo in queryset.filter(status__in=['ativo', 'renovado', 'atrasado']):
            multa = emprestimo.calcular_multa()
            if multa > 0:
                total_multa += multa
        self.message_user(request, f"Multas calculadas. Total: R$ {total_multa:.2f}")
    calcular_multas.short_description = "Calcular multas pendentes"

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['id', 'livro', 'usuario', 'data_reserva', 'data_expiracao', 'status']
    list_filter = ['status', 'data_reserva']
    search_fields = ['livro__titulo', 'usuario__username']
    list_per_page = 50
    
    actions = ['cancelar_reservas', 'marcar_como_concluidas']

    def cancelar_reservas(self, request, queryset):
        for reserva in queryset.filter(status='ativa'):
            reserva.cancelar()
        self.message_user(request, f"{queryset.count()} reservas canceladas.")
    cancelar_reservas.short_description = "Cancelar reservas selecionadas"

    def marcar_como_concluidas(self, request, queryset):
        for reserva in queryset.filter(status='ativa'):
            reserva.concluir()
        self.message_user(request, f"{queryset.count()} reservas marcadas como concluídas.")
    marcar_como_concluidas.short_description = "Marcar como concluídas"