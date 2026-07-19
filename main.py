import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import ssl
import re
import winreg
import random  # Adicionado para a escolha aleatória de tempo

# Ignora a verificação de certificados SSL globalmente no script
ssl._create_default_https_context = ssl._create_unverified_context

def carregar_prompts():
    """Lê o arquivo de texto de forma avançada, ignorando espaços ocultos nas linhas em branco"""
    caminho_arquivo = "prompts.txt"
    
    if not os.path.exists(caminho_arquivo):
        if os.path.exists("prompts"):
            caminho_arquivo = "prompts"
        else:
            print(f"❌ AVISO: O arquivo não foi encontrado.")
            print(f"Verifique se ele se chama 'prompts.txt' e se está na pasta: {os.getcwd()}")
            return []
            
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()
        
    prompts_crus = re.split(r'\n\s*\n', conteudo)
    prompts_limpos = [p.strip() for p in prompts_crus if p.strip()]
    
    print(f"✅ Sucesso! Foram encontrados {len(prompts_limpos)} prompts no bloco de notas.")
    return prompts_limpos

def obter_versao_chrome():
    """Busca a versão exata do Chrome instalada no Windows"""
    try:
        chave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        versao, _ = winreg.QueryValueEx(chave, "version")
        versao_principal = int(versao.split('.')[0])
        return versao_principal
    except Exception as e:
        print(f"Aviso: Não foi possível detectar a versão automaticamente via registro.")
        return None

def iniciar_navegador():
    options = uc.ChromeOptions()
    
    caminho_perfil = os.path.join(os.getcwd(), 'Perfil_Whisk')
    options.add_argument(f"--user-data-dir={caminho_perfil}")
    
    print("\nIniciando o Chrome...")
    
    versao_atual = obter_versao_chrome()
    
    if versao_atual:
        print(f"🔎 Versão do Chrome detectada: {versao_atual}")
        driver = uc.Chrome(options=options, version_main=versao_atual)
    else:
        print("Deixando o driver tentar descobrir a versão sozinho...")
        driver = uc.Chrome(options=options)
    
    driver.set_page_load_timeout(45)
    
    url_flow = "https://labs.google/fx/pt/tools/flow" 
    print(f"Acessando: {url_flow}")
    
    try:
        time.sleep(2)
        driver.get(url_flow)
    except Exception as e:
        print("Aviso: O carregamento demorou mais que o esperado, forçando a continuidade...")
    
    return driver

def aguardar_pagina_carregar_e_criar_projeto(driver):
    print("Aguardando a página do Flow carregar e procurando o botão 'Novo Projeto'...")
    
    xpath_novo_projeto = "//button[contains(., 'Novo projeto') or contains(., 'Novo')]"
    
    tentativas = 0
    limite_tentativas = 3
    
    while tentativas < limite_tentativas:
        try:
            botao_novo_projeto = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, xpath_novo_projeto))
            )
            print("Botão 'Novo Projeto' encontrado! Clicando nele...")
            botao_novo_projeto.click()
            time.sleep(3) 
            return True
            
        except Exception as e:
            tentativas += 1
            print(f"⚠️ Tentativa {tentativas}/{limite_tentativas} falhou. O site pode ter engasgado.")
            if tentativas < limite_tentativas:
                print("🔄 Atualizando a página (F5) para tentar novamente...")
                try:
                    driver.refresh()
                    time.sleep(5)
                except:
                    pass
    
    print("❌ Falha crítica: A automação não conseguiu carregar o site corretamente após várias tentativas.")
    return False

def enviar_prompts(driver, lista_de_prompts):
    print("\nIniciando o envio dos prompts...")
    
    ultimo_tempo = None # Variável para lembrar qual foi o último segundo escolhido
    
    for i, prompt in enumerate(lista_de_prompts):
        print(f"\n[{i+1}/{len(lista_de_prompts)}] Processando prompt...")
        
        # --- INÍCIO DA NOVA LÓGICA DE SELEÇÃO DE TEMPO ---
        opcoes_tempo = ["4s", "6s", "8s"]
        
        # Se houver um tempo anterior, remove ele da lista de opções do sorteio atual
        if ultimo_tempo in opcoes_tempo:
            opcoes_tempo.remove(ultimo_tempo)
            
        # Sorteia entre as opções restantes e salva como o último tempo usado
        tempo_escolhido = random.choice(opcoes_tempo)
        ultimo_tempo = tempo_escolhido 
        
        print(f"⏱️ Sorteado vídeo de {tempo_escolhido}. Ajustando configurações...")
        
        try:
            # Encontra o botão principal de Vídeo e rola a tela até ele ficar visível
            xpath_menu = "//button[@aria-haspopup='menu' and (contains(., 'Vídeo') or contains(., 'Video'))]"
            botao_menu = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath_menu))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_menu)
            time.sleep(0.5)
            
            # Tenta clicar de forma natural primeiro, depois força via Javascript
            try:
                botao_menu.click()
            except:
                driver.execute_script("arguments[0].click();", botao_menu)
            
            time.sleep(1.5) # Aguarda a animação do menu abrir completamente
            
            # Localiza a aba correta (4s, 6s ou 8s) dentro do menu aberto
            xpath_segundos = f"//button[@role='tab' and contains(., '{tempo_escolhido}')]"
            botao_tempo = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath_segundos))
            )
            
            # Clica no tempo escolhido
            try:
                botao_tempo.click()
            except:
                driver.execute_script("arguments[0].click();", botao_tempo)
                
            time.sleep(1)
            
            # Fecha o menu de forma nativa usando a tecla ESCAPE
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            print(f"✅ Tempo configurado com sucesso para {tempo_escolhido}!")
            
        except Exception as e:
            print(f"⚠️ Falha ao alterar o tempo (Erro: {type(e).__name__}). Prosseguindo com o tempo padrão...")
        # --- FIM DA NOVA LÓGICA DE SELEÇÃO DE TEMPO ---

        try:
            caixa_texto = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[role='textbox']"))
            )
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", caixa_texto)
            time.sleep(1) 
            
            try:
                caixa_texto.click()
            except:
                driver.execute_script("arguments[0].click();", caixa_texto)
            
            time.sleep(0.5)
            
            # Limpa o campo antes de inserir o novo prompt
            acoes = ActionChains(driver)
            acoes.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL) 
            acoes.send_keys(Keys.BACKSPACE) 
            acoes.perform() 
            time.sleep(0.5)
            
            # Lógica de inserção via ActionChains
            acoes_texto = ActionChains(driver)
            acoes_texto.send_keys(prompt)
            acoes_texto.send_keys(" ") # Gatilho para o site ver que digitamos algo
            acoes_texto.perform()
            time.sleep(1.5) 
            
            # Tenta enviar
            try:
                caixa_texto.send_keys(Keys.CONTROL, Keys.ENTER)
            except:
                botao_enviar = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Send') or contains(@aria-label, 'Enviar') or @type='submit']")
                driver.execute_script("arguments[0].click();", botao_enviar)
            
            print("✅ Prompt inserido e enviado! Aguardando 7 segundos...")
            time.sleep(7)
            
        except Exception as e:
            print(f"❌ Erro ao tentar enviar o prompt. Pulando para o próximo.")
            print(f"Detalhe do erro: {type(e).__name__} - Falha ao interagir com o textbox.")

if __name__ == "__main__":
    print("="*40)
    print("🤖 AUTOMATIZADOR GOOGLE FLOW")
    print("="*40)
    
    lista_de_prompts = carregar_prompts()
    
    if len(lista_de_prompts) > 0:
        driver = iniciar_navegador()
        
        if aguardar_pagina_carregar_e_criar_projeto(driver):
            
            # ---- PAUSA MANUAL PARA O USUÁRIO ----
            print("\n" + "="*50)
            print("🛑 PAUSA MANUAL - AÇÃO NECESSÁRIA")
            print("="*50)
            print("1. Vá até a janela do navegador aberta pela automação.")
            print("2. Selecione se você quer Vídeo ou Imagem.")
            print("3. Escolha o Modelo desejado, ative o Agente e configure a quantidade se necessário.")
            print("4. Volte aqui neste terminal e pressione [ENTER] para continuar.")
            input("\nPressione [ENTER] quando estiver pronto...")
            print("="*50 + "\n")
            
            # ---- RETOMADA DA AUTOMAÇÃO ----
            enviar_prompts(driver, lista_de_prompts)
            
            print("\n✅ Todos os prompts foram enviados para a fila!")
            input("\nPressione [ENTER] no teclado para fechar o navegador e encerrar a automação...")
        
        print("Fechando o navegador...")
        driver.quit()
    else:
        print("Adicione prompts no arquivo de texto e rode novamente.")