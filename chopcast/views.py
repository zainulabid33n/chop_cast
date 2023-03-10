import os

import openai
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from transformers import AutoTokenizer


tokenizer = AutoTokenizer.from_pretrained("gpt2")
os.environ["TOKENIZERS_PARALLELISM"] = "true"
openai.api_key = "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"
def break_transcript_to_chunks(transcript, chunk_size=2000, overlap=100):
    tokens = tokenizer.encode(transcript)
    num_tokens = len(tokens)
    chunks = []
    for i in range(0, num_tokens, chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(chunk)

    return chunks


def consolidate_transcript(transcript):
    prompt_response = []
    chunks = break_transcript_to_chunks(transcript)

    for i, chunk in enumerate(chunks):
        prompt_request = "do not remove timestamps but other remove unnecessary information from this transcript: " + tokenizer.decode(chunks[i])

        messages = [{"role": "system", "content": "remove unnecessary information"}]    
        messages.append({"role": "user", "content": prompt_request})

        response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=.5,
                max_tokens=1900,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
        )
        prompt_response.append(response["choices"][0]["message"]['content'].strip())
        return prompt_response

def generate_formatted_key_notes(updated_transcript, q_variables):
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": "You are my detail-oriented YouTube social media assistant robot. You respond back with exactly the outputs that I need, nothing more and nothing less."},
            {"role": "user", "content": f"Please review {updated_transcript}. What are the top {q_variables['max_clips']} coherent key moments that can be expressed in a duration a bit less than {q_variables['max_duration']} seconds, that ideally focus on {q_variables['user_prompt']}, before other topics? Please make sure that you don't share any overlapping clips from a timestamp perspective, and that you ignore any variables if empty. Also, for each clip you select, format you answer as follows: Clip N 1. Suggested Clip Title 2. Full clip Timestamps (not exceeding {q_variables['max_duration']} seconds) 3. Total clip duration 4n. Suitable captions for each item in {q_variables['social_platforms']} with a {q_variables['tone']} tone, and emojis. 5. Full clip transcript. all in form of json"},
        ]
    )
    print(response['choices'][0]['message']['content'])
    return response['choices'][0]['message']['content']



class KeyNotesView(APIView):
    # add permission to check if user is authenticated
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        '''
        Get Key Moments from a Transcript.
        '''
        updated_transcript = consolidate_transcript(request.data['transcript'])
        key_notes = generate_formatted_key_notes(updated_transcript, request.data)

        return Response({"key_notes": key_notes}, status=status.HTTP_202_ACCEPTED)
