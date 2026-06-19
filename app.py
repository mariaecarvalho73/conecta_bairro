from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = '12345'

# ==========================================
# PASTA DAS FOTOS
# ==========================================
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================================
# CONEXÃO MYSQL (CORRIGIDA E GARANTIDA)
# ==========================================
import os
import mysql.connector

def conectar_db():
    host = os.getenv("MYSQLHOST", "localhost")
    user = os.getenv("MYSQLUSER", "root")
    password = os.getenv("MYSQLPASSWORD", "")
    port = int(os.getenv("MYSQLPORT", 3306))
    database = os.getenv("MYSQLDATABASE", "conecta_bairro")

    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        database=database
    )

# ==========================================
# CRIAR TABELA
# ==========================================
def criar_tabela():
    conectar = conectar_db()
    cursor = conectar.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cadastro (
            id_cadastro INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            foto_perfil VARCHAR(255),
            nome VARCHAR(100) NOT NULL,
            nome_de_usuario VARCHAR(100) NOT NULL,
            sexo VARCHAR(20),
            email VARCHAR(100) NOT NULL,
            senha VARCHAR(100) NOT NULL
        )
    """)

    conectar.commit()
    cursor.close()
    conectar.close()


# PÁGINA INICIAL
@app.route('/')
def index():
    return render_template('index.html')


# ✅ PÁGINA HOME
@app.route('/home')
def home():
    if 'id_cadastro' not in session:
        return redirect('/login')

    sexo_usuario = session.get('sexo', '')

    try:
        conectar = conectar_db()
        cursor = conectar.cursor(dictionary=True)

        # BUSCA TODOS OS PROFISSIONAIS
        cursor.execute("""
            SELECT *
            FROM perfil_profissional
            ORDER BY id_perfil DESC
        """)

        perfis = cursor.fetchall()

        cursor.close()
        conectar.close()

        return render_template(
            'home.html',
            sexo_usuario=sexo_usuario,
            perfis=perfis
        )

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")
        return redirect('/')
    
    
# LOGIN (CORRIGIDO PARA LER OS DADOS)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        try:
            conectar = conectar_db()
            cursor = conectar.cursor()

            # Busca exato por email e senha
            cursor.execute("""
                SELECT id_cadastro, foto_perfil, nome, nome_de_usuario, sexo, email, senha, termos_aceitos 
                FROM cadastro WHERE email=%s AND senha=%s
            """, (email, senha))

            usuario = cursor.fetchone()

            cursor.close()
            conectar.close()

            if usuario:
                # Salva tudo na sessão
                session['id_cadastro'] = usuario[0]
                session['nome'] = usuario[2]
                session['nome_de_usuario'] = usuario[3]
                session['foto'] = usuario[1]
                session['sexo'] = usuario[4]
                session['termos'] = usuario[7]
                flash("✅ Login realizado com sucesso!", "sucesso")
                return redirect('/home')
            else:
                flash("❌ Email ou senha incorretos!", "erro")

        except Exception as e:
            flash(f"❌ ERRO NO LOGIN: {e}", "erro")

    return render_template('login.html')


# CADASTRO (100% CORRIGIDO - SALVA NO BANCO)
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        # Pegando os dados do formulário
        nome = request.form['nome']
        nome_de_usuario = request.form['nome_de_usuario']
        sexo = request.form['sexo']
        email = request.form['email']
        senha = request.form['senha']

        # Tratamento da foto
        foto = request.files['foto']
        nome_foto = 'padrao.png'
        if foto and foto.filename != '':
            nome_foto = f"{datetime.now().timestamp()}_{foto.filename}"
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_foto)
            foto.save(caminho)

        try:
            # 🔶 CONECTA NO BANCO
            conectar = conectar_db()
            cursor = conectar.cursor()

            # Verifica se já existe usuário com esse email ou nome
            cursor.execute("SELECT * FROM cadastro WHERE email=%s OR nome_de_usuario=%s", (email, nome_de_usuario))
            usuario_existente = cursor.fetchone()

            if usuario_existente:
                flash("❌ Email ou nome de usuário já cadastrado!", "erro")
                cursor.close()
                conectar.close()
                return redirect('/cadastro')

            # 🔶 INSERE OS DADOS - ESSA PARTE ESTAVA ERRADA ANTES
            cursor.execute("""
                INSERT INTO cadastro (foto_perfil, nome, nome_de_usuario, sexo, email, senha, termos_aceitos)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nome_foto, nome, nome_de_usuario, sexo, email, senha, False))

            # 🔶 GARANTE QUE VAI SALVAR (mesmo com autocommit, deixamos seguro)
            conectar.commit()

            # Fecha conexão
            cursor.close()
            conectar.close()

            flash("✅ Cadastro realizado! Agora faça login.", "sucesso")
            return redirect('/login')

        except Exception as e:
            # Se der erro, mostra qual é
            flash(f"❌ ERRO AO CADASTRAR: {e}", "erro")
            return redirect('/cadastro')

    # Se for GET, só mostra a página
    return render_template('cadastro.html')


# ✅ FAVORITOS
@app.route('/favoritos')
def favoritos():
    if 'id_cadastro' not in session:
        return redirect('/login')

    sexo_usuario = session.get('sexo', '')

    return render_template(
        'favoritos.html',
        sexo_usuario=sexo_usuario
    )




# ✅ CONFIGURAÇÕES (PRINCIPAL)
@app.route('/config')
def config():
    if 'id_cadastro' not in session:
        return redirect('/login')

    try:
        conectar = conectar_db()
        cursor = conectar.cursor(dictionary=True)


      
        cursor.execute("SELECT * FROM cadastro WHERE id_cadastro=%s", (session['id_cadastro'],))
        usuario = cursor.fetchone()

        # DADOS DO PERFIL PROFISSIONAL
        cursor.execute("SELECT * FROM perfil_profissional WHERE id_cadastro=%s", (session['id_cadastro'],))
        perfil = cursor.fetchone()

        # SERVIÇOS/PRODUTOS SE TIVER PERFIL
        servicos = []
        if perfil:
            cursor.execute("SELECT * FROM servicos_produtos WHERE id_perfil=%s", (perfil['id_perfil'],))
            servicos = cursor.fetchall()

        cursor.close()
        conectar.close()
        sexo_usuario = session.get('sexo', '')
        return render_template(
                 'config.html',
    usuario=usuario,
    perfil=perfil,
    servicos=servicos,
    sexo_usuario=sexo_usuario
)
    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")
        return redirect('/home')

  # DADOS DO USUÁRIO


# ✅ ALTERAR SENHA
@app.route('/alterar_senha', methods=['POST'])
def alterar_senha():
    if 'id_cadastro' not in session:
        return redirect('/login')

    senha_atual = request.form['senha_atual']
    nova_senha = request.form['nova_senha']
    confirma_senha = request.form['confirma_senha']

    if nova_senha != confirma_senha:
        flash('As senhas novas não coincidem!', 'erro')
        return redirect('/config?aba=perfil')

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()

        # Verifica senha atual
        cursor.execute("SELECT senha FROM cadastro WHERE id_cadastro=%s", (session['id_cadastro'],))
        senha_bd = cursor.fetchone()[0]

        if senha_bd != senha_atual:
            flash('Senha atual incorreta!', 'erro')
            cursor.close()
            conectar.close()
            return redirect('/config?aba=perfil')

        # Atualiza
        cursor.execute("UPDATE cadastro SET senha=%s WHERE id_cadastro=%s", (nova_senha, session['id_cadastro']))

        flash('Senha alterada com sucesso!', 'sucesso')
        cursor.close()
        conectar.close()

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")

    return redirect('/config?aba=perfil')


# ✅ ALTERAR NOME DE USUÁRIO
@app.route('/alterar_usuario', methods=['POST'])
def alterar_usuario():
    if 'id_cadastro' not in session:
        return redirect('/login')

    novo_usuario = request.form['novo_usuario']

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()

        # Verifica se já existe
        cursor.execute("SELECT id_cadastro FROM cadastro WHERE nome_de_usuario=%s AND id_cadastro!=%s", (novo_usuario, session['id_cadastro']))
        if cursor.fetchone():
            flash('Nome de usuário já existe!', 'erro')
            cursor.close()
            conectar.close()
            return redirect('/config?aba=perfil')

        cursor.execute("UPDATE cadastro SET nome_de_usuario=%s WHERE id_cadastro=%s", (novo_usuario, session['id_cadastro']))
        session['nome_de_usuario'] = novo_usuario

        flash('Nome de usuário alterado!', 'sucesso')
        cursor.close()
        conectar.close()

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")

    return redirect('/config?aba=perfil')


# ✅ ALTERAR FOTO DE PERFIL
@app.route('/alterar_foto', methods=['POST'])
def alterar_foto():
    if 'id_cadastro' not in session:
        return redirect('/login')

    foto = request.files['foto_perfil']
    if foto and foto.filename != '':
        try:
            nome_foto = f"perfil_{session['id_cadastro']}_{datetime.now().timestamp()}_{foto.filename}"
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_foto)
            foto.save(caminho)

            conectar = conectar_db()
            cursor = conectar.cursor()
            cursor.execute("UPDATE cadastro SET foto_perfil=%s WHERE id_cadastro=%s", (nome_foto, session['id_cadastro']))
            session['foto'] = nome_foto

            flash('Foto alterada!', 'sucesso')
            cursor.close()
            conectar.close()

        except Exception as e:
            flash(f"❌ Erro: {e}", "erro")

    return redirect('/config?aba=perfil')


# ✅ APAGAR CONTA
@app.route('/apagar_conta', methods=['POST'])
def apagar_conta():
    if 'id_cadastro' not in session:
        return redirect('/login')

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()
        cursor.execute("DELETE FROM cadastro WHERE id_cadastro=%s", (session['id_cadastro'],))
        cursor.close()
        conectar.close()
        session.clear()
        flash("✅ Conta apagada com sucesso!", "sucesso")

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")

    return redirect('/')


# ✅ ACEITAR TERMOS
@app.route('/aceitar_termos', methods=['POST'])
def aceitar_termos():
    if 'id_cadastro' not in session:
        return redirect('/login')

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()
        cursor.execute("UPDATE cadastro SET termos_aceitos=TRUE WHERE id_cadastro=%s", (session['id_cadastro'],))
        session['termos'] = True
        cursor.close()
        conectar.close()
        flash('Termos aceitos! Agora pode criar seu perfil profissional.', 'sucesso')

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")

    return redirect('/config?aba=profissional')


@app.route('/salvar_perfil_profissional', methods=['POST'])
def salvar_perfil_profissional():

    if 'id_cadastro' not in session or not session.get('termos'):
        flash('Você precisa aceitar os termos de uso primeiro!', 'erro')
        return redirect('/profissional')

    nome_perfil = request.form['nome_perfil']
    descricao = request.form['descricao']
    rua = request.form['rua']
    numero = request.form['numero']
    bairro = request.form['bairro']
    cidade = request.form['cidade']
    estado = request.form['estado']
    telefone = request.form.get('telefone')
    instagram = request.form.get('instagram')
    a_domicilio = True if request.form.get('a_domicilio') else False

    locais = request.form.getlist('local_exibicao')

    if 'home' in locais and 'espaco_feminino' in locais:
        local_exibicao = 'ambos'
    elif 'espaco_feminino' in locais:
        local_exibicao = 'espaco_feminino'
    else:
        local_exibicao = 'home'

    nome_logo = None
    logo = request.files.get('logo')

    if logo and logo.filename != '':
        nome_logo = f"logo_{session['id_cadastro']}_{datetime.now().timestamp()}_{logo.filename}"

        caminho = os.path.join(
            app.config['UPLOAD_FOLDER'],
            nome_logo
        )

        logo.save(caminho)

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()

        cursor.execute(
            "SELECT id_perfil FROM perfil_profissional WHERE id_cadastro=%s",
            (session['id_cadastro'],)
        )

        perfil_existente = cursor.fetchone()

        if perfil_existente:

            if nome_logo:
                cursor.execute("""
                    UPDATE perfil_profissional
                    SET nome_perfil=%s,
                        descricao=%s,
                        local_exibicao=%s,
                        rua=%s,
                        numero=%s,
                        bairro=%s,
                        cidade=%s,
                        estado=%s,
                        telefone=%s,
                        instagram=%s,
                        a_domicilio=%s,
                        logo=%s
                    WHERE id_cadastro=%s
                """, (
                    nome_perfil,
                    descricao,
                    local_exibicao,
                    rua,
                    numero,
                    bairro,
                    cidade,
                    estado,
                    telefone,
                    instagram,
                    a_domicilio,
                    nome_logo,
                    session['id_cadastro']
                ))

            else:
                cursor.execute("""
                    UPDATE perfil_profissional
                    SET nome_perfil=%s,
                        descricao=%s,
                        local_exibicao=%s,
                        rua=%s,
                        numero=%s,
                        bairro=%s,
                        cidade=%s,
                        estado=%s,
                        telefone=%s,
                        instagram=%s,
                        a_domicilio=%s
                    WHERE id_cadastro=%s
                """, (
                    nome_perfil,
                    descricao,
                    local_exibicao,
                    rua,
                    numero,
                    bairro,
                    cidade,
                    estado,
                    telefone,
                    instagram,
                    a_domicilio,
                    session['id_cadastro']
                ))

        else:
            cursor.execute("""
                INSERT INTO perfil_profissional (
                    id_cadastro,
                    nome_perfil,
                    descricao,
                    local_exibicao,
                    rua,
                    numero,
                    bairro,
                    cidade,
                    estado,
                    telefone,
                    instagram,
                    a_domicilio,
                    logo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session['id_cadastro'],
                nome_perfil,
                descricao,
                local_exibicao,
                rua,
                numero,
                bairro,
                cidade,
                estado,
                telefone,
                instagram,
                a_domicilio,
                nome_logo
            ))

            cursor.execute("""
                UPDATE cadastro
                SET ja_teve_perfil_profissional = TRUE
                WHERE id_cadastro = %s
            """, (
                session['id_cadastro'],
            ))

        conectar.commit()

        flash('Perfil profissional salvo com sucesso!', 'sucesso')

        cursor.close()
        conectar.close()

    except Exception as e:
        flash(f'❌ Erro ao salvar perfil: {e}', 'erro')

    return redirect('/profissional')

# ✅ ADICIONAR SERVIÇO
@app.route('/adicionar_item', methods=['POST'])
def adicionar_item():

    if 'id_cadastro' not in session or not session.get('termos'):
        return redirect('/config')

    nome_item = request.form['nome_item']
    descricao_item = request.form['descricao_item']

    # HOME / ESPAÇO FEMININO / AMBOS
    locais = request.form.getlist('local_exibicao')

    if 'home' in locais and 'espaco_feminino' in locais:
        local_exibicao = 'ambos'
    elif 'espaco_feminino' in locais:
        local_exibicao = 'espaco_feminino'
    else:
        local_exibicao = 'home'

    foto_item = request.files['foto_item']
    nome_foto = None

    if foto_item and foto_item.filename != '':
        nome_foto = f"item_{session['id_cadastro']}_{datetime.now().timestamp()}_{foto_item.filename}"

        caminho = os.path.join(
            app.config['UPLOAD_FOLDER'],
            nome_foto
        )

        foto_item.save(caminho)

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()

        cursor.execute(
            "SELECT id_perfil FROM perfil_profissional WHERE id_cadastro=%s",
            (session['id_cadastro'],)
        )

        perfil = cursor.fetchone()

        if not perfil:
            flash('Crie o perfil profissional primeiro!', 'erro')
            cursor.close()
            conectar.close()
            return redirect('/config?aba=profissional')

        id_perfil = perfil[0]

        cursor.execute("""
            INSERT INTO servicos_produtos (
                id_perfil,
                nome_item,
                descricao_item,
                foto_item,
                local_exibicao
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            id_perfil,
            nome_item,
            descricao_item,
            nome_foto,
            local_exibicao
        ))

        conectar.commit()

        flash('Serviço adicionado!', 'sucesso')

        cursor.close()
        conectar.close()

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")

    return redirect('/config?aba=profissional')

# ✅ EXCLUIR ITEM INDIVIDUAL
@app.route('/excluir_item/<int:id_item>')
def excluir_item(id_item):
    if 'id_cadastro' not in session:
        return redirect('/login')

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()
        cursor.execute("DELETE FROM servicos_produtos WHERE id_item=%s", (id_item,))
        cursor.close()
        conectar.close()
        flash('Item excluído!', 'sucesso')

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")

    return redirect('/config?aba=profissional')

@app.route('/espaco_feminino')
def espaco_feminino():

    if 'id_cadastro' not in session:
        return redirect('/login')

    try:
        conectar = conectar_db()
        cursor = conectar.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM perfil_profissional
            WHERE local_exibicao IN ('espaco_feminino', 'ambos')
            ORDER BY id_perfil DESC
        """)

        perfis = cursor.fetchall()

        cursor.close()
        conectar.close()

        return render_template(
            'espaco_feminino.html',
            perfis=perfis
        )

    except Exception as e:
        flash(f"Erro: {e}", "erro")
        return redirect('/home')
    
@app.route('/excluir_perfil')
def excluir_perfil():

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()

        # busca perfil
        cursor.execute("""
            SELECT id_perfil
            FROM perfil_profissional
            WHERE id_cadastro = %s
        """, (session['id_cadastro'],))

        perfil = cursor.fetchone()

        if perfil:
            id_perfil = perfil[0]

            # exclui serviços
            cursor.execute("""
                DELETE FROM servicos_produtos
                WHERE id_perfil = %s
            """, (id_perfil,))

            # exclui perfil
            cursor.execute("""
                DELETE FROM perfil_profissional
                WHERE id_perfil = %s
            """, (id_perfil,))

            conectar.commit()

        cursor.close()
        conectar.close()

    except Exception as e:
        flash(f'Erro: {e}', 'erro')

    # REDIRECIONA PARA A TELA PESSOAL
    return redirect('/conta_pessoal')

@app.route('/conta_pessoal')
def conta_pessoal():
    return render_template('conta_pessoal.html')


# ✅ EDITAR PERFIL PESSOAL APÓS EXCLUIR PROFISSIONAL
@app.route('/tornar_pessoal', methods=['POST'])
def tornar_pessoal():
    if 'id_cadastro' not in session:
        return redirect('/login')

    novo_nome_usuario = request.form['novo_nome_usuario']

    # Foto nova
    foto = request.files['nova_foto']
    nome_foto = session.get('foto')
    if foto and foto.filename != '':
        nome_foto = f"pessoal_{session['id_cadastro']}_{datetime.now().timestamp()}_{foto.filename}"
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_foto)
        foto.save(caminho)

    try:
        conectar = conectar_db()
        cursor = conectar.cursor()
        cursor.execute("""
            UPDATE cadastro 
            SET nome_de_usuario=%s, foto_perfil=%s 
            WHERE id_cadastro=%s
        """, (novo_nome_usuario, nome_foto, session['id_cadastro']))
        session['nome_de_usuario'] = novo_nome_usuario
        session['foto'] = nome_foto

        flash('Conta alterada para pessoal!', 'sucesso')
        cursor.close()
        conectar.close()

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")

    return redirect('/config?aba=perfil')


# ✅ PÁGINA PERFIL PROFISSIONAL SEPARADA
@app.route('/profissional')
def profissional():
    if 'id_cadastro' not in session:
        return redirect('/login')

    try:
        conectar = conectar_db()
        cursor = conectar.cursor(dictionary=True)

        # DADOS DO USUÁRIO
        cursor.execute("SELECT * FROM cadastro WHERE id_cadastro=%s", (session['id_cadastro'],))
        usuario = cursor.fetchone()

        # DADOS DO PERFIL PROFISSIONAL
        cursor.execute("SELECT * FROM perfil_profissional WHERE id_cadastro=%s", (session['id_cadastro'],))
        perfil = cursor.fetchone()

        # SERVIÇOS/PRODUTOS SE TIVER PERFIL
        servicos = []
        if perfil:
            cursor.execute("SELECT * FROM servicos_produtos WHERE id_perfil=%s", (perfil['id_perfil'],))
            servicos = cursor.fetchall()

        cursor.close()
        conectar.close()

        return render_template('profissional.html', usuario=usuario, perfil=perfil, servicos=servicos)

    except Exception as e:
        flash(f"❌ Erro: {e}", "erro")
        return redirect('/home')
    

    


# EXECUTAR
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
