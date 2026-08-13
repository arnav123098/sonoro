![banner](https://github.com/arnav123098/sonoro/blob/main/banner.png)
Sonoro lets you talk to your favorite game or anime characters. You can also make a custom character on your own.

#### Things you need
- 3D model (vrm)
- Voicelines (at least one)

That's it!

## Installation (ps: it's not completed and i'm lazy so i'm not setting up serving web ui from python anytime too soon!)
Clone the repo
```
  git clone https://github.com/arnav123098/sonoro project
  cd project
```

Install Python packages
```
  cd sonoro/engine
  pip install -r requirements.txt
```

Run bun install in sonoro/ui (for now, the web ui runs on port 5173).
From the project root, run the commands -
```
  cd sonoro/ui
  bun i # make sure you have bun installed
```

## Usage (in development mode)
Open up two terminals in project root and run.
```
  # in terminal 1
  cd sonoro/engine
  python -m chat

  # in terminal 2
  cd sonoro/ui
  bun dev
```

Just head to http://localhost:5173 in your browser to use it.
For starters, you can try chatting with A-chan, the default character.

You have to use your own API keys for the providers you'll be using for LLM, STT, TTS (only Kyutai Pocket TTS works for now) and for Tavily and ScraperAPI for web search and scraping tool.
Personally, I've tested it with Groq (free tier btw).

Or create a directory for your character in project/characters and get the models and voicelines in there.
(ps: i'll make a guide soon! i promise...)

As an example, I have Yinlin from Wuthering Waves in my sonoro.

![Yinlin example](https://github.com/arnav123098/sonoro/blob/main/example.png)

## ⚠️ Alpha software
Sonoro is currently in early development. APIs, configuration, installation steps, and features may change frequently. Things will probably break.

## TODOS
- [ ] gltf support (if i won't be a sloth, that is)
- [ ] add more built-in animations
- [ ] convo examples
- [ ] reference voice and better tts (potentially F5 TTS)
- [ ] streamed response and chunk-wise tts generation to mask latency 
- [ ] handle guardrails

---
