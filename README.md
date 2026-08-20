![banner](https://github.com/arnav123098/sonoro/blob/main/banner.png)

---
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
  py -m venv .venv # create a virtual environment
  .venv/Scripts/activate # activate the venv
  pip install -r requirements.txt
```

Run bun install in sonoro/ui (for now, the web ui runs on port 5173).
From the project root, run the commands -
```
  cd sonoro/ui
  bun i # make sure you have bun installed
```

## Usage (in development mode)
Open up two terminals in project root, activate venv and run.
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

Recommended LLM for best experience: Llama 70B or a Qwen 27B

Or create a directory for your character in project/characters and get the models and voicelines in there.
(ps: i'll make a guide soon! i promise...)

As an example, I have Yinlin from Wuthering Waves in my sonoro.

![Yinlin example](https://github.com/arnav123098/sonoro/blob/main/example.png)

## ⚠️ Alpha software
Sonoro is currently in early development. APIs, configuration, installation steps, and features may change frequently. Things will probably break.

## Sonoro TUI and SDK (on the way)
Soon, you'll be able to use sonoro externally as a tool for letting your ai use a 3D model, voice and web search/scrape, song playing etc.
A terminal interface is in the making too.

## TODOS
- [x] music player tool (not in the repo version for now)
- [x] handle guardrails (marking complete cuz i haven't seen it break on anything for now; didn't test Llama 70B though)
- [ ] tui
- [ ] settings ui
- [ ] better character maker interface + convo examples
- [ ] streamed response and chunk-wise tts generation to mask latency
- [ ] reference voice and better tts (potentially F5 TTS)
- [ ] character walks from screen to screen
---
