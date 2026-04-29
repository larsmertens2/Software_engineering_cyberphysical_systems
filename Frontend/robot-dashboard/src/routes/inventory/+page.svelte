<script>
    import { io } from 'socket.io-client';
    import { onMount } from 'svelte';

    let { data } = $props(); 

    let items = $state(data.items ?? []);

    let searchTerm = $state("");

    $effect(() => {
        items = data.items ?? [];
    });

    onMount(() => {
        const socket = io('http://localhost:5000');

        socket.on('inventory_updated', () => {
            console.log("Inventory change detected, refreshing...");
            refreshInventory();
        });

        return () => socket.disconnect();
    });

    async function refreshInventory() {
		const res = await fetch('http://localhost:5000/api/items');
		if (res.ok) {
			items = await res.json();
		}
	}

    let inventory = $derived(
        items.map(item => ({
            id: item.id.toString(),
            name: item.name,
            category: item.category,
            stock: item.stock,
            location: `Aisle ${item.aisle}`
        }))
    );

    let filteredInventory = $derived(
        inventory.filter(item => 
            item.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
            item.id.toLowerCase().includes(searchTerm.toLowerCase())
        )
    );
</script>

<div class="dashboard">
	<section class="main-content">
		<header class="content-header">
			{#if data.error}
				<div class="error-banner">{data.error}</div>
			{/if}
			<div>
				<h1>Inventory Overview</h1>
				<p class="subtitle">Manage and locate warehouse items</p>
			</div>
			
			<div class="search-container">
				<input 
					type="text" 
					placeholder="Search by name or ID..." 
					bind:value={searchTerm} 
				/>
			</div>
		</header>

		<div class="table-wrapper">
			<div class="titels">
			</div>
			<table>
                <tbody>
					<tr>
						<td>ID</td>
						<td>Name</td>
						<td>Category</td>
						<td>Stock</td>
						<td>Aisle</td>
					</tr>
                    {#each filteredInventory as item}
                        <tr>
                            <td class="id-cell">{item.id}</td>
                            <td class="bold">{item.name}</td>
                            <td><span class="tag">{item.category}</span></td>
                            <td class={item.stock < 20 ? 'low-stock' : ''}>{item.stock} units</td>
                            <td>{item.location}</td>
                        </tr>
                    {:else}
                        <tr>
                            <td colspan="5" class="no-results">
                                {searchTerm ? `No items found matching "${searchTerm}"` : 'Loading inventory...'}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
		</div>
	</section>
</div>

<style>
	.dashboard { display: flex; height: calc(100vh - 65px); }
	.main-content { flex: 1; padding: 2rem;}
	
	.content-header { 
		display: flex; 
		justify-content: space-between; 
		align-items: flex-end; 
		margin-bottom: 2rem; 
	}

	h1 { margin: 0; font-size: 1.5rem; }
	.subtitle { color: #888; margin: 4px 0 0 0; font-size: 0.9rem; }

	.search-container {
		position: relative;
		width: 10%;
		margin-left: 10%;
	}

	input {
		width: 100%;
		padding: 10px 10px 10px 35px;
		border: 1px solid #ddd;
		border-radius: 8px;
		font-size: 0.9rem;
		outline: none;
		transition: border-color 0.2s;
	}

	input:focus { border-color: #007bff; box-shadow: 0 0 0 2px rgba(0,123,255,0.1); }

	.table-wrapper { background: white; border-radius: 12px; border: 1px solid #e0e0e0; overflow: hidden; }
	table { width: 100%; border-collapse: collapse; }
	td { padding: 1rem; border-bottom: 1px solid #f9f9f9; }

	.id-cell { font-family: monospace; color: #007bff; font-weight: 600; }
	.bold { font-weight: 600; }
	
	.tag { 
		background: #f0f0f0; 
		padding: 3px 8px; 
		border-radius: 12px; 
		font-size: 0.8rem; 
		color: #555; 
	}

	.low-stock { color: #d9534f; font-weight: bold; }
	.no-results { text-align: center; padding: 3rem; color: #999; font-style: italic; }
	.error-banner { background: #f8d7da; color: #721c24; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
</style>