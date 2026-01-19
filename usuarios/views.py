from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import FormCadastroUsuario, FormLoginUsuario, FormEditarPerfil

def cadastrar(request):
    """Página de cadastro de usuário"""
    if request.user.is_authenticated:
        return redirect('biblioteca:home')
    
    if request.method == 'POST':
        form = FormCadastroUsuario(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Cadastro realizado com sucesso! Bem-vindo(a), {user.first_name}!')
            return redirect('biblioteca:home')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = FormCadastroUsuario()
    
    context = {'form': form}
    return render(request, 'usuarios/cadastrar.html', context)

def login_usuario(request):
    """Página de login"""
    if request.user.is_authenticated:
        return redirect('biblioteca:home')
    
    if request.method == 'POST':
        form = FormLoginUsuario(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo(a) de volta, {user.first_name}!')
                
                # Redirecionar para próxima página se especificada
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('biblioteca:home')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    else:
        form = FormLoginUsuario()
    
    context = {'form': form}
    return render(request, 'usuarios/login.html', context)

@login_required
def logout_usuario(request):
    """Logout do usuário"""
    logout(request)
    messages.success(request, 'Você saiu do sistema com sucesso.')
    return redirect('biblioteca:home')

@login_required
def perfil(request):
    """Página de perfil do usuário"""
    user = request.user
    
    # Estatísticas - CORRIGIDO
    from biblioteca.models import Emprestimo, Reserva
    
    # Filtro correto para empréstimos ativos
    emprestimos_ativos = Emprestimo.objects.filter(
        usuario=user,
        status__in=['ativo', 'renovado', 'atrasado']
    ).count()
    
    total_emprestimos = Emprestimo.objects.filter(usuario=user).count()
    reservas_ativas = Reserva.objects.filter(usuario=user, status='ativa').count()
    
    # Pegar o perfil do usuário
    try:
        perfil_usuario = user.perfil
    except:
        from .models import PerfilUsuario
        perfil_usuario, created = PerfilUsuario.objects.get_or_create(user=user)
    
    context = {
        'user': user,
        'perfil_usuario': perfil_usuario,
        'emprestimos_ativos': emprestimos_ativos,
        'total_emprestimos': total_emprestimos,
        'reservas_ativas': reservas_ativas,
    }
    return render(request, 'usuarios/perfil.html', context)

@login_required
def editar_perfil(request):
    """Editar perfil do usuário"""
    if request.method == 'POST':
        form = FormEditarPerfil(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('usuarios:perfil')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = FormEditarPerfil(instance=request.user)
    
    context = {'form': form}
    return render(request, 'usuarios/editar_perfil.html', context)