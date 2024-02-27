![Logo](logo.png)

## Project

This is a quick and dirty 

## What it does

LaVague provides a voice interface to surf the internet by turning natural language commands into browser interaction

## How we built it

- Continuous audio stream listening
- When audio is above threshold we send audio to a Whisper model for transcription of the voice command
- We then send the current HTML page + voice command to Llama index to generate a prompt
- Prompt is enhanced by Few-Shot learning and Chain of Thought. Prompt engineering is automated with DSPy.
- We send the prompt to model hosted by Fireworks
- We receive code to execute on the selenium controlled browser

## Challenges we ran into

Poor retriever for HTML, which means chunks are not well split, which makes it hard to have a good generation.

## Accomplishments that we're proud of

Well it's cool and it works and it's non trivial

## What's next for LaVague

Thinking of open sourcing and let the community improve it and help build together the future of internet interaction.
