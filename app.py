from flask import Flask, render_template, request
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in .env file")

client = OpenAI(api_key=api_key)
app = Flask(__name__)
#Chatbot memory
tasks =[]
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/rule-based", methods=['GET', 'POST'])
def rule_based():
    response = ""

    if request.method == 'POST':
        user_input = request.form["user_input"].lower()

        #Rule 1: Add task
        if "add" in user_input:
            task = user_input.replace("add","").strip()
            tasks.append(task)
            response = f"Task added: {task}"

        #Rule 2: Show tasks
        elif "show" in user_input or "list" in user_input:
            response = "Tasks: "+", ".join(tasks) if tasks else "No tasks found."

        #Rule 3: Delete task
        elif "delete" in user_input:
            task = user_input.replace("delete", "").strip()
            if task in tasks:
                tasks.remove(task)
                response = f"Deleted task: {task}"
            else:
                response = "Task not found."

        else:
            response = "Sorry, I only understand: add, show, delete."

    return render_template('rule_based.html',response=response)


@app.route('/llm', methods=['GET', 'POST'])
def llm():
    response = ""
    if request.method == 'POST':
        user_input = request.form["user_input"]

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful AI chatbot."},
                    {"role": "user", "content": user_input}
                ]
            )
            response = completion.choices[0].message.content
        except Exception as e:
            response = f"Error: {str(e)}"
    return render_template('llm_chat.html', response=response)

#helper function
def load_documents():
    with open("rag_data/docs.txt", "r") as f:
        return f.read().split("\n")

#
def retrieve_context(user_input, documents):
    results = []
    for doc in documents:
        if user_input.lower() in doc.lower():
            results.append(doc)
    return results

@app.route('/rag', methods=['GET', 'POST'])
@app.route('/rag', methods=['GET', 'POST'])
def rag():
    response = ""

    if request.method == 'POST':
        user_input = request.form["user_input"]

        documents = load_documents()
        context = retrieve_context(user_input, documents)

        context_text = "\n".join(context) if context else "No relevant data found."

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Answer ONLY from the provided context."},
                    {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {user_input}"}
                ]
            )

            response = completion.choices[0].message.content

        except Exception as e:
            response = f"Error: {str(e)}"

    return render_template('rag_chat.html', response=response)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)