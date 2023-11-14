from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

# Constants
ALLERTOP_URL = "https://www.ddg-pharmfac.net/AllerTOP/"
DEEPSOLUE_URL = "http://39.100.246.211:10505/DeepSoluE/"
PROTEINSOL_URL = "https://protein-sol.manchester.ac.uk/"
PROTPARAM_URL = "https://web.expasy.org/protparam"
TOXINPRED_URL = "https://webs.iiitd.edu.in/raghava/toxinpred/protein.php"
ALLERTOP_RESULT_FILE_PATH = "results/AllerTOP_results.txt"
DEEPSOLUE_RESULT_FILE_PATH = "results/DeepSoluE_results.txt"
PROTEINSOL_RESULT_FILE_PATH = "results/ProteinSol_results.txt"
PROTPARAM_RESULT_FILE_PATH = "results/ProtParam_results.txt"
TOXINPRED_RESULT_FILE_PATH = "results/ToxinPred_results.txt"
FAILED_SEQ_FILE_PATH = "results/failed_sequences.txt"
SUCCESSFUL_SEQ_FILE_PATH = "results/successful_sequences.txt"
PROTEIN_SEQ_FILE = "protein_sequences.txt"
RESULTS_DIR = "results"
LOG_FILE = 'errors.log'

# Set up logging
logging.basicConfig(filename=LOG_FILE, filemode='w', format='%(name)s %(message)s')

def read_chunks(file, chunk_size=100):
    while True:
        lines = [next(file) for _ in range(chunk_size)]
        if not lines:
            break
        yield lines

def process_protparam(driver, sequence, index):
    try:
        driver.get(PROTPARAM_URL)

        # Find and fill the input area
        input_area = driver.find_element(By.NAME, "sequence")
        input_area.clear()
        input_area.send_keys(sequence)

        # Submit the form
        compute_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Compute parameters']")
        compute_button.click()

        # Wait for the page to load
        driver.implicitly_wait(20)

        # Extract values from the page source
        page_text = driver.page_source
        extracted_value, is_stable = extract_values_from_protparam(page_text)

        # Write results to file
        with open(PROTPARAM_RESULT_FILE_PATH, "a") as f:
            # f.write(f"{index}, {sequence}, {extracted_value}, {str(is_stable)}\n")

        return is_stable, (1 - float(extracted_value)/100)

    except Exception as e:
        logging.error(f"Error in ProtParam for sequence {index}: {e}")

def extract_values_from_protparam(page_text):
    try:
        text_before_value = "is computed to be "
        text_after_value = "\nThis"
        value_start_index = page_text.index(text_before_value) + len(text_before_value)
        value_end_index = page_text.index(text_after_value, value_start_index)
        extracted_value = page_text[value_start_index:value_end_index]

        text_before_stability = "classifies the protein as "
        text_after_stability = "."
        stability_start_index = page_text.index(text_before_stability) + len(text_before_stability)
        stability_end_index = page_text.index(text_after_stability, stability_start_index)
        extracted_stability = page_text[stability_start_index:stability_end_index]

        is_stable = "stable" in extracted_stability.lower()
        return extracted_value, is_stable

    except ValueError as e:
        logging.error(f"Error in extracting values: {e}")
        return None, False

def process_toxinpred(driver, sequence, index):
    try:
        driver.get(TOXINPRED_URL)
        
        # Wait for any element obscuring the submit button to disappear
        WebDriverWait(driver, 2).until(EC.invisibility_of_element_located((By.XPATH, "//element_that_obscures_submit_button")))
        
        textarea = driver.find_element(By.ID, "input_box")
        textarea.clear()
        textarea.send_keys(sequence)
        
        # Use JavaScript to click the submit button
        submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        driver.execute_script("arguments[0].click();", submit_button)

        # Wait for results
        is_not_toxic = True
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, "tableTwo")))
        
        for i in range(10):  # Adjust the range as needed
            rows = driver.find_elements(By.XPATH, "//table[@id='tableTwo']/tbody/tr")
            for row in rows:
                prediction = row.find_elements(By.TAG_NAME, "td")[2].text
                if prediction.lower() == "toxin":
                    is_not_toxic = False
                    break
            if not is_not_toxic:
                break

            # Find the next button and use JavaScript to scroll it into view and click it
            next_button = driver.find_element(By.XPATH, "//img[@class='next']")
            driver.execute_script("arguments[0].scrollIntoView();", next_button)
            driver.execute_script("arguments[0].click();", next_button)

        # Write result to file
        with open(TOXINPRED_RESULT_FILE_PATH, "a") as f:
            f.write(f"{index}, {sequence}, {is_not_toxic}\n")

        return is_not_toxic

    except Exception as e:
        logging.error(f"Error in ToxinPred for sequence {index}: {e}")


  
def process_allertop(driver, sequence, index):
    try:
        driver.get(ALLERTOP_URL)

        # Find and fill the textarea
        textarea = driver.find_element(By.NAME, "sequence")
        textarea.clear()
        textarea.send_keys(sequence)

        # Submit the form
        submit_button = driver.find_element(By.XPATH, "//input[@type='image']")
        submit_button.click()

        # Wait for the results
        
        result_xpath = "//h4[contains(text(), 'Your sequence is:')]/following-sibling::h4[1]"
        result_element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, result_xpath)))
        not_alergenic = "NON" in result_element.text.upper()

        # Extract and write the result
        with open(ALLERTOP_RESULT_FILE_PATH, "a") as f:
            f.write(f"{index}, {sequence}, {not_alergenic}\n")
            
        return not_alergenic

    except Exception as e:
        logging.error(f"Error in AllerTOP for sequence {index}: {e}")
 

def process_proteinsol(driver, sequence, index):
    try:
        # Navigate to the website
        driver.get(PROTEINSOL_URL)

        # Find the textarea and input the sequence
        textarea = driver.find_element(By.ID, "fastaInputBox")
        textarea.send_keys(sequence)

        # Find and click the submit button
        submit_button = driver.find_element(By.ID, "sequence-button")
        submit_button.click()

        # XPath to find the <p> tag that immediately follows the <h5> with the specific text
        result_xpath = "//h5[contains(text(), 'Predicted scaled solubility:')]/following-sibling::p"
        result_element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, result_xpath)))

        # Extract the result value
        result_value = result_element.text
        is_soluble = float(result_value) >= 0.45

        # Write results to file
        with open(PROTEINSOL_RESULT_FILE_PATH, "a") as f:
            f.write(f"{index}, {sequence}, {result_value}, {is_soluble}\n")
            
        return is_soluble, float(result_value)
            
    except Exception as e:
        logging.error(f"Error in ProteinSol for sequence {index}: {e}")

def process_sequence(sequence, index):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=chrome_options)

        # DeepSoluE
        continue_process, output_score = process_proteinsol(driver, sequence, index)
        protein_score = output_score if continue_process else 0.0

        if not continue_process:
            with open(FAILED_SEQ_FILE_PATH, "a") as f:
                f.write(f"{index}, {sequence}, ProteinSol\n")

        # AllerTOP
        continue_process = process_allertop(driver, sequence, index)

        if not continue_process:
            with open(FAILED_SEQ_FILE_PATH, "a") as f:
                f.write(f"{index}, {sequence}, AllerTOP\n")

        # ProtParam
        continue_process, output_score = process_protparam(driver, sequence, index)
        protein_score *= output_score if continue_process else 0.0

        if not continue_process:
            with open(FAILED_SEQ_FILE_PATH, "a") as f:
                f.write(f"{index}, {sequence}, ProtParam\n")

        # # ToxinPred
        # continue_process = process_toxinpred(driver, sequence, index)

        # if not continue_process:
        #     with open(FAILED_SEQ_FILE_PATH, "a") as f:
        #         f.write(f"{index}, {sequence}, ToxinPred\n")

        # Write successful sequences to file
        if protein_score > 0.0:
            with open(SUCCESSFUL_SEQ_FILE_PATH, "a") as f:
                f.write(f"{index}, {sequence}, {protein_score}\n")

        driver.quit()

    except Exception as e:
        logging.error(f"Error for sequence {index}: {e}")

def main():
    try:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        global_index = 1

        with open(PROTEIN_SEQ_FILE, "r") as file:
            sequences = [sequence.strip() for sequence in file if sequence.strip()]
        
        with ThreadPoolExecutor(max_workers=16) as executor:
            for sequence in sequences:
                executor.submit(process_sequence, sequence, global_index)
                global_index += 1

    except Exception as e:
        logging.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()

