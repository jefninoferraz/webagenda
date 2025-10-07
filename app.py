from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
from models import db, Usuario, Compromisso
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('agenda'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Usuário desativado')
                return render_template('login.html')

            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('agenda'))
        else:
            flash('Usuário ou senha inválidos')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Limpa toda a sessão, incluindo mensagens flash
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('agenda'))

    usuarios = Usuario.query.all()
    return render_template('admin.html', usuarios=usuarios)


@app.route('/criar_usuario', methods=['POST'])
@login_required
def criar_usuario():
    if not current_user.is_admin:
        return redirect(url_for('agenda'))

    username = request.form['username']
    password = request.form['password']
    is_admin = 'is_admin' in request.form

    if Usuario.query.filter_by(username=username).first():
        flash('Usuário já existe')
        return redirect(url_for('admin'))

    novo_usuario = Usuario(username=username, is_admin=is_admin, is_active=True)
    novo_usuario.set_password(password)
    db.session.add(novo_usuario)
    db.session.commit()

    flash('Usuário criado com sucesso')
    return redirect(url_for('admin'))


@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if not current_user.is_admin:
        return redirect(url_for('agenda'))

    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        # Processar o formulário de edição (seu código atual)
        usuario.username = request.form['username']
        usuario.is_admin = 'is_admin' in request.form
        usuario.is_active = 'is_active' in request.form

        if request.form['password']:
            usuario.set_password(request.form['password'])

        db.session.commit()
        flash('Usuário atualizado com sucesso')
        return redirect(url_for('admin'))

    # Método GET - exibir formulário de edição
    return render_template('editar_usuario.html', usuario=usuario)


@app.route('/excluir_usuario/<int:id>')
@login_required
def excluir_usuario(id):
    if not current_user.is_admin:
        return redirect(url_for('admin'))

    usuario = Usuario.query.get_or_404(id)
    if usuario.username == 'admin':
        flash('Não é possível excluir o usuário administrador padrão')
        return redirect(url_for('admin'))

    # Remover compromissos do usuário
    Compromisso.query.filter_by(usuario_id=id).delete()
    db.session.delete(usuario)
    db.session.commit()

    flash('Usuário excluído com sucesso')
    return redirect(url_for('admin'))


@app.route('/agenda')
@login_required
def agenda():
    if current_user.is_admin:
        return redirect(url_for('admin'))

    # Ordenar compromissos por data e hora (mais recentes primeiro)
    agora = datetime.now()
    compromissos = Compromisso.query.filter(
        Compromisso.usuario_id == current_user.id,
        Compromisso.data_hora >= agora  # Só mostra compromissos FUTUROS
    ).order_by(Compromisso.data_hora.asc()).all()

    # Passar a data atual para o template
    hoje = datetime.now().date()

    return render_template('agenda.html', compromissos=compromissos, hoje=hoje)


@app.route('/proximos_compromissos')
@login_required
def proximos_compromissos():
    if current_user.is_admin:
        return jsonify([])

    # Calcular data de hoje e data de 7 dias à frente
    hoje = datetime.now().date()
    sete_dias_frente = hoje + timedelta(days=7)

    # Buscar compromissos dos próximos 7 dias
    compromissos = Compromisso.query.filter(
        Compromisso.usuario_id == current_user.id,
        Compromisso.data_hora >= hoje,
        Compromisso.data_hora <= sete_dias_frente
    ).order_by(Compromisso.data_hora.asc()).all()

    resultados = []
    for comp in compromissos:
        resultados.append({
            'id': comp.id,
            'nome': comp.nome,
            'descricao': comp.descricao,
            'data_hora': comp.data_hora.strftime('%d/%m/%Y %H:%M')
        })

    return jsonify(resultados)


@app.route('/criar_compromisso', methods=['GET', 'POST'])
@login_required
def criar_compromisso():
    if current_user.is_admin:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')

        novo_compromisso = Compromisso(
            nome=nome,
            descricao=descricao,
            data_hora=data_hora,
            usuario_id=current_user.id
        )
        db.session.add(novo_compromisso)
        db.session.commit()

        flash('Compromisso criado com sucesso')
        return redirect(url_for('agenda'))

    return render_template('compromisso_form.html')


@app.route('/editar_compromisso/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_compromisso(id):
    if current_user.is_admin:
        return redirect(url_for('admin'))

    compromisso = Compromisso.query.get_or_404(id)
    if compromisso.usuario_id != current_user.id:
        flash('Acesso não autorizado')
        return redirect(url_for('agenda'))

    if request.method == 'POST':
        compromisso.nome = request.form['nome']
        compromisso.descricao = request.form['descricao']
        compromisso.data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')

        db.session.commit()
        flash('Compromisso atualizado com sucesso')
        return redirect(url_for('agenda'))

    return render_template('compromisso_form.html', compromisso=compromisso)


@app.route('/excluir_compromisso/<int:id>')
@login_required
def excluir_compromisso(id):
    if current_user.is_admin:
        return redirect(url_for('admin'))

    compromisso = Compromisso.query.get_or_404(id)
    if compromisso.usuario_id != current_user.id:
        flash('Acesso não autorizado')
        return redirect(url_for('agenda'))

    db.session.delete(compromisso)
    db.session.commit()
    flash('Compromisso excluído com sucesso')
    return redirect(url_for('agenda'))


@app.route('/pesquisar_compromissos')
@login_required
def pesquisar_compromissos():
    if current_user.is_admin:
        return redirect(url_for('admin'))

    data_str = request.args.get('data', '')

    if not data_str:
        # Se não houver data, retorna todos os compromissos ordenados por data
        compromissos = Compromisso.query.filter_by(
            usuario_id=current_user.id
        ).order_by(Compromisso.data_hora.asc()).all()
    else:
        try:
            # Converter a string de data para objeto date
            data_pesquisa = datetime.strptime(data_str, '%Y-%m-%d').date()

            # Buscar compromissos do usuário na data especificada, ordenados por hora
            compromissos = Compromisso.query.filter(
                Compromisso.usuario_id == current_user.id,
                db.func.date(Compromisso.data_hora) == data_pesquisa
            ).order_by(Compromisso.data_hora.asc()).all()
        except ValueError:
            flash('Data inválida')
            return redirect(url_for('agenda'))

    resultados = []
    for comp in compromissos:
        resultados.append({
            'id': comp.id,
            'nome': comp.nome,
            'descricao': comp.descricao,
            'data_hora': comp.data_hora.strftime('%d/%m/%Y %H:%M'),
            'data': comp.data_hora.strftime('%Y-%m-%d'),
            'hora': comp.data_hora.strftime('%H:%M')  # Adicionando campo hora separado
        })

    return jsonify(resultados)


@app.route('/alterar_senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']

        if not current_user.check_password(senha_atual):
            flash('Senha atual incorreta')
            return render_template('alterar_senha.html')

        if nova_senha != confirmar_senha:
            flash('Nova senha e confirmação não coincidem')
            return render_template('alterar_senha.html')

        current_user.set_password(nova_senha)
        db.session.commit()
        flash('Senha alterada com sucesso')

        if current_user.is_admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('agenda'))

    return render_template('alterar_senha.html')


# Função para inicializar o banco de dados
def init_database():
    with app.app_context():
        db.create_all()
        # Criar usuário admin padrão se não existir
        if not Usuario.query.filter_by(username='admin').first():
            admin_user = Usuario(username='admin', is_admin=True, is_active=True)
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário admin criado: usuario=admin, senha=admin")


# Inicializar o banco de dados
init_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)