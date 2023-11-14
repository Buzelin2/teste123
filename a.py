from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import geckodriver_autoinstaller
import os

# Verificar se o geckodriver está instalado e, se não estiver, instalar localmente
geckodriver_path = './geckodriver'

# Configurar o WebDriver para o Firefox
driver = webdriver.Firefox(executable_path=geckodriver_path)

with open("alergia.txt", "w") as output_file:
    with open("input.txt", "r") as input_file:
        for sequence in input_file:
            sequence = sequence.strip()
            
            # Navegar até o site
            driver.get('https://www.ddg-pharmfac.net/AllerTOP/')

            # Encontrar a área de texto e inserir a sequência
            textarea = driver.find_element(By.NAME, "sequence")
            textarea.send_keys(sequence)

            # Encontrar e clicar no botão de envio
            submit_button = driver.find_element(By.XPATH, "//input[@type='image']")
            submit_button.click()

            # Aguardar os resultados estarem prontos e localizar o elemento de resultado
            wait = WebDriverWait(driver, 30)  # Ajuste o tempo limite conforme necessário

            result_xpath = "//h4[contains(text(), 'Your sequence is:')]/following-sibling::h4[1]"
            result_element = wait.until(EC.visibility_of_element_located((By.XPATH, result_xpath)))

            # Extrair o valor do resultado
            result_value = result_element.text

            # Escrever o resultado no arquivo de saída
            # output_file.write(f"Sequence: {sequence}\nResult: {result_value}\n")

# Fechar o navegador
driver.quit()
