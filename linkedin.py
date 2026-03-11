import os
import re
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from groq import Groq


# ===============================
# CONFIG
# ===============================

LINKEDIN_EMAIL = "Marketnow.pvt@outlook.com"
LINKEDIN_PASSWORD = "marketnow@777"

GROQ_API_KEY = "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"


# ===============================
# AI CLIENT
# ===============================

client = Groq(api_key=GROQ_API_KEY)


# ===============================
# REMOVE EMOJIS (Fix Selenium Bug)
# ===============================

def remove_emojis(text):
    return re.sub(r'[^\x00-\xFFFF]', '', text)


# ===============================
# GENERATE LINKEDIN POST
# ===============================

def generate_post(prompt):

    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
You are a LinkedIn content expert.

Write a professional LinkedIn post.

Rules:
- Engaging
- Short paragraphs
- Maximum 120 words
- Add call to action
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    text = chat.choices[0].message.content
    text = remove_emojis(text)

    return text

# ===============================
# LINKEDIN LOGIN
# ===============================

def linkedin_login(driver):

    print("Opening LinkedIn login")

    driver.get("https://www.linkedin.com/login")

    time.sleep(3)

    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)

    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    print("Logged in")

    time.sleep(6)


# ===============================
# POST ON LINKEDIN
# ===============================

def post_on_linkedin(post_text):

    print("Starting Chrome")

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    linkedin_login(driver)

    print("Opening create post")

    driver.get("https://www.linkedin.com/feed/")

    time.sleep(6)

    create_post_trigger = driver.find_element(
        By.XPATH,
        "//*[@id='workspace']/div/div/div[2]/div/div[1]/div/div[1]/div/div/div"
    )
    create_post_trigger.click()

    time.sleep(4)

    print("Entering post text")

    # Post editor is inside shadow DOM; use JS path to find and fill it
    post_html = post_text.replace("\n", "<br>")
    driver.execute_script("""
        var root = document.querySelector("#interop-outlet").shadowRoot;
        var el = root.querySelector("#ember62 > div > div.share-creation-state.share-creation-state__share-box-v2.share-creation-state__share-box-v2--redesigned-detours > div.share-creation-state__content-scrollable > div > div > div > div > div > div > div.ql-editor.ql-blank > p");
        if (el) {
            el.focus();
            el.innerHTML = arguments[0];
        }
    """, post_html)

    time.sleep(3)

    print("Clicking POST button")

    driver.execute_script("""
        var root = document.querySelector("#interop-outlet").shadowRoot;
        var btn = root.querySelector("#ember89");
        if (btn) btn.click();
    """)

    print("POST PUBLISHED SUCCESSFULLY")

    time.sleep(6)

    driver.quit()


# ===============================
# MAIN PROGRAM
# ===============================

print("\n===== LINKEDIN AI POST GENERATOR =====\n")

prompt = input("Enter your post idea:\n> ")

post = generate_post(prompt)

while True:

    print("\nGenerated LinkedIn Post:\n")
    print("----------------------------------")
    print(post)
    print("----------------------------------")

    choice = input(
        "\nOptions:\n1 Approve & Post\n2 Improve Post\n3 Edit yourself\nChoice: "
    ).strip()

    if choice == "1":

        print("\nPublishing post...\n")

        post_on_linkedin(post)

        break

    elif choice == "2":

        feedback = input("\nWhat should AI improve?\n> ")

        post = generate_post(
            f"{prompt}\n\nImprove based on feedback:\n{feedback}"
        )

    elif choice == "3":

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(post)
            temp_path = f.name

        print("\nOpening post in your editor. Edit it, save, then close the file.")
        os.startfile(temp_path)
        input("Press Enter when you have finished editing and saved... ")

        with open(temp_path, encoding="utf-8") as f:
            post = f.read().strip()

        try:
            os.unlink(temp_path)
        except OSError:
            pass

        if not post:
            print("Post was cleared. Generating again.")
            post = generate_post(prompt)

    else:

        print("Invalid choice")

