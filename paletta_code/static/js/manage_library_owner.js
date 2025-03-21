document.addEventListener("DOMContentLoaded", function () {



    const filesToLoad = [
        { url: "./navigation_internal.html", targetId: "header" },
        { url: "./footer.html", targetId: "footer" }
    ];
    
    Promise.all(filesToLoad.map(file =>
        fetch(file.url)
            .then(response => response.text())
            .then(data => {
                document.getElementById(file.targetId).innerHTML = data;
            })
            .catch(error => console.error(`Error loading ${file.url}:`, error))
    ));

});
