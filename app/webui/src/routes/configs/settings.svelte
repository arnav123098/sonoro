<h2>Choose LLM provider</h2>
<select onchange={({target}) => config.llm.base_url = base_urls.llm[target.value.toLowerCase()]}>
    {#each Object.keys(base_urls.llm) as p}
        <option>{toTitleCase(p)}</option>
    {/each}
</select>

<br><br>

<h2>Enter API key</h2>
<input bind:value={config.llm.api_key}>

<button onclick={() => getModels('llm')}>Confirm</button>

<br>

<h2>Choose LLM</h2>
<select bind:value={config.llm.model}>
    {#each models.llm as model}
        <option>{model}</option>
    {/each}
</select>

<br><br>
<hr>
<br>

<h2>Choose STT provider</h2>
<select onchange={({target}) => config.stt.base_url = base_urls.stt[target.value.toLowerCase()]}>
    {#each Object.keys(base_urls.stt) as p}
        <option>{toTitleCase(p)}</option>
    {/each}
</select>

<br><br>

<h2>Enter API key</h2>
<input bind:value={config.stt.api_key}>

<button onclick={() => getModels('stt')}>Confirm</button>

<br>


<h2>Choose STT Model</h2>
<select bind:value={config.stt.model}>
    {#each models.stt as model}
        <option>{model}</option>
    {/each}
</select>

<br><br>
<hr>
<br>

<h2>Choose TTS provider</h2>
<select bind:value={config.tts.provider}>
    {#each tts as p}
        <option>{toTitleCase(p)}</option>
    {/each}
</select>

<br><br>
<hr>
<br>

<h2>Tavily API Key</h2>
<input bind:value={config.tools.web_search.tavily_api_key} />

<h2>ScraperAPI API Key</h2>
<input bind:value={config.tools.web_search.scraper_api_key} />

<br>
<hr>
<br><br>

<button onclick={updateConfig}>Save</button>

<br><br>

<script>
    import { globals, toTitleCase } from '$lib/index.svelte.js';
    import { onMount } from 'svelte';

    let config = $state(globals.config);

    const updateConfig = () => {
        globals.conn.emit('updateConfig', globals.config);
        console.log('updating settings...');
        window.location.reload();
    };

    const base_urls = {
        llm: {  
            groq: "https://api.groq.com/openai/v1",
            openai: "https://api.openai.com/v1",
            openrouter: "https://openrouter.ai/api/v1",
            together: "https://api.together.xyz/v1",
            deepinfra: "https://api.deepinfra.com/v1/openai"
        },
        stt: {
            groq: "https://api.groq.com/openai/v1",
            openai: "https://api.openai.com/v1"
        }
    };
    const tts = ['Kyutai Pocket TTS'];

    let models = $state({
        llm: [],
        stt: []
    });

    const getModels = (type, isAlert = true) => {
        const ready = config[type].base_url && config[type].api_key;

        if (!ready) {
            if (isAlert) window.alert('Please select provider and enter API key to continue');
            return;
        }

        models[type] = [];
        globals.conn.emit('getModels', type, config);
    }

    const handleListModels = ([data, type]) => {
        if (type === 'llm') {
            models.llm = data;
        } else if (type === 'stt') {
            models.stt = data;
        }
    }

    onMount(() => {
        getModels('llm', false);
        getModels('stt', false);

        globals.conn.on('listModels', handleListModels);

        return () => globals.conn.off('listModels', handleListModels);;
    });
</script>

<style>
    hr {
        width: 50%;
    }
</style>
