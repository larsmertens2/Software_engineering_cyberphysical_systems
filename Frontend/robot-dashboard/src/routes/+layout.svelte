<script>
	let { children } = $props();
</script>

<header class="top-header">
	<div class="brand">RoboLogistics</div>
</header>

<div class="app-body">
	<aside class="sidebar">
		<nav class="sidebar-nav">
			<a href="/">Active Queue</a>
			<a href="/inventory">Inventory</a>
			<a href="/map">Warehouse Map</a>
		</nav>
	</aside>

	<main class="content">
		{@render children()}
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: sans-serif;
		background: #f4f7f6;
	}

	.top-header {
		height: 60px;
		background: #1a1a1a;
		color: white;
		display: flex;
		align-items: center;
		padding: 0 2rem;
	}

	.app-body {
		display: flex;
		height: calc(100vh - 60px); /* Trek de header hoogte eraf */
	}

	.sidebar {
		width: 240px;
		background: white;
		border-right: 1px solid #ddd;
		padding-top: 1rem;
	}

	.sidebar-nav a {
		display: block;
		padding: 12px 20px;
		color: #333;
		text-decoration: none;
	}

	.sidebar-nav a:hover {
		background: #f0f0f0;
	}

	.content {
		flex: 1;
		padding: 2rem;
		overflow-y: auto;
	}
</style>