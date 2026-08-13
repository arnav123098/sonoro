<h2>Name</h2>
<input bind:value={config.name}>
<br>

<h2>PFP (optional)</h2>
<select bind:value={config.pfp}>
    {#each pfps as pfp}
        <option>{pfp}</option>
    {/each}
</select>

<h1>Description (optional)</h1>
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

<h1>Background Lore (optional)</h1>
<textarea bind:value={config.background_lore}></textarea>

<h1>Select Model</h1>
<h2>Path</h2>
<select bind:value={config.model_path}>
    {#each model_paths as p}
        <option>{p}</option>
    {/each}
</select>
<br>
<h2>Type (only vrm supported for now)</h2>
<select bind:value={config.model_type}>
    <option selected={config.model_type === 'gltf'}>gltf</option>
    <option selected={config.model_type === 'vrm'}>vrm</option>
</select>

<h1>Voicelines for different expressions (neutral is required)</h1>
{#each expressions as exp}
    <h2>{exp}</h2>
    <select bind:value={config.expression_to_voice[exp]}>
        {#each voiceline_paths as path}
            <option>{path}</option>
        {/each}
    </select>
    <br>
{/each}
<hr>

<button onclick={handleSaveCharacter}>Save Character</button>

<br><br>

<script>
    import { globals } from "$lib/index.svelte";
    import { onMount } from "svelte";

    let { character_dir } = $props();

    let pfps = $state();
    let model_paths = $state();
    let voiceline_paths = $state();

    let genDescBoxVisible = $state(false);
    let genDescInput = $state('');
    let genDescInputType = $state('');

    const expressions = ['neutral', 'happy', 'sad', 'angry', 'embarrassed', 'excited']

    let config = $state({
        // 3D
        model_path: null,
        model_type: null,

        // Voice
        expression_to_voice: {}, // {expression: voiceline...}

        // Lore
        name: null,
        description: null,
        background_lore: null,

        pfp: null
    });

    const requiredConfigs = ['model_path', 'model_type', 'name', 'expression_to_voice']
    
    const handleLoadCharacterDir = async (data) => {
        model_paths = data.model_paths;
        if (model_paths && !data.config.model_path) data.config.model_path = model_paths[0];

        pfps = data.pfps;
        if (pfps && !data.config.pfp) data.config.pfp = pfps[0];

        voiceline_paths = data.voiceline_paths;

        let isVal = data.config?.expression_to_voice;

        for (const exp of expressions) {
            if (isVal) {
                isVal = data.config.expression_to_voice.hasOwnProperty(exp);
            }
            
            data.config.expression_to_voice[exp] = isVal ? data.config.expression_to_voice[exp] : null;
        }

        config = data.config;
    };

    const handleSaveCharacter = async () => {
        if (
            (Object.keys(config).filter(k => !k && requiredConfigs.includes(k))).length !== 0
        ) return;

        if (!config.expression_to_voice?.neutral) return;

        globals.conn.emit('saveCharacter', {dir: character_dir, config: config});
    };

    const handleSavedCharacterSuccess = async () => {
        window.location.reload();
    };

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
    });

    $effect(() => {
        if (character_dir) {
            globals.conn.emit('getCharacterData', character_dir);
        }
    });

    $effect(() => {
        if (config.model_path) {
            if (config.model_path.endsWith('.gltf')) {
                config.model_type = 'gltf';
            } else {
                config.model_type = 'vrm';
            }
        };
    });
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
