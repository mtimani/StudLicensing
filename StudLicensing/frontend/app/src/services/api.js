const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
console.log("API URL:", API_BASE_URL);

export async function postToken(data) {
    
    const formBody = new URLSearchParams(data).toString();
  
    const res = await fetch(`${API_BASE_URL}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
      },
      body: formBody,
    });
  
    if (!res.ok) throw new Error("API error");
  
    return await res.json();
  }