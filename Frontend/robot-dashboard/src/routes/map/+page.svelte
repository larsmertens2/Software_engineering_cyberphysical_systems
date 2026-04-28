<script>
    import { onMount } from 'svelte';

    let mapData = $state(null);
    let loadError = $state('');
    let isLoading = $state(true);

    onMount(async () => {
        try {
            const response = await fetch('http://localhost:5000/api/map');

            if (!response.ok) {
                throw new Error(`HTTP fout: ${response.status}`);
            }

            mapData = await response.json();

            const coords = Object.values(mapData.nodes);
            const xValues = coords.map(n => n.x);
            const yValues = coords.map(n => n.y);
            console.log("X bereik:", Math.min(...xValues), "tot", Math.max(...xValues));
            console.log("Y bereik:", Math.min(...yValues), "tot", Math.max(...yValues));
        } catch (error) {
            console.error('Fout bij laden map:', error);
            loadError = 'De warehouse map kon niet worden opgehaald uit de database.';
        } finally {
            isLoading = false;
        }
    });

    const scale = 200; 
    const offsetX = 500;
    const offsetY = 1800;

    function getX(x) { return offsetX + (x * scale); }
    function getY(y) { return offsetY - (y * scale); }

    // Reactieve berekeningen voor Svelte 5
    let nodes = $derived(mapData?.nodes ? Object.entries(mapData.nodes) : []);
    let edges = $derived(mapData?.edges ? mapData.edges : []);

    let robots = $state([
        { id: 'Bot_1', x: -0.3, y: 1.2, color: '#ff4444' }
    ]);
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
            {#each edges as [start, end]}
                {#if mapData.nodes[start] && mapData.nodes[end]}
                    <line 
                        x1={getX(mapData.nodes[start].x)} 
                        y1={getY(mapData.nodes[start].y)} 
                        x2={getX(mapData.nodes[end].x)} 
                        y2={getY(mapData.nodes[end].y)} 
                        stroke="#333" 
                        stroke-width="3" 
                        stroke-linecap="round"
                    />
                {/if}
            {/each}

            {#each nodes as [name, coord]}
                <circle 
                    cx={getX(coord.x)} 
                    cy={getY(coord.y)} 
                    r={name.includes('Entrance') ? 7 : 5} 
                    fill={name.includes('Entrance') ? '#f1c40f' : '#555'} 
                    stroke="#1a1a1a"
                    stroke-width="1"
                />
                
                {#if name.includes('Entrance') || name.includes('Droppoff')}
                    <text 
                        x={getX(coord.x)} 
                        y={getY(coord.y) - 15} 
                        fill="white" 
                        font-size="12"
                        font-weight="500"
                        text-anchor="middle"
                        class="node-label"
                    >
                        {name.replace('Droppoff_', 'D')}
                    </text>
                {/if}
            {/each}

            {#each robots as robot}
                <g class="robot-marker">
                    <circle 
                        cx={getX(robot.x)} 
                        cy={getY(robot.y)} 
                        r="16" 
                        fill={robot.color} 
                        stroke="white" 
                        stroke-width="3" 
                    />
                    <text 
                        x={getX(robot.x)} 
                        y={getY(robot.y)} 
                        text-anchor="middle" 
                        dominant-baseline="central" 
                        fill="white" 
                        font-weight="bold"
                        font-size="14"
                    >
                        {robot.id.replace('Bot_', '')}
                    </text>
                </g>
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

    svg {
        width: 100%;
        height: 100%;
        display: block; 
    }
    .node-label {
        pointer-events: none;
        user-select: none;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }

    .robot-marker circle {
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
</style>