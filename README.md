# 🛡️ Care Vision - Detector de Quedas para Idosos

Projeto desenvolvido para a disciplina de UPX. Este sistema utiliza Visão Computacional para monitorar e detectar quedas em tempo real, visando auxiliar na segurança e no tempo de resposta no socorro a idosos.

## 🚀 O Problema
Quedas são uma das principais causas de acidentes graves entre a população idosa. O tempo de resposta entre a queda e o socorro é crucial. O objetivo deste projeto é criar um sistema automatizado capaz de identificar o acidente e alertar responsáveis.

## 🛠️ Tecnologias Utilizadas
* **Python**
* **OpenCV** (Processamento de imagem)
* **MediaPipe & CVZone** (Detecção e mapeamento espacial do corpo)

## ⚙️ Como rodar o projeto (Prova de Conceito)

1. Clone o repositório.
2. Crie um ambiente virtual (recomendado): `python -m venv venv` e ative-o.
3. Instale as dependências: `pip install -r requirements.txt`
4. Coloque um vídeo de teste na pasta `data/` ou altere o código para usar sua webcam.
5. Execute o script principal: `python src/main.py`

## 🚧 Próximos Passos (Backlog)
- [ ] Refinar algoritmo para reduzir falsos positivos (implementar análise de tempo de permanência e velocidade da queda).
- [ ] Integrar sistema de notificação externa (ex: envio de mensagem automática).
- [ ] Lidar com cenários de oclusão (quando móveis tampam parte do corpo).