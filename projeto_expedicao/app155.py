# test_env.py
# %%
import os
from dotenv import load_dotenv

print("Tentando carregar o arquivo .env...")

# A função load_dotenv retorna True se encontrou e carregou o arquivo
success = load_dotenv()

if success:
    print("SUCESSO: Arquivo .env foi encontrado e carregado!")
else:
    print("FALHA: Arquivo .env NÃO foi encontrado na pasta atual.")
    print(f"O script está sendo executado de: {os.getcwd()}") # Imprime a pasta atual

print("-" * 30)

# Agora, vamos tentar ler a variável
print("Tentando ler a variável GOOGLE_CREDENTIALS_PATH...")
cred_path = os.getenv("GOOGLE_CREDENTIALS_PATH")

print(f"O valor lido foi: {cred_path}")
# %%
