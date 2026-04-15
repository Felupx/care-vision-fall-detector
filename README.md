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
4. Coloque um vídeo de teste na pasta `data/`.
5. Execute com um dos comandos abaixo:

```bash
python src/main.py
python src/main.py --video vd02.mp4
python src/main.py --camera 0
```

## 🧠 Como a detecção funciona nesta versão

Esta primeira versão foi pensada para a etapa de analise de videos. O algoritmo combina:

- pose corporal identificada com MediaPipe/CVZone;
- proporcao do corpo para saber se a pessoa ficou mais "horizontal";
- deslocamento vertical rapido do quadril;
- permanencia da pessoa proxima ao chao por alguns frames.

Na tela, o sistema mostra:

- `POSTURA ESTAVEL` quando nao ha indicio de queda;
- `RISCO DE QUEDA` quando detecta um movimento suspeito;
- `QUEDA CONFIRMADA` quando o evento persiste e se parece com uma queda real.

## 🚧 Próximos Passos (Backlog)
- [ ] Refinar algoritmo para reduzir falsos positivos com testes em mais videos e diferentes angulos.
- [ ] Integrar sistema de notificação externa (ex: envio de mensagem automática).
- [ ] Lidar com cenários de oclusão (quando móveis tampam parte do corpo).
- [ ] Adaptar a mesma lógica para monitoramento continuo com webcam.
