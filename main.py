import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import re
import winreg

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

# ==========================================
# FUNÇÃO SIMPLIFICADA: APENAS CLICAR NO AGENTE
# ==========================================
def ativar_agente(driver):
    print("\nProcurando o botão 'Agente'...")
    try:
        # Localiza a div que contém o span com o texto "Agente"
        xpath_agente = "//div[span[@class='content' and text()='Agente']]"
        
        botao_agente = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, xpath_agente))
        )
        
        print("✅ Botão 'Agente' encontrado! Clicando nele...")
        botao_agente.click()
        time.sleep(2) # Tempo para o site registrar o clique e a janela abrir/atualizar
            
    except Exception as e:
        print("⚠️ Botão 'Agente' não encontrado na tela. A automação continuará normalmente.")

def configurar_tipo_e_modelo(driver, tipo_escolhido, modelo_escolhido):
    """Navega pelos menus para selecionar se é Imagem ou Vídeo e escolhe o modelo correto"""
    print(f"\n⚙️ Configurando o estúdio para: {tipo_escolhido.upper()} | Modelo: {modelo_escolhido}")
    
    try:
        aba_xpath = f"//button[@role='tab' and contains(., '{tipo_escolhido}')]"
        try:
            botao_aba = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, aba_xpath)))
            
            estado = botao_aba.get_attribute("data-state")
            if estado != "active":
                print(f"Clicando na aba de {tipo_escolhido}...")
                botao_aba.click()
                time.sleep(2)
            else:
                print(f"Aba de {tipo_escolhido} já estava selecionada.")
                
        except:
            print("Aba direta não encontrada, tentando abrir o menu principal...")
            botao_menu_principal = driver.find_element(By.XPATH, "//button[@aria-haspopup='menu' and (contains(., 'Vídeo') or contains(., 'Imagem') or contains(., '🍌'))]")
            botao_menu_principal.click()
            time.sleep(1)
            driver.find_element(By.XPATH, aba_xpath).click()
            time.sleep(2)

        try:
            print("Configurando quantidade para '1x'...")
            botao_1x_xpath = "//button[@role='tab' and text()='1x']"
            botao_1x = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, botao_1x_xpath)))
            
            if botao_1x.get_attribute("data-state") != "active":
                driver.execute_script("arguments[0].click();", botao_1x)
                print("✅ Opção '1x' selecionada com sucesso!")
                time.sleep(1)
            else:
                print("✅ A opção '1x' já estava selecionada.")
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível definir a opção para '1x'. Ela pode estar oculta.")

        dropdown_modelo_xpath = "//button[@aria-haspopup='menu' and .//i[text()='arrow_drop_down']]"
        botao_dropdown = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, dropdown_modelo_xpath)))
        
        texto_botao_atual = botao_dropdown.text
        
        if modelo_escolhido in texto_botao_atual:
            print(f"✅ O modelo '{modelo_escolhido}' já está selecionado corretamente!")
        else:
            print(f"Trocando modelo de '{texto_botao_atual.strip()}' para '{modelo_escolhido}'...")
            botao_dropdown.click()
            time.sleep(1)
            
            opcao_modelo_xpath = f"//span[contains(text(), '{modelo_escolhido}')]"
            botao_opcao = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, opcao_modelo_xpath)))
            botao_opcao.click()
            time.sleep(1)
            print(f"✅ Modelo '{modelo_escolhido}' selecionado com sucesso!")
            
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao tentar configurar a aba/modelo: {type(e).__name__}")
        print("Continuando mesmo assim, verifique manualmente se está correto.")
        return False

def enviar_prompts(driver, lista_de_prompts, tipo_escolhido):
    print("\nIniciando o envio dos prompts...")
    
    for i, prompt in enumerate(lista_de_prompts):
        print(f"\n[{i+1}/{len(lista_de_prompts)}] Processando prompt...")
        
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
            
            # Lógica de Tempo Unificada
            if (i + 1) % 5 == 0:
                print("✅ Prompt inserido e enviado!")
                print(f"⏳ Lote de 5 atingido. Pausa de descanso de 40 segundos...")
                time.sleep(40)
            else:
                print("✅ Prompt inserido e enviado! Aguardando 7 segundos...")
                time.sleep(7)
            
        except Exception as e:
            print(f"❌ Erro ao tentar enviar o prompt. Pulando para o próximo.")
            print(f"Detalhe do erro: {type(e).__name__} - Falha ao interagir com o textbox.")

def menu_interativo():
    print("="*40)
    print("🤖 AUTOMATIZADOR GOOGLE FLOW")
    print("="*40)
    print("O que você deseja criar?")
    print("1 - Vídeos")
    print("2 - Imagens")
    
    escolha_tipo = input("\nDigite a opção (1 ou 2): ").strip()
    
    if escolha_tipo == "1":
        tipo = "Vídeo"
        modelo = "Veo 3.1 - Lite [Lower Priority]"
        return tipo, modelo
        
    elif escolha_tipo == "2":
        tipo = "Imagem"
        print("\nQual modelo de imagem você deseja usar?")
        print("1 - Nano Banana 2")
        print("2 - Nano Banana Pro")
        escolha_modelo = input("Digite a opção (1 ou 2): ").strip()
        
        if escolha_modelo == "2":
            modelo = "Nano Banana Pro"
        else:
            modelo = "Nano Banana 2"
            
        return tipo, modelo
        
    else:
        print("Opção inválida. Fechando o programa.")
        exit()

if __name__ == "__main__":
    tipo_escolhido, modelo_escolhido = menu_interativo()
    
    lista_de_prompts = carregar_prompts()
    
    if len(lista_de_prompts) > 0:
        driver = iniciar_navegador()
        
        if aguardar_pagina_carregar_e_criar_projeto(driver):
            
            # ---- CLIQUE NO AGENTE SIMPLIFICADO AQUI ----
            ativar_agente(driver)
            # --------------------------------------------
            
            configurar_tipo_e_modelo(driver, tipo_escolhido, modelo_escolhido)
            
            enviar_prompts(driver, lista_de_prompts, tipo_escolhido)
            
            print("\n✅ Todos os prompts foram enviados para a fila!")
            input("\nPressione [ENTER] no teclado para fechar o navegador e encerrar a automação...")
        
        print("Fechando o navegador...")
        driver.quit()
    else:
        print("Adicione prompts no arquivo de texto e rode novamente.")