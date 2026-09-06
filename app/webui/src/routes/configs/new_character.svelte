<div id='menu'>
    <div>
        <input bind:value={newCharName} placeholder="character name">
        <button onclick={() => createFunc(newCharName)}>Create</button>
    </div>
</div>

<script>
    let newCharName = $state('');
    let { createFunc } = $props();
</script>

<style>
    #menu {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
    }

    #menu div {
        width: 100%;
        text-align: center;
    }

    input {
        background-color: rgba(255, 255, 255, 0.17);
    }
</style>
