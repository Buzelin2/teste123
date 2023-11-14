from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import geckodriver_autoinstaller

# Instalar o geckodriver automaticamente, se necessário
geckodriver_autoinstaller.install()

# Configurar o WebDriver para o Firefox
driver = webdriver.Firefox()
with open("alergia.txt", "w") as output_file:
    with open("input.txt", "r") as input_file:
        for sequence in input_file:
            sequence = sequence.strip()
            
            # Navigate to the website
            driver.get('https://www.ddg-pharmfac.net/AllerTOP/')

            # Find the textarea and input the sequence
            textarea = driver.find_element(By.NAME, "sequence")
            textarea.send_keys(sequence)

            # Find and click the submit button
            submit_button = driver.find_element(By.XPATH, "//input[@type='image']")
            submit_button.click()

            # Wait for the results to be ready and locate the result element
            wait = WebDriverWait(driver, 30)  # Adjust timeout as needed

            result_xpath = "//h4[contains(text(), 'Your sequence is:')]/following-sibling::h4[1]"
            result_element = wait.until(EC.visibility_of_element_located((By.XPATH, result_xpath)))

            # Extract the result value
            result_value = result_element.text

            # Write the result to the output file
            # output_file.write(f"Sequence: {sequence}\nResult: {result_value}")  # Corrected this line

# Close the browser
driver.quit()
