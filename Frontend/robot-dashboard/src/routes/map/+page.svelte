<script>
    import { onMount } from 'svelte';
    import { io } from 'socket.io-client';

    let mapData     = $state(null);
    let loadError   = $state('');
    let isLoading   = $state(true);
    let aisleStates = $state({});

    const ROBOT_COLORS = {
        'Bot_1': '#e74c3c',
        'Bot_2': '#3498db',
        'Bot_3': '#2ecc71',
    };
    function robotColor(id) { return ROBOT_COLORS[id] ?? '#f39c12'; }

    onMount(async () => {
        try {
            const res = await fetch('http://localhost:5000/api/map');
            if (!res.ok) throw new Error(`HTTP fout: ${res.status}`);
            mapData = await res.json();
        } catch (error) {
            console.error('Fout bij laden map:', error);
            loadError = 'De warehouse map kon niet worden opgehaald.';
        } finally {
            isLoading = false;
        }

        try {
            const res = await fetch('http://localhost:5000/api/aisle/states');
            if (res.ok) aisleStates = await res.json();
        } catch (_) {}

        const socket = io('http://localhost:5000');
        socket.on('aisle_updated', (data) => { aisleStates = data; });
        return () => socket.disconnect();
    });

    const scale   = 200;
    const offsetX = 500;
    const offsetY = 1800;

    function getX(x) { return offsetX + x * scale; }
    function getY(y) { return offsetY - y * scale; }

    function getBaseAisle(name) {
        return name.split('_').slice(0, 2).join('_'); // "Ailse_1_2" -> "Ailse_1"
    }

    function aisleEdgeColor(nodeName) {
        const st = aisleStates[getBaseAisle(nodeName)];
        return st?.locker ? '#e74c3c' : '#2ecc71';
    }

    let nodes = $derived(mapData?.nodes ? Object.entries(mapData.nodes) : []);
    let edges = $derived(mapData?.edges ?? []);

    // Robots die wachten op een aisle: toon op hun exacte node-positie
    let waitingRobots = $derived(
        Object.entries(aisleStates).flatMap(([aisle, st]) =>
            (st.waiting ?? []).map(w => ({ robot_id: w.robot_id, node: w.node, aisle }))
        )
    );

    // Robots die in de aisle zijn: toon bij de entrance node van die aisle
    let inAisleRobots = $derived(
        Object.entries(aisleStates)
            .filter(([_, st]) => st.locker)
            .map(([aisle, st]) => ({ robot_id: st.locker, aisle_node: aisle }))
    );
</script>

<div class="map-container">
    <svg
        viewBox="0 0 1000 800"
        width="95%"
        height="95%"
        preserveAspectRatio="xMidYMid meet"
    >
        {#if isLoading}
            <text x="500" y="400" fill="white" text-anchor="middle" font-style="italic">
                Warehouse data laden...
            </text>
        {:else if loadError}
            <text x="500" y="400" fill="#ff8080" text-anchor="middle" font-weight="bold">
                {loadError}
            </text>
        {:else if mapData}

            <!-- Edges -->
            {#each edges as [start, end]}
                {#if mapData.nodes[start] && mapData.nodes[end]}
                    {#if start.includes('Ailse') && end.includes('Ailse')}
                        <!-- Aisle edge: groen = vrij, rood = bezet -->
                        <line
                            x1={getX(mapData.nodes[start].x)} y1={getY(mapData.nodes[start].y)}
                            x2={getX(mapData.nodes[end].x)}   y2={getY(mapData.nodes[end].y)}
                            stroke={aisleEdgeColor(start)}
                            stroke-width="8"
                            stroke-linecap="round"
                            opacity="0.7"
                            class="aisle-edge"
                        />
                    {:else}
                        <line
                            x1={getX(mapData.nodes[start].x)} y1={getY(mapData.nodes[start].y)}
                            x2={getX(mapData.nodes[end].x)}   y2={getY(mapData.nodes[end].y)}
                            stroke="#333"
                            stroke-width="3"
                            stroke-linecap="round"
                        />
                    {/if}
                {/if}
            {/each}

            <!-- Nodes -->
            {#each nodes as [name, coord]}
                <circle
                    cx={getX(coord.x)} cy={getY(coord.y)}
                    r={name.includes('Droppoff') ? 7 : 5}
                    fill={name.includes('Droppoff') ? '#f1c40f' : '#555'}
                    stroke="#1a1a1a" stroke-width="1"
                />
                {#if name.includes('Droppoff')}
                    <text
                        x={getX(coord.x)} y={getY(coord.y) - 12}
                        fill="white" font-size="12" font-weight="500" text-anchor="middle"
                        class="node-label"
                    >
                        {name.replace('Droppoff_', 'D')}
                    </text>
                {/if}
            {/each}

            <!-- Robots in de aisle: gestippeld, bij entrance node -->
            {#each inAisleRobots as r}
                {#if mapData.nodes[r.aisle_node]}
                    <g class="robot-marker" opacity="0.8">
                        <circle
                            cx={getX(mapData.nodes[r.aisle_node].x)}
                            cy={getY(mapData.nodes[r.aisle_node].y)}
                            r="14"
                            fill={robotColor(r.robot_id)}
                            stroke="white" stroke-width="2" stroke-dasharray="4 2"
                        />
                        <text
                            x={getX(mapData.nodes[r.aisle_node].x)}
                            y={getY(mapData.nodes[r.aisle_node].y)}
                            text-anchor="middle" dominant-baseline="central"
                            fill="white" font-weight="bold" font-size="12"
                        >
                            {r.robot_id.replace('Bot_', '')}
                        </text>
                    </g>
                {/if}
            {/each}

            <!-- Wachtende robots: vol, op exacte node-positie -->
            {#each waitingRobots as r}
                {#if mapData.nodes[r.node]}
                    <g class="robot-marker">
                        <circle
                            cx={getX(mapData.nodes[r.node].x)}
                            cy={getY(mapData.nodes[r.node].y)}
                            r="16"
                            fill={robotColor(r.robot_id)}
                            stroke="white" stroke-width="3"
                        />
                        <text
                            x={getX(mapData.nodes[r.node].x)}
                            y={getY(mapData.nodes[r.node].y)}
                            text-anchor="middle" dominant-baseline="central"
                            fill="white" font-weight="bold" font-size="14"
                        >
                            {r.robot_id.replace('Bot_', '')}
                        </text>
                    </g>
                {/if}
            {/each}

        {/if}
    </svg>
</div>

<style>
    .map-container {
        background: #1a1a1a;
        width: 100%;
        height: 100%;
        max-height: 100%;
        border-radius: 16px;
        display: flex;
        justify-content: center;
        align-items: center;
        overflow: hidden;
        box-sizing: border-box;
    }

    svg { width: 100%; height: 100%; display: block; }

    .aisle-edge {
        transition: stroke 0.4s ease;
    }

    .node-label {
        pointer-events: none;
        user-select: none;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
    }

    .robot-marker circle {
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
</style>
