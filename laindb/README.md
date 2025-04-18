# LainDB

LainDB é um banco de dados leve, baseado em arquivos JSON, projetado para armazenar e manipular dados de maneira simples e flexível. Este módulo permite criar bancos de dados, tabelas, inserir e consultar registros, além de manipular o esquema das tabelas.

## Instalação

Este módulo pode ser facilmente integrado em seu projeto Python. Para usá-lo, basta copiá-lo para o diretório do seu projeto ou instalá-lo via pip se estiver disponível em um repositório.

### Dependências

- Python 3.x
- Nenhuma dependência externa (tudo é feito utilizando bibliotecas padrão do Python como `os`, `json`, `shutil`, etc.)

## Como Usar

### 1. Criar ou Carregar um Banco de Dados

Você pode criar um novo banco de dados ou carregar um banco de dados existente.

```python
from laindb.laindb import Lainconfig

db_name = "meu_banco"
db = Lainconfig.load_db(db_name)
```

### 2. Criar Tabelas

Após criar ou carregar um banco de dados, você pode criar tabelas dentro dele.

```python
db.create_table("usuarios", {
    "id": "int",
    "nome": "str",
    "idade": "int"
})
```

### 3. Inserir Registros

Para inserir registros nas tabelas:

```python
record = {
    "id": 1,
    "nome": "Lain",
    "idade": 25
}
db.insert("usuarios", record)
```

### 4. Consultar Registros

Você pode consultar registros por ID ou realizar consultas com base em condições específicas.

#### Buscar todos os registros

```python
usuarios = db.find_all("usuarios")
```

#### Buscar um registro por ID

```python
usuario = db.find_by_id("usuarios", 1)
```

#### Consultar com condições

```python
resultados = db.query("usuarios", {"idade": {">": 20}})
```

### 5. Atualizar Registros

Para atualizar um registro, basta fornecer o ID e os novos dados.

```python
db.update("usuarios", 1, {"idade": 26})
```

### 6. Deletar Registros

Para excluir um registro pelo ID:

```python
db.delete("usuarios", 1)
```

### 7. Manipulação do Esquema

Você pode adicionar ou remover colunas de uma tabela.

#### Adicionar uma nova coluna

```python
db.add_column("usuarios", "email")
```

#### Remover uma coluna

```python
db.remove_column("usuarios", "email")
```

### 8. Backup e Restauração

O módulo também oferece suporte para backup e restauração do banco de dados.

#### Fazer Backup

```python
db.backup("backup.zip")
```

#### Restaurar Backup

```python
db.restore("backup.zip")
```

## Estrutura do Banco de Dados

Cada banco de dados é armazenado em uma pasta chamada `instances`, dentro da pasta onde o módulo está localizado. Dentro do banco de dados, há pastas para cada tabela, que contêm arquivos JSON:

- `tabela_nome_columns.json`: Define o esquema da tabela (colunas e tipos de dados).
- `tabela_nome_data.json`: Armazena os registros da tabela.

## Funções e Métodos

- **Lainconfig.load_db(db_name)**: Carrega ou cria um banco de dados com o nome `db_name`.
- **Laindb.create_table(table_name, columns)**: Cria uma nova tabela no banco de dados.
- **Laindb.insert(table_name, record)**: Insere um novo registro na tabela.
- **Laindb.find_all(table_name)**: Retorna todos os registros de uma tabela.
- **Laindb.find_by_id(table_name, record_id)**: Retorna um registro específico de uma tabela por ID.
- **Laindb.update(table_name, record_id, new_data)**: Atualiza um registro na tabela.
- **Laindb.delete(table_name, record_id)**: Deleta um registro de uma tabela.
- **Laindb.add_column(table_name, column_name)**: Adiciona uma nova coluna à tabela.
- **Laindb.remove_column(table_name, column_name)**: Remove uma coluna da tabela.
- **Laindb.query(table_name, conditions)**: Realiza uma consulta com base em condições específicas.
- **Laindb.backup(backup_path)**: Faz backup do banco de dados.
- **Laindb.restore(backup_path)**: Restaura o banco de dados a partir de um backup.

## Contribuindo

1. Faça o fork do projeto.
2. Crie uma branch para suas mudanças (`git checkout -b feature/novidade`).
3. Faça suas modificações e adicione testes conforme necessário.
4. Envie um pull request para a branch principal.
