<script>
	// We gebruiken $state voor de ruwe data
	let searchTerm = $state("");
	
	let inventory = $state([
		{ id: "001", name: "Smartphone Case", category: "Electronics", stock: 45, location: "Aisle 1" },
		{ id: "002", name: "Bluetooth Speaker", category: "Electronics", stock: 12, location: "Aisle 3" },
		{ id: "042", name: "Coffee Mug", category: "Kitchenware", stock: 89, location: "Aisle 5" },
		{ id: "105", name: "Ergonomic Mouse", category: "Office", stock: 23, location: "Aisle 2" },
		{ id: "210", name: "USB-C Cable", category: "Electronics", stock: 150, location: "Aisle 1" }
	]);

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
			<table>
				<thead>
					<tr>
						<th>Item ID</th>
						<th>Name</th>
						<th>Category</th>
						<th>Stock</th>
						<th>Location</th>
					</tr>
				</thead>
				<tbody>
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
							<td colspan="5" class="no-results">No items found matching "{searchTerm}"</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>
</div>

<style>
	/* De algemene dashboard en sidebar styling is hetzelfde als je +page.svelte */
	.dashboard { display: flex; height: calc(100vh - 65px); }
	.main-content { flex: 1; padding: 2rem; overflow-y: auto; }
	
	.content-header { 
		display: flex; 
		justify-content: space-between; 
		align-items: flex-end; 
		margin-bottom: 2rem; 
	}

	h1 { margin: 0; font-size: 1.5rem; }
	.subtitle { color: #888; margin: 4px 0 0 0; font-size: 0.9rem; }

	/* Zoekbalk Styling */
	.search-container {
		position: relative;
		width: 300px;
	}

	.search-icon {
		position: absolute;
		left: 12px;
		top: 50%;
		transform: translateY(-50%);
		color: #999;
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

	/* Tabel Details */
	.table-wrapper { background: white; border-radius: 12px; border: 1px solid #e0e0e0; overflow: hidden; }
	table { width: 100%; border-collapse: collapse; }
	th { background: #fcfcfc; padding: 1rem; text-align: left; font-size: 0.85rem; color: #666; border-bottom: 1px solid #eee; }
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
</style>