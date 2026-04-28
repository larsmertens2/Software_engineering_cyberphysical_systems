import { browser } from '$app/environment';

export async function load({ fetch }) {
    const apiHost = browser ? 'http://localhost:5000' : 'http://backend:5000';
    
    try {
        const response = await fetch(`${apiHost}/api/queue/status`);
        if (!response.ok) throw new Error('Backend not reachable');
        
        const items = await response.json();
        return { items };
    } catch (err) {
        console.error("Fetch fout:", err);
        return { items: [], error: "loading failed, try refreshing" };
    }
}