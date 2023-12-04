from flask import Flask, make_response, jsonify, request
from flask_cors import CORS
import mysql.connector
import io
import zipfile
import os

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='Mysqltasks'
)

app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# CARDS ---------------------------------------------------
def sql_get_cards(sql):
    my_cursor = mydb.cursor()
    print(sql)

    my_cursor.execute(sql)
    cards = my_cursor.fetchall()
    cards_return = list()

    for card in cards:
        cards_return.append(
            {
                'id': card[0],
                'id_pessoa': card[1],                
                'titulo': card[3],
                'descricao': card[4],
                'situacao': card[5],
                'nome': card[6],
                'categoria': card[8]
            }
        )  
    return cards_return

@app.route('/cards', methods=['GET'])
def get_cards_zip():

    sql = f'''SELECT a.*, b.nome, b.email, c.nome as categoria
            FROM tb_cards a  
            INNER JOIN tb_pessoas b ON a.id_pessoa = b.id 
            INNER JOIN tb_categorias c ON a.id_categoria = c.id''' 
    
    return sql_get_cards(sql)

@app.route('/cards/<int:situacao>', methods=['GET'])
def get_cards_by_id(situacao):

    sql_situacao = 'a.situacao '

    if situacao == 1:
        sql_situacao += 'IS NULL'
    elif situacao == 2:
        sql_situacao += ' = 1'
    else:
        sql_situacao += ' = 2'

    sql = f'''SELECT a.*, b.nome, b.email, c.nome as categoria
            FROM tb_cards a  
            INNER JOIN tb_pessoas b ON a.id_pessoa = b.id 
            INNER JOIN tb_categorias c ON a.id_categoria = c.id             
            WHERE ''' + sql_situacao 
    
    dados = sql_get_cards(sql)

    return make_response(
        jsonify(
            mensagem = 'Lista de cards',
            dados = dados
        )        
    )

@app.route('/cards/<int:situacao>/logado', methods=['GET'])
def get_cards_logado(situacao):

    sql_situacao = 'AND a.situacao '

    if situacao == 1:
        sql_situacao += 'IS NULL'
    elif situacao == 2:
        sql_situacao += ' = 1'
    else:
        sql_situacao += ' = 2'

    sql = f'''SELECT a.*, b.nome, b.email, c.nome as categoria, b.Logado
            FROM tb_cards a  
            INNER JOIN tb_pessoas b ON a.id_pessoa = b.id 
            INNER JOIN tb_categorias c ON a.id_categoria = c.id             
            WHERE b.Logado = 1 ''' + sql_situacao
    
    return make_response(
        jsonify(
            mensagem = 'Lista de cards',
            dados = sql_get_cards(sql)
        )        
    )

@app.route('/cards', methods=['POST'])
def create_card():
    card = request.json
    my_cursor = mydb.cursor()
    sql = f"INSERT INTO tb_cards (id_pessoa, id_categoria, titulo, descricao) VALUES ({card['id_pessoa']}, {card['id_categoria']}, '{card['titulo']}', '{card['descricao']}')"

    my_cursor.execute(sql)
    mydb.commit()

    return make_response(
        jsonify(
            mensagem='Card cadastrado com sucesso.',
            dados=card
        )
    )


@app.route('/cards/<int:id>/<int:situacao>', methods=['PUT'])
def update_card(id, situacao):

    if situacao == 0:
        situacao = 'NULL'

    sql = f'UPDATE tb_cards SET situacao = {situacao} WHERE id = {id}'
    mydb.cursor().execute(sql)
    mydb.commit()
    return make_response(
        jsonify(
            mensagem = f'Card id: {id} atualizado.'
        )
    )

@app.route('/cards/<int:id>', methods=['DELETE'])
def delete_card(id):
    mydb.cursor().execute(f'DELETE FROM tb_cards WHERE id = {id}')
    mydb.commit()
    return make_response(
        jsonify(
            mensagem = f'Card id: {id} deletado com sucesso.'
        )
    )


    
# PESSOAS ---------------------------------------------------
def sql_get_pessoas(sql):
    my_cursor = mydb.cursor()
    my_cursor.execute(sql)
    pessoas = my_cursor.fetchall()
    pessoas_return = list()

    for pessoa in pessoas:
        pessoas_return.append(
            {
                'id': pessoa[0],
                'nome': pessoa[1],
                'email': pessoa[2]
            }
        )       
    return pessoas_return

@app.route('/pessoas', methods=['GET'])
def get_pessoas():
    sql = 'SELECT * FROM tb_pessoas'
    return make_response(
        jsonify(
            mensagem = 'Lista de pessoas',
            dados = sql_get_pessoas(sql)
        )        
    )


def get_pessoas_zip():
    sql = 'SELECT * FROM tb_pessoas'
    return sql_get_pessoas(sql)


@app.route('/pessoas/<int:id>', methods=['GET'])
def get_pessoas_by_id(id):
    
    sql = f'SELECT * FROM tb_pessoas WHERE id = {id}'
    return make_response(
        jsonify(
            mensagem = f'Pessoa id: {id}',
            dados = sql_get_pessoas(sql)
        )        
    )

@app.route('/pessoas/logado', methods=['GET'])
def get_pessoa_logada():
    sql = f'SELECT * FROM tb_pessoas WHERE Logado = 1'
    return make_response(
        jsonify(
            mensagem = f'Pessoa logada',
            dados = sql_get_pessoas(sql)
        )        
    )

@app.route('/pessoas', methods=['POST'])
def create_pessoa():
    pessoa = request.json
    my_cursor = mydb.cursor()
    sql = f"INSERT INTO tb_pessoas (nome, email, senha) VALUES ('{pessoa['nome']}', '{pessoa['email']}', '{pessoa['senha']}')"

    my_cursor.execute(sql)
    mydb.commit()

    return make_response(
        jsonify(
            mensagem='Pessoa cadastrada com sucesso.',
            dados=pessoa
        )
    )

@app.route('/pessoas', methods=['PUT'])
def logar_pessoa():
    mensagem = "Usuário não encontrado."
    pessoa = request.json    
    my_cursor = mydb.cursor()
    my_cursor.execute(f"SELECT * FROM tb_pessoas WHERE email = '{pessoa['email']}' AND senha = '{pessoa['senha']}'")
    pessoa_logada = my_cursor.fetchall()    

    id_logado = pessoa_logada[0][0]

    if pessoa_logada:
        try:
            my_cursor.execute(f"UPDATE tb_pessoas SET Logado = 0 WHERE id <> {id_logado}")
            mydb.commit()
            my_cursor.execute(f"UPDATE tb_pessoas SET Logado = 1 WHERE id = {id_logado}")        
            mydb.commit()
        except Exception as e:
            print(f'Erro no banco: {e}')

        mensagem = f'Usuário id: {id_logado} logado com sucesso.'
    
    return make_response(
        jsonify(
           mensagem = mensagem,
        )        
    )

@app.route('/pessoas/<int:id>', methods=['DELETE'])
def delete_pessoa(id):
    mydb.cursor().execute(f'DELETE FROM tb_pessoas WHERE id = {id}')
    mydb.commit()
    return make_response(
        jsonify(
            mensagem = f'Pessoa id: {id} deletada com sucesso.'
        )
    )

 
# CATEGORIAS ---------------------------------------------------
def sql_get_categorias(sql):
    my_cursor = mydb.cursor()
    my_cursor.execute(sql)
    categorias = my_cursor.fetchall()
    categorias_return = list()

    for categoria in categorias:
        categorias_return.append(
            {
                'id': categoria[0],
                'nome': categoria[1]
            }
        ) 

    return categorias_return

@app.route('/categorias', methods=['GET'])
def get_categorias():
     
    sql = 'SELECT * FROM tb_categorias'

    return make_response(
        jsonify(
            mensagem = 'Lista de categorias',
            dados = sql_get_categorias(sql)
        )        
    )

def get_categorias_zip():    
    sql = 'SELECT * FROM tb_categorias'
    return sql_get_categorias(sql)


@app.route('/categorias/<int:id>', methods=['GET'])
def get_categorias_by_id(id):
     
    sql = f'SELECT * FROM tb_categorias WHERE id={id}'

    return make_response(
        jsonify(
            mensagem = f'Categoria id: {id}',
            dados = sql_get_categorias(sql)
        )        
    )

@app.route('/categorias', methods=['POST'])
def create_categoria():
    categoria = request.json
    my_cursor = mydb.cursor()
    sql = f"INSERT INTO tb_categorias (nome) VALUES ('{categoria['nome']}')"

    my_cursor.execute(sql)
    mydb.commit()

    return make_response(
        jsonify(
            mensagem='Categoria cadastrada com sucesso.',
            dados=categoria
        )
    )


@app.route('/categorias/<int:id>', methods=['DELETE'])
def delete_categoria(id):
    mydb.cursor().execute(f'DELETE FROM tb_categorias WHERE id = {id}')
    mydb.commit()
    return make_response(
        jsonify(
            mensagem = f'Categoria id: {id} deletada com sucesso.'
        )
    )

@app.route('/exportar_zip', methods=['POST'])
def exportar_zip():
    dados_para_zip = get_cards_zip() + get_pessoas_zip() + get_categorias_zip()

    # Criar um arquivo .zip em memória
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zip_file:
        # Adicionar um arquivo chamado 'dados.txt' ao .zip com as informações
        zip_file.writestr('dados.txt', str(dados_para_zip))

    # Obter o caminho da pasta de downloads padrão
    pasta_downloads = os.path.expanduser("~/Downloads")

    # Configurar o caminho completo do arquivo no diretório de downloads
    caminho_arquivo_zip = os.path.join(pasta_downloads, 'dados_exportados.zip')

    # Salvar o arquivo .zip no diretório de downloads
    with open(caminho_arquivo_zip, 'wb') as file:
        file.write(output_zip.getvalue())

    # Configurar a resposta para o cliente
    response = make_response('Arquivo exportado para a pasta de downloads.')
    response.headers['Content-Type'] = 'text/plain'
    return response


app.run()