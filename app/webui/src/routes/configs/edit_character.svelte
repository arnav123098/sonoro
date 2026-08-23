{#if config}
    <h2>Name</h2>
    <input bind:value={config.name}>
    <br><br>

    <h2>Upload assets</h2>
    <br><br>
    <input
        type="file"
        accept={accept}
        multiple
        bind:files={assets}
        bind:this={assetInput}
        id='file-input'
    />
    <br>
    <button onclick={uploadAssets}>Upload</button>
    <br><br><br>

    <h2>PFP</h2>
    <select bind:value={config.pfp}>
        <option value={null}>default</option>
        {#each images as img}
            <option>{img}</option>
        {/each}
    </select>
        {#if config.pfp}
            <button onclick={() => deleteAsset(config.pfp, 'images')}>delete</button>
        {/if}
    <br><br>

    <h2>Chat Background</h2>
    <select bind:value={config.theme.chat_background}>
        <option value={null}>default</option>
        {#each images as img}
            <option>{img}</option>
        {/each}
        {#if config.theme.chat_background}
            <button onclick={() => deleteAsset(config.theme.chat_background, 'images')}>delete</button>
        {/if}
    </select>

    <h1>Description</h1>
    <textarea bind:value={config.description}></textarea>
    <br><br>
    <button onclick={() => genDescBoxVisible = !genDescBoxVisible}>use ai to write description</button>

    {#if genDescBoxVisible}
        <br><br>
        <textarea bind:value={genDescInput}>
            Enter url of a page or some text about the character
        </textarea>
        <br>
        <select bind:value={genDescInputType}>
            <option>url</option>
            <option>text</option>
        </select>
        <br><br>
        <button onclick={generateDesc}>generate description</button>
    {/if}

    <h1>Background Lore</h1>
    <textarea bind:value={config.background_lore}></textarea>

    <h1>Select Model</h1>
    <h2>Path</h2>
    <select bind:value={config.vrm_model}>
        {#each vrm_models as path}
            <option>{path}</option>
        {/each}
    </select>
        {#if config.vrm_model}
            <button onclick={() => deleteAsset(config.vrm_model, 'models')}>delete</button>
        {/if}
    <br>

    <h1>Voicelines for different expressions</h1>
    {#each Object.keys(config.expression_to_voice) as exp}
        <h2>{exp}{exp === 'neutral' ? '*' : ''}</h2>
        <select bind:value={config.expression_to_voice[exp]}>
            {#each voicelines as path}
                <option>{path}</option>
            {/each}
        </select>
        {#if config.expression_to_voice[exp]}
            <button onclick={() => deleteAsset(config.expression_to_voice[exp], 'voicelines')}>delete</button>
        {/if}
        <br>
    {/each}
    <hr>

    <br>
    <button onclick={deleteCharacter}>Delete Character</button>
    
    <button onclick={handleSaveCharacter}>Save Character</button>

    <br><br>
{/if}

<script>
    import { globals } from "$lib/index.svelte";
    import { onMount } from "svelte";

    let { character } = $props();

    let images = $state();
    let vrm_models = $state();
    let voicelines = $state();

    let genDescBoxVisible = $state(false);
    let genDescInput = $state('');
    let genDescInputType = $state('');

    let config = $state();

    let assets = $state();
    let assetInput = $state();

    const assetFormats = {
        models: ['vrm'],
        voicelines: ['wav', 'ogg'],
        images: ['png' , 'jpg', 'jpeg', 'webp']
    };
    const accept = Object.values(assetFormats).flat().map(f => `.${f}`).join(',');

    const uploadAssets = () => {
        if (!assets?.length) return;
        const assetArray = Array.from(assets).map(a => ({
            name: a.name,
            type: a.type,
            data: a
        }));
        globals.conn.emit('uploadAssets', character, assetArray);

        assets = null;
        assetInput.value = '';

        setTimeout(() => globals.conn.emit('getCharacterData', character), 500);
    }

    const deleteAsset = (name, type) => {
        const asset = {
            name,
            type
        }

        globals.conn.emit('deleteAsset', character, asset);
        setTimeout(() => globals.conn.emit('getCharacterData', character), 500);
    }

    const deleteCharacter = () => {
        globals.conn.emit('deleteCharacter', character);
        window.location.reload();
    }
    
    const handleLoadCharacterDir = async (data) => {
        console.log('editing character: ', data)
        config = data.config;
        vrm_models = data.vrm_models;
        images = data.images;
        voicelines = data.voicelines;
    };

    const handleSaveCharacter = async () => config.name && config.expression_to_voice.neutral && globals.conn.emit('updateCharacter', config.name, config);
    const handleSavedCharacterSuccess = async () => window.location.reload();

    const generateDesc = () => {
        if (!genDescInput || !genDescInputType) return;
        globals.conn.emit('getGenDesc', {
            type: genDescInputType,
            data: genDescInput
        });
    };
    const handleGenDesc = async (data) => {
        config.description = data;
        genDescBoxVisible = false;
    };

    onMount(() => {
        globals.conn.on('loadCharacterData', handleLoadCharacterDir);
        globals.conn.on('savedCharacterSuccess', handleSavedCharacterSuccess);
        globals.conn.on('genDesc', handleGenDesc);

        return () => {
            globals.conn.off('loadCharacterData', handleLoadCharacterDir);
            globals.conn.off('savedCharacterSuccess', handleSavedCharacterSuccess);
            globals.conn.off('genDesc', handleGenDesc)
        }
    });

    $effect(() => character && globals.conn.emit('getCharacterData', character));
</script>

<style>
    h1 {
        font-size: 1.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    h2 {
        font-size: 1rem;
        display: inline;
        margin-right: 1rem;
    }

    :global(select) {
        border-radius: 16px;
        border: solid 1px rgb(0, 140, 255);
    }

    option {
        color: black;
    }

    textarea {
        height: 10rem;
        width: 80%;
        padding: 1rem;
        border-radius: 10px;
    }

    input, textarea, button {
        border: solid 1px rgb(0, 140, 255);
        color: white;
    }

    input, textarea, :global(select) {
        background-color: rgba(255, 255, 255, 0.1);
    }

    hr {
        margin: 2rem;
    }
</style>
