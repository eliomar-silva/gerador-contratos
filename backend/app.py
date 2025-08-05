import os
import io
import logging
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from docxtpl import DocxTemplate
from datetime import datetime

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuração CORS aprimorada
CORS(app, resources={
    r"/.*": {
        "origins": [
            "http://127.0.0.1:5500",
            "https://eliomar-silva.github.io",
            "https://eliomar-silva.github.io/gerador-contratos/frontend/"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True,
        "max_age": 86400
    }
})

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'base-contrato.docx')

# Middleware para tratamento de CORS
@app.after_request
def after_request(response):
    allowed_origins = [
        "http://127.0.0.1:5500",
        "https://eliomar-silva.github.io",
        "https://eliomar-silva.github.io/gerador-contratos/frontend/"
    ]
    origin = request.headers.get('Origin')
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/gerar-contrato', methods=['OPTIONS'])
def handle_options():
    return jsonify({"status": "ok"}), 200

@app.route('/gerar-contrato', methods=['POST'])
def gerar_contrato():
    try:
        logger.info("Iniciando processamento de contrato")
        
        # Verificação inicial
        if not os.path.exists(TEMPLATE_PATH):
            error_msg = f"Template não encontrado em {TEMPLATE_PATH}"
            logger.error(error_msg)
            return jsonify({"erro": error_msg}), 500

        if not request.is_json:
            error_msg = "Content-Type deve ser application/json"
            logger.warning(error_msg)
            return jsonify({"erro": error_msg}), 400

        dados = request.json
        logger.debug(f"Dados recebidos: {dados}")
        
        # Validação dos campos obrigatórios
        campos_obrigatorios = [
            'comprador', 'cpfComprador', 'enderecoComprador', 'cidadeComprador',
            'ufComprador', 'marca', 'modelo', 'cor', 'combustivel', 'dataEmissao',
            'placa', 'renavam', 'valor', 'formaPagamento'
        ]
        
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                error_msg = f"Campo obrigatório faltando: {campo}"
                logger.warning(error_msg)
                return jsonify({"erro": error_msg}), 400

        # Processamento seguro do endereço
        try:
            partes_endereco = [parte.strip() for parte in dados['enderecoComprador'].split(',')]
            endereco = partes_endereco[0] if len(partes_endereco) > 0 else ""
            numero = partes_endereco[1] if len(partes_endereco) > 1 else "S/N"
            bairro = partes_endereco[2] if len(partes_endereco) > 2 else ""
        except Exception as e:
            error_msg = f"Formato de endereço inválido: {str(e)}"
            logger.error(error_msg)
            return jsonify({"erro": error_msg}), 400

        # Contexto com valores padrão para campos opcionais
        data_emissao = dados.get('dataEmissao', datetime.now().strftime('%d/%m/%Y'))
        contexto = {
            'NOME': dados['comprador'],
            'CPF_CNPJ': dados.get('cpfComprador', ''),
            'ENDERECO': endereco,
            'NUMERO': numero,
            'BAIRRO': bairro,
            'CIDADE': dados.get('cidadeComprador', ''),
            'ESTADO_UF': dados.get('ufComprador', ''),
            'CEP': dados.get('cepComprador', ''),
            'TELEFONE_CELULAR': dados.get('telefoneComprador', ''),
            'EMAIL': dados.get('emailComprador', ''),
            'MARCA': dados['marca'],
            'MODELO': dados['modelo'],
            'COR': dados.get('cor', ''),
            'COMBUSTÍVEL': dados.get('combustivel', ''),
            'DIA_MES_ANO': data_emissao,
            'ANO_FAB': dados.get('anoFab', ''),
            'ANO_MOD': dados.get('anoMod', ''),
            'QUILOMETRAGEM': dados.get('quilometragem', '0'),
            'PLACA': dados.get('placa', '').upper(),
            'RENAVAM': dados.get('renavam', ''),
            'CHASSI': dados.get('chassi', '').upper(),
            'VALOR': dados.get('valor', '0,00'),
            'DESCONTO': dados.get('desconto', '0,00'),
            'VALOR - DESCONTO': dados.get('valorFinal', '0,00'),
            'FORMA_PAGAMENTO': dados.get('formaPagamento', ''),
            'IPVA': dados.get('ipva', 'PAGO'),
            'MULTAS': dados.get('multas', 'NÃO'),
            'DIA_MES_ANO_2': data_emissao,
            'DIA': dados.get('dia', datetime.now().strftime('%d')),
            'MES': dados.get('mes', datetime.now().strftime('%m')),
            'ANO': dados.get('ano', datetime.now().strftime('%Y')),
            'NOME_2': dados.get('comprador', ''),
            'CPF_CNPJ_2': dados.get('cpfComprador', '')
        }

        logger.info("Renderizando documento DOCX")
        doc = DocxTemplate(TEMPLATE_PATH)
        doc.render(contexto)
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        logger.info("Contrato gerado com sucesso")
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"Contrato_{dados['comprador'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"
        )

    except KeyError as e:
        error_msg = f"Campo obrigatório faltando: {str(e)}"
        logger.error(error_msg)
        return jsonify({"erro": error_msg}), 400
    except Exception as e:
        error_msg = f"Erro ao gerar contrato: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({"erro": "Ocorreu um erro interno ao gerar o contrato"}), 500

@app.route('/healthcheck', methods=['GET', 'OPTIONS'])
def healthcheck():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Gerador de Contratos",
        "version": "1.0.0"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port)
