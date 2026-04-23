<script>
	// We gebruiken $state voor reactieve data (Svelte 5)
	let activeQueue = $state([
		{ itemId: "ITM-102", robotId: "TB-01", aisle: "3" },
		{ itemId: "ITM-505", robotId: "TB-02", aisle: "1" },
		{ itemId: "ITM-990", robotId: "TB-03", aisle: "7" },
		{ itemId: "ITM-212", robotId: "Searching...", aisle: "-" }
	]);
</script>

<div class="dashboard">
	<section class="main-content">
		<header class="content-header">
			<h1>Live Task Overview</h1>
			<button class="add-btn">+ Add Item</button>
		</header>

		<div class="table-wrapper">
			<table>
				<thead>
					<tr>
						<th>Item ID</th>
						<th>Robot ID</th>
						<th>Aisle nr</th>
					</tr>
				</thead>
				<tbody>
					{#each activeQueue as task}
						<tr>
							<td class="bold">{task.itemId}</td>
							<td>
								<span class="robot-badge">{task.robotId}</span>
							</td>
							<td>
								<span class="aisle-indicator">Aisle {task.aisle}</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>
</div>

<style>
	.dashboard {
		display: flex;
		height: calc(100vh - 65px); /* Header eraf trekken */
	}

	/* Content Styling */
	.main-content {
		flex: 1;
		padding: 2rem;
		overflow-y: auto;
	}

	.content-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	h1 { margin: 0; font-size: 1.5rem; }

	.add-btn {
		background-color: #007bff;
		color: white;
		border: none;
		padding: 10px 20px;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 600;
	}

	/* Tabel Styling */
	.table-wrapper {
		background: white;
		border-radius: 12px;
		border: 1px solid #e0e0e0;
		overflow: hidden;
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}

	th {
		background-color: #fcfcfc;
		padding: 1rem;
		text-align: left;
		font-size: 0.85rem;
		color: #666;
		border-bottom: 1px solid #eee;
	}

	td {
		padding: 1rem;
		border-bottom: 1px solid #f9f9f9;
	}

	.bold { font-weight: 600; color: #1a1a1a; }

	.robot-badge {
		background: #f0f0f0;
		padding: 4px 8px;
		border-radius: 4px;
		font-family: 'Courier New', Courier, monospace;
		font-size: 0.9rem;
	}

	.aisle-indicator {
		color: #666;
		font-style: italic;
	}

	tr:hover {
		background-color: #fcfdff;
	}
</style>