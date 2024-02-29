from openai import OpenAI
from datetime import date
import os
import csv


def generate_summary(csv_path):

  # process cvs string
  object_detect_str = ""
  with open(csv_path, newline='') as csvfile:
      spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
      for row in spamreader:
          object_detect_str += ' '.join(row) + '\n'
          #print(', '.join(row))

  # opencv request
  key = os.environ["OPENAI_API_KEY"]

  client = OpenAI(api_key=key)

  response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {
        "role": "system",
        "content": "Can you give a warm, summarized and concise report for pet owners, telling them the main activities of the pets throughout the day, in 5-10 bullet points and tone it down. Please do not give specific time."
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

  return response.choices[0].message.content

print(generate_summary("pet_video_captin_report_2024-02-27.csv"))