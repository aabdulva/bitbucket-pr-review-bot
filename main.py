from flask import Flask, request, jsonify
import openai, os, requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME")
BITBUCKET_APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD")

@app.route("/", methods=["GET"])
def home():
    return "Bitbucket PR Review Bot Running"

@app.route("/pr-webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    print("Webhook received:", data)
    try:
        pr = data['pullrequest']
        repo = data['repository']
        pr_id = pr['id']
        repo_slug = repo['full_name']
        source_branch = pr['source']['branch']['name']

        diff_url = pr['links']['diff']['href']
        print(f"PR #{pr_id} in repo {repo_slug}, branch {source_branch}")

        # Fetch PR diff
        resp = requests.get(diff_url, auth=(BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD))
        diff_text = resp.text[:5000]  # Truncate if large

        # Call OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a code reviewer."},
                {"role": "user", "content": f"Review this PR diff:\n{diff_text}"}
            ]
        )

        review_comment = response['choices'][0]['message']['content']
        print("AI Review:", review_comment)

        # Post comment to Bitbucket PR
        comment_url = f"https://api.bitbucket.org/2.0/repositories/{repo_slug}/pullrequests/{pr_id}/comments"
        requests.post(comment_url,
                      auth=(BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD),
                      json={"content": {"raw": review_comment}})

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
