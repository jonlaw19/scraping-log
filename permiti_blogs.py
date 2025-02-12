import openai
import json

# Set up OpenAI API key
openai.api_key = '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'

# Function to generate blog topics
def generate_blog_topics(prompt, num_topics):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for brainstorming very specific and niche blog topics."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        topics = response.choices[0].message.content.split("\n")
        return topics[:num_topics]
    except Exception as e:
        print("Error: ", e)
        return []

# Function to generate a blog article based on a topic
def generate_blog_article(topic):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a skilled blog writer specialized in commercial permitting."},
                {"role": "user", "content": f"Write a detailed blog article (500-2000 words) on the following topic: {topic}"}
            ],
            max_tokens=3000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Error: ", e)
        return ""

# Generate topics and articles, and save them to a file
if __name__ == "__main__":
    num_articles = int(input("Enter the number of articles (25-100): "))
    if num_articles < 25 or num_articles > 100:
        print("Please enter a number between 25 and 100.")
        exit()

    topic_prompt = (
        f"Generate a list of {num_articles} very specific and niche blog topics about commercial permitting. "
        "Each topic should be suitable for a 500-2000 word article."
    )

    print("Generating topics...")
    blog_topics = generate_blog_topics(topic_prompt, num_articles)

    if blog_topics:
        output_filename = "blog_articles.txt"
        with open(output_filename, "w") as f:
            for i, topic in enumerate(blog_topics):
                print(f"Writing article {i + 1} on topic: {topic}")
                article = generate_blog_article(topic)
                f.write(f"Topic: {topic}\n\n{article}\n\n{'='*80}\n\n")

        print(f"Generated {num_articles} articles and saved them to {output_filename}.")
    else:
        print("No topics were generated.")
