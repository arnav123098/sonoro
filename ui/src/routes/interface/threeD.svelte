<Model model_path={model_path} model_type={model_type} />

<script>
    import Model from './model.svelte';

    let { model_path, model_type } = $props();
</script>
