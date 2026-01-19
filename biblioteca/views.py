from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta
from .models import Livro, Emprestimo, Reserva, Categoria, Autor

def home(request):
    """Página inicial do sistema"""
    livros_recentes = Livro.objects.filter(
        quantidade_disponivel__gt=0
    ).order_by('-data_cadastro')[:6]
    
    livros_populares = Livro.objects.filter(
        emprestimos__isnull=False
    ).distinct().order_by('?')[:6]
    
    categorias = Categoria.objects.all()[:5]
    
    context = {
        'livros_recentes': livros_recentes,
        'livros_populares': livros_populares,
        'categorias': categorias,
    }
    return render(request, 'biblioteca/home.html', context)

def listar_livros(request):
    """Lista todos os livros com filtros"""
    livros = Livro.objects.all()
    
    # Filtros
    pesquisa = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')
    autor_id = request.GET.get('autor', '')
    
    if pesquisa:
        livros = livros.filter(
            Q(titulo__icontains=pesquisa) |
            Q(autor__nome__icontains=pesquisa) |
            Q(isbn__icontains=pesquisa) |
            Q(descricao__icontains=pesquisa)
        )
    
    if categoria_id:
        livros = livros.filter(categoria_id=categoria_id)
    
    if autor_id:
        livros = livros.filter(autor_id=autor_id)
    
    # Contexto
    categorias = Categoria.objects.all()
    autores = Autor.objects.all()
    
    context = {
        'livros': livros,
        'categorias': categorias,
        'autores': autores,
        'pesquisa': pesquisa,
        'categoria_selecionada': categoria_id,
        'autor_selecionado': autor_id,
    }
    return render(request, 'biblioteca/livros/listar.html', context)

def detalhes_livro(request, livro_id):
    """Detalhes de um livro específico"""
    livro = get_object_or_404(Livro, id=livro_id)
    
    # Verificar se usuário tem empréstimo ativo deste livro
    emprestimo_ativo = None
    reserva_ativa = None
    
    if request.user.is_authenticated:
        emprestimo_ativo = Emprestimo.objects.filter(
            livro=livro,
            usuario=request.user,
            status__in=['ativo', 'renovado', 'atrasado']
        ).first()
        
        reserva_ativa = Reserva.objects.filter(
            livro=livro,
            usuario=request.user,
            status='ativa'
        ).first()
    
    context = {
        'livro': livro,
        'emprestimo_ativo': emprestimo_ativo,
        'reserva_ativa': reserva_ativa,
    }
    return render(request, 'biblioteca/livros/detalhes.html', context)

@login_required
def solicitar_emprestimo(request, livro_id):
    """Solicitar empréstimo de um livro"""
    livro = get_object_or_404(Livro, id=livro_id)
    
    # Verificar se pode emprestar
    if not livro.pode_ser_emprestado():
        messages.error(request, 'Este livro não está disponível para empréstimo no momento.')
        return redirect('biblioteca:detalhes_livro', livro_id=livro_id)
    
    # Verificar se já tem empréstimo ativo
    emprestimo_ativo = Emprestimo.objects.filter(
        livro=livro,
        usuario=request.user,
        status__in=['ativo', 'renovado', 'atrasado']
    ).exists()
    
    if emprestimo_ativo:
        messages.warning(request, 'Você já possui um empréstimo ativo deste livro.')
        return redirect('biblioteca:detalhes_livro', livro_id=livro_id)
    
    # Verificar limite de empréstimos (máximo 3)
    emprestimos_ativos = Emprestimo.objects.filter(
        usuario=request.user,
        status__in=['ativo', 'renovado', 'atrasado']
    ).count()
    
    if emprestimos_ativos >= 3:
        messages.error(request, 'Você atingiu o limite máximo de 3 empréstimos ativos.')
        return redirect('biblioteca:detalhes_livro', livro_id=livro_id)
    
    # Criar empréstimo
    if request.method == 'POST':
        data_devolucao = date.today() + timedelta(days=14)  # 14 dias
        
        emprestimo = Emprestimo.objects.create(
            livro=livro,
            usuario=request.user,
            data_devolucao_prevista=data_devolucao,
            status='ativo'
        )
        
        # Atualizar livro
        livro.quantidade_disponivel -= 1
        livro.atualizar_status()
        
        messages.success(request, 
            f'Empréstimo realizado com sucesso! '
            f'Data de devolução: {data_devolucao.strftime("%d/%m/%Y")}'
        )
        return redirect('biblioteca:meus_emprestimos')
    
    context = {
        'livro': livro,
        'data_devolucao': date.today() + timedelta(days=14),
    }
    return render(request, 'biblioteca/emprestimos/solicitar.html', context)

@login_required
def meus_emprestimos(request):
    """Lista empréstimos do usuário"""
    emprestimos = Emprestimo.objects.filter(usuario=request.user).order_by('-data_emprestimo')
    
    # Calcular multas pendentes
    for emprestimo in emprestimos.filter(status__in=['ativo', 'renovado', 'atrasado']):
        emprestimo.calcular_multa()
    
    context = {
        'emprestimos': emprestimos,
    }
    return render(request, 'biblioteca/emprestimos/meus.html', context)

@login_required
def devolver_emprestimo(request, emprestimo_id):
    """Devolver um livro emprestado"""
    emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id, usuario=request.user)
    
    if emprestimo.status == 'devolvido':
        messages.info(request, 'Este empréstimo já foi devolvido.')
        return redirect('biblioteca:meus_emprestimos')
    
    if request.method == 'POST':
        emprestimo.devolver()
        
        # Verificar se há multa
        if emprestimo.multa > 0:
            messages.warning(request, 
                f'Livro devolvido com sucesso! '
                f'Multa aplicada: R$ {emprestimo.multa:.2f}'
            )
        else:
            messages.success(request, 'Livro devolvido com sucesso!')
        
        return redirect('biblioteca:meus_emprestimos')
    
    context = {
        'emprestimo': emprestimo,
    }
    return render(request, 'biblioteca/emprestimos/devolver.html', context)

@login_required
def renovar_emprestimo(request, emprestimo_id):
    """Renovar um empréstimo"""
    emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id, usuario=request.user)
    
    if emprestimo.status != 'ativo':
        messages.error(request, 'Este empréstimo não pode ser renovado.')
        return redirect('biblioteca:meus_emprestimos')
    
    if emprestimo.esta_atrasado():
        messages.error(request, 'Não é possível renovar empréstimos atrasados.')
        return redirect('biblioteca:meus_emprestimos')
    
    if emprestimo.renovar():
        messages.success(request, 
            f'Empréstimo renovado com sucesso! '
            f'Nova data de devolução: {emprestimo.data_devolucao_prevista.strftime("%d/%m/%Y")}'
        )
    else:
        messages.error(request, 'Não foi possível renovar o empréstimo.')
    
    return redirect('biblioteca:meus_emprestimos')

@login_required
def fazer_reserva(request, livro_id):
    """Fazer reserva de um livro"""
    livro = get_object_or_404(Livro, id=livro_id)
    
    if livro.pode_ser_emprestado():
        messages.info(request, 'Este livro está disponível para empréstimo imediato.')
        return redirect('biblioteca:detalhes_livro', livro_id=livro_id)
    
    # Verificar se já tem reserva ativa
    reserva_existente = Reserva.objects.filter(
        livro=livro,
        usuario=request.user,
        status='ativa'
    ).exists()
    
    if reserva_existente:
        messages.warning(request, 'Você já possui uma reserva ativa para este livro.')
        return redirect('biblioteca:detalhes_livro', livro_id=livro_id)
    
    # Verificar limite de reservas (máximo 2)
    reservas_ativas = Reserva.objects.filter(
        usuario=request.user,
        status='ativa'
    ).count()
    
    if reservas_ativas >= 2:
        messages.error(request, 'Você atingiu o limite máximo de 2 reservas ativas.')
        return redirect('biblioteca:detalhes_livro', livro_id=livro_id)
    
    # Criar reserva
    if request.method == 'POST':
        data_expiracao = date.today() + timedelta(days=7)  # 7 dias
        
        Reserva.objects.create(
            livro=livro,
            usuario=request.user,
            data_expiracao=data_expiracao,
            status='ativa'
        )
        
        messages.success(request, 
            f'Reserva realizada com sucesso! '
            f'A reserva expira em: {data_expiracao.strftime("%d/%m/%Y")}'
        )
        return redirect('biblioteca:minhas_reservas')
    
    context = {
        'livro': livro,
        'data_expiracao': date.today() + timedelta(days=7),
    }
    return render(request, 'biblioteca/reservas/fazer.html', context)

@login_required
def minhas_reservas(request):
    """Lista reservas do usuário"""
    reservas = Reserva.objects.filter(usuario=request.user).order_by('-data_reserva')
    
    # Verificar expirações
    for reserva in reservas.filter(status='ativa'):
        if reserva.esta_expirada():
            reserva.status = 'expirada'
            reserva.save()
    
    context = {
        'reservas': reservas,
    }
    return render(request, 'biblioteca/reservas/minhas.html', context)

@login_required
def cancelar_reserva(request, reserva_id):
    """Cancelar uma reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    
    if reserva.status != 'ativa':
        messages.error(request, 'Esta reserva não pode ser cancelada.')
        return redirect('biblioteca:minhas_reservas')
    
    reserva.cancelar()
    messages.success(request, 'Reserva cancelada com sucesso!')
    
    return redirect('biblioteca:minhas_reservas')