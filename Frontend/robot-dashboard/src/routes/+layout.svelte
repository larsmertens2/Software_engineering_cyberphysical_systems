<script>
	let { children } = $props();
	let emergencyActive = $state(false);

	async function toggleEmergency() {
		try {
			const response = await fetch('http://localhost:5000/api/emergency', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			});

			if (response.ok) {
				const data = await response.json();
				emergencyActive = data.emergency_active;
				console.log('Emergency status:', data);
			} else {
				console.error('Failed to toggle emergency');
			}
		} catch (error) {
			console.error('Error calling emergency endpoint:', error);
		}
	}

	async function checkEmergencyStatus() {
		try {
			const response = await fetch('http://localhost:5000/api/emergency', {
				method: 'GET'
			});

			if (response.ok) {
				const data = await response.json();
				emergencyActive = data.emergency_active;
			}
		} catch (error) {
			console.error('Error checking emergency status:', error);
		}
	}

	$effect(() => {
		checkEmergencyStatus();
		const interval = setInterval(checkEmergencyStatus, 1000); 
		return () => clearInterval(interval);
	});
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

		<button 
		class="emergency-button"
		class:active={emergencyActive}
		onclick={toggleEmergency}
	>
		{emergencyActive ? 'EMERGENCY ACTIVE' : 'EMERGENCY STOP'}
	</button>

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
		height: calc(100vh - 60px);
	}

	.sidebar {
		width: 240px;
		background: white;
		border-right: 1px solid #ddd;
		padding-top: 1rem;
		
		display: flex;
		flex-direction: column;
		align-items: center; 
		overflow: hidden;
	}

	.sidebar-nav {
		width: 100%; 
	}

	.sidebar-nav a {
		display: block;
		padding: 12px 20px;
		color: #333;
		text-decoration: none;
		width: 100%;
	}

	.sidebar-nav a:hover {
		background: #f0f0f0;
	}

	.content {
		flex: 1;
		padding: 2rem;
		overflow-y: auto;
	}

	.emergency-button {
		background-color: red;
		color: white;
		font-weight: bold;
		width: 80%;
		height: 60px;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		margin: 20px 0;
		font-size: 14px;
		transition: background-color 0.3s ease;
	}

	.emergency-button:hover {
		background-color: darkred;
	}

	.emergency-button.active {
		background-color: green;
	}

	.emergency-button.active:hover {
		background-color: darkgreen;
	}
</style>