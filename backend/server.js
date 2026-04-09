app.post("/query", async (req, res) => {
    const userQuery = req.body.query;

    const response = await fetch("http://127.0.0.1:8000/ai", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ query: userQuery })
    });

    const data = await response.json();
    res.json(data);
});