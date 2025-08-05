from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Permite todas as origens (apenas para desenvolvimento)
from flask import Flask, request, send_file
from docxtpl import DocxTemplate
import io
import os

app = Flask(__name__)

@app.route('/gerar-contrato', methods=['POST'])
def gerar_contrato():
    try:
        # Receber dados do frontend
        dados = request.json
        
        # Caminho absoluto para o template
        template_path = os.path.join(os.path.dirname(__file__), 'base-contrato.docx')
        
        # Carregar template
        doc = DocxTemplate(template_path)
        
        # Contexto de substituição
        contexto = {
            'NOME': dados['comprador'],
            'CPF_CNPJ': dados['cpfComprador'],
            'ENDERECO': dados['enderecoComprador'].split(',')[0],
            'NUMERO': dados['enderecoComprador'].split(',')[1],
            'BAIRRO': dados['enderecoComprador'].split(',')[2],
            'CIDADE': dados['cidadeComprador'],
            'ESTADO_UF': dados['ufComprador'],
            'CEP': dados['cepComprador'],
            'TELEFONE_CELULAR': dados['telefoneComprador'],
            'EMAIL': dados['emailComprador'],
            'MARCA': dados['marca'],
            'MODELO': dados['modelo'],
            'COR': dados['cor'],
            'COMBUSTÍVEL': dados['combustivel'],
            'DIA_MES_ANO': dados['dataEmissao'],
            'ANO_FAB': dados['anoFab'],
            'ANO_MOD': dados['anoMod'],
            'QUILOMETRAGEM': dados['quilometragem'],
            'PLACA': dados['placa'],
            'RENAVAM': dados['renavam'],
            'CHASSI': dados['chassi'],
            'VALOR': dados['valor'],
            'DESCONTO': dados['desconto'],
            'VALOR - DESCONTO': dados['valorFinal'],
            'FORMA_PAGAMENTO': dados['formaPagamento'],
            'IPVA': dados['ipva'],
            'MULTAS': dados['multas'],
            'DIA_MES_ANO_2': dados['dataEmissao'],
            'DIA': dados['dia'],
            'MES': dados['mes'],
            'ANO': dados['ano'],
            'NOME_2': dados['comprador'],
            'CPF_CNPJ_2': dados['cpfComprador']
        }
        
        # Renderizar documento
        doc.render(contexto)
        
        # Criar arquivo em memória
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name='Contrato_Gerado.docx'
        )
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':

    app.run(port=5000)

