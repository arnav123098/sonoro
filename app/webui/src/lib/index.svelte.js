export const toTitleCase = text => {
    if (!text) return;
    return text.charAt(0).toUpperCase() + text.slice(1)
}

export const globals = $state({
    conn: null,
    is_conn: false,
    config: null,
    missing_configs: [],
    characters: null,
    current_char: null,
    animator: null,
    bgImg: '/flowers.gif',
    defaultbg: '/flowers.gif'
});
