import { browser } from '$app/environment';

export async function load({ fetch }) {
    // CRUCIAAL: Gebruik de servicenaam 'backend' als we op de server draaien
    const apiHost = browser ? 'http://localhost:5000' : 'http://backend:5000';
    
    try {
        const response = await fetch(`${apiHost}/api/items`);
        if (!response.ok) throw new Error('Backend niet bereikbaar');
        
        const items = await response.json();
        return { items };
    } catch (err) {
        console.error("Fetch fout:", err);
        return { items: [], error: "Laden mislukt, probeer te refreshen." };
    }
}