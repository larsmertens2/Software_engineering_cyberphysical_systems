<script>
    let { data } = $props(); 
    let showPopup = $state(false); // Houdt bij of de popup open is
    let newItemId = $state("");    // Het ID voor het toegevogede item

    let activeQueue = $derived(
        data.items?.map(task => ({
            id: task.id,
            itemName: task.name,
            status: task.status,
            robotId: task.robot_id ?? "not assigned", 
            aisle: task.aisle
        })) ?? []
    );

    async function handleSubmit() {
    if (!newItemId) return;

    // Stuur de data naar je Flask backend
    const response = await fetch('http://localhost:5000/api/queue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: newItemId })
    });

    if (response.ok) {
      showPopup = false; // Sluit de popup
      newItemId = "";    // Reset het veld
      // Optioneel: refresh je data hier
    } else {
      alert("Fout bij toevoegen van item.");
    }
  }

</script>

<div class="dashboard">
    <section class="main-content">
        <header class="content-header">
            <h1>Live Task Overview</h1>
            <button onclick={() => showPopup = true}>+ Add Item</button>
            {#if showPopup}
            <div class="modal-overlay">
                <div class="modal-content">
                <h3>Add Item to Queue</h3>
                <p>Enter the Item ID:</p>
                
                <input 
                    type="number" 
                    bind:value={newItemId} 
                    placeholder="e.g. 1, 2, 3..." 
                />

                <div class="modal-buttons">
                    <button onclick={() => showPopup = false}>Cancel</button>
                    <button onclick={handleSubmit} class="confirm-btn">Add to Queue</button>
                </div>
                </div>
            </div>
            {/if}
        </header>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Item</th>
                        <th>Status</th>
                        <th>Robot</th>
                        <th>Aisle</th>
                    </tr>
                </thead>
                <tbody>
                    {#each activeQueue as task}
                        <tr>
                            <td class="bold">{task.id}</td>
                            <td>{task.itemName}</td>
                            <td>
                                <span class="status-tag {task.status}">
                                    {task.status}
                                </span>
                            </td>
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
    /* ... Je bestaande CSS ... */

    /* Nieuwe styles voor status tags */
    .status-tag {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        text-transform: uppercase;
        font-weight: bold;
    }

    .status-tag.pending {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
    }

    .status-tag.assigned {
        background-color: #d1ecf1;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }

    .robot-badge {
        background: #f0f0f0;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9rem;
    }
    
    /* Zorg dat de tabel er netjes uitziet */
    .table-wrapper {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .modal-content {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    text-align: center;
  }

  input {
    display: block;
    margin: 1rem auto;
    padding: 0.5rem;
    width: 80%;
  }

  .modal-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  .confirm-btn {
    background-color: #4CAF50;
    color: white;
  }

</style>