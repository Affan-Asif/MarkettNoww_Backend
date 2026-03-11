from groq import Groq
import os

# =============================
# CONFIG
# =============================

GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

# =============================
# GENERATE SCRIPT
# =============================

def generate_script(prompt):

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": """
You are a professional YouTube content creator.

Generate:

1 Viral YouTube Title
2 Hook
3 Full YouTube Script
4 YouTube Description
5 YouTube Tags

Rules:
• Hook must grab attention in 5 seconds
• Script should be engaging
• Use storytelling
• Keep paragraphs short
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return chat.choices[0].message.content


# =============================
# SAVE SCRIPT
# =============================

def save_script(script):

    if not os.path.exists("youtube_scripts"):
        os.makedirs("youtube_scripts")

    filename = "youtube_scripts/script.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(script)

    print("\n Script saved:", filename)


# =============================
# MAIN PROGRAM
# =============================

print("\n===== YOUTUBE SCRIPT AI GENERATOR =====\n")

prompt = input("Enter your YouTube video idea:\n> ")

script = generate_script(prompt)

while True:

    print("\nGenerated Script\n")
    print("------------------------------------------------\n")
    print(script)
    print("\n------------------------------------------------")

    choice = input(
        "\nOptions:\n"
        "1 Approve Script\n"
        "2 Improve Script\n"
        "3 New Script\n"
        "Choice: "
    )

    if choice == "1":

        save_script(script)
        print("\n Script generation completed.\n")
        break

    elif choice == "2":

        feedback = input("\nWhat should AI improve?\n> ")

        script = generate_script(
            f"{prompt}\n\nImprove this script based on feedback:\n{feedback}"
        )

    elif choice == "3":

        prompt = input("\nEnter new video idea:\n> ")
        script = generate_script(prompt)

    else:
        print("Invalid choice")