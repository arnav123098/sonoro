<h1>Choose LLM</h1>
<select bind:value={config.llm}>
    {#each models.llm as model}
        <option>{model}</option>
    {/each}
</select>

<hr>

<h1>Choose STT</h1>
<select bind:value={config.stt}>
    {#each models.stt as model}
        <option>{model}</option>
    {/each}
</select>

<button onclick={() => {
    if (!config.llm || !config.stt) return;
    setConfig('llm.model', config.llm, false);
    setConfig('stt.model', config.stt);
}}>Continue</button>

<script>
    import { onMount } from 'svelte';
    import { globals } from '$lib/index.svelte.js';

    let { setConfig } = $props();

    let config = $state({
        llm: globals.config?.llm?.model,
        stt: globals.config?.stt?.model
    });

    let models = $state({
        llm: null,
        stt: null
    });

    const handleListModels = async (data) => {
        models.llm = data.llm;
        models.stt = data.stt;
    }

    onMount(async () => {
        globals.conn.on('listModels', handleListModels);
        globals.conn.emit('getModels');
    });
</script>
