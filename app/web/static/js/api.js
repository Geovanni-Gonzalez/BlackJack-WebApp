export async function fetchData(url, data = null, method = 'POST') {
    console.log(`[API REQUEST] ${method} ${url}`, data);
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        };

        const config = {
            method: method,
            headers: headers
        };

        if (method !== 'GET' && data) {
            config.body = JSON.stringify(data);
        }

        const response = await fetch(url, config);
        const json = await response.json();
        console.log(`[API RESPONSE] ${url}:`, json);
        return json;
    } catch (e) {
        console.error(`[API ERROR] ${url}:`, e);
        return null;
    }
}
