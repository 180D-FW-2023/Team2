from openai import OpenAI
import csv

# process cvs string
object_detect_str = ""
with open('pet_video_captin_report_2024-02-03.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in spamreader:
        object_detect_str += ' '.join(row) + '\n'
        #print(', '.join(row))

print(object_detect_str)

# opencv request

client = OpenAI(api_key="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")

response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {
      "role": "system",
      "content": "Summarize content you are provided with in specific time and date in 1 sentence."
    },
    {
      "role": "user",
      "content": object_detect_str
    }
  ],
  temperature=0.5,
  max_tokens=200,
  top_p=1
)

print(response)
print(response.choices[0].message.content)