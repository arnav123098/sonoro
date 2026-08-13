<div
    bind:this={win}
    class='window'
>
    <div class="titlebar">
        <span>{name}</span>
        {#if !required}
            <button class='close-btn' onclick={() => closeWindow()}>X</button>
        {/if}
    </div>

    <div class='content'>
        {@render children?.()}
    </div>
</div>

<script>
    import { onMount } from "svelte";

    let win;

    let {
        name = '',
        closeWindow,
        children,
        required,
        bg = true
    } = $props();
</script>

<style>
    .window {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        overflow: hidden;
        height: 70vh;
        width: 75vw;
        max-width: 600px;
        background: rgba(0, 134, 255, 0.3);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(3.1px);
        -webkit-backdrop-filter: blur(3.1px);
        border: 1px solid rgba(0, 134, 255, 0.3);
    }

    .titlebar {
        height: 2.5rem;

        display: flex;
        justify-content: space-between;
        align-items: center;

        padding-inline: 2rem;

        background-color: rgb(0, 140, 255);

        border-bottom: 1px solid rgba(255,255,255, 0.1);

        letter-spacing: 0.1rem;
    }

    .close-btn {
        font-weight: bold;
        font-size: 1rem;
        cursor: pointer;
        transition-duration: 0.25s;
    }

    .close-btn:hover {
        color: red;
    }

    .content {
        height: calc(100% - 3rem);

        overflow-y: auto;
        overflow-x: hidden;

        padding: 1rem 2rem;
    }

    .content::-webkit-scrollbar, :global(textarea)::-webkit-scrollbar {
        width: 8px;
    }

    .content::-webkit-scrollbar-track, :global(textarea)::-webkit-scrollbar-track {
        background: transparent;
    }

    .content::-webkit-scrollbar-thumb, :global(textarea)::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,.25);
        border-radius: 999px;
    }

    .content::-webkit-scrollbar-thumb:hover, :global(textarea)::-webkit-scrollbar--thumb:hover {
        background: rgba(255,255,255,.4);
    }
</style>
