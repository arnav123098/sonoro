<h2>Choose LLM provider</h2>
<select bind:value={config.llm.provider}>
    {#each Object.keys(base_urls.llm) as p}
        <option>{toTitleCase(p)}</option>
    {/each}
</select>

<h2>Enter API key</h2>
<input bind:value={config.llm.api_key}>

<br><br>

<h2>Choose STT provider</h2>
<select bind:value={config.stt.provider}>
    {#each Object.keys(base_urls.stt) as p}
        <option>{toTitleCase(p)}</option>
    {/each}
</select>

<h2>Enter API key</h2>
<input bind:value={config.stt.api_key}>

<br><br>

<h2>Choose TTS provider</h2>
<select bind:value={config.tts.provider}>
    {#each tts as p}
        <option>{toTitleCase(p)}</option>
    {/each}
</select>
<br><br>
<hr>
<br>
<button onclick={handleProviderConfigSave}>Continue</button>

<br><br>

<script>
    import { globals, toTitleCase } from '$lib/index.svelte.js';

    let { setConfig } = $props();

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

    const tts = ['Kyutai Pocket TTS', 'F5 TTS (Gradio)'];

    const providers = {};
    Object.keys(base_urls).forEach(k => {
        providers[k] = {};
        Object.keys(base_urls[k]).forEach(p => {
            providers[k][base_urls[k][p]] = p
        });
    });

    let config = $state({
        llm: {provider: toTitleCase(providers.llm[globals.config?.llm?.base_url]), api_key: globals.config?.llm?.api_key},
        stt: {provider: toTitleCase(providers.stt[globals.config?.stt?.base_url]), api_key: globals.config?.stt?.api_key},
        tts: {provider: 'Kyutai Pocket TTS'}
    });

    const handleProviderConfigSave = () => {
        const provider_config = {};

        Object.keys(config).forEach(key => {
            const val = config[key];

            if (key != 'tts') {
                if (!val.provider || !val.api_key) {
                    return;
                }
            } else {
                if (!val.provider) {
                    return
                }
            }

            if (key != 'tts') {
                provider_config[key] = {
                    base_url: base_urls[key][val.provider.toLowerCase()],
                    api_key: val.api_key
                }
            } else {
                provider_config[key] = config.tts;
            }
        });

        setConfig('llm', provider_config.llm, false);
        setConfig('stt', provider_config.stt, false);
        setConfig('tts', provider_config.tts)
    }
</script>
