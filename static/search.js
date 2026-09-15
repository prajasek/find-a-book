console.log("js loaded")

async function fetchResults(url) {
     console.log("sdfsdf fetching results", url)
     const response = await fetch(url);

        const data = await response.json();

        console.log("--DATA: ", data)

        return data
}


document
    .getElementById("search-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const loader = document.getElementById("loader");
        loader.innerHTML = "Loading";
        loader.classList.remove("hidden-loader")

        const title = document.getElementById("title").value;
        const author = document.getElementById("author").value;
        
        const url = `/search?title=${encodeURIComponent(title)}&author=${encodeURIComponent(author)}`;
        
        const data = await fetchResults(url);

        renderResults(data)
    });


// Goodreads
document
    .getElementById("goodreads-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const loader = document.getElementById("loader");
        loader.innerHTML = "Loading";
        loader.classList.remove("hidden-loader")


        console.log("goodreads url hit")

        const data = await fetchResults("/goodreads");

        renderResults(data)

    });



document
    .getElementById("library-form")
    .addEventListener("submit", async (event) => {
        const loader = document.getElementById("loader");
        loader.innerHTML = "Loading";
        loader.classList.remove("hidden-loader")

        event.preventDefault();
        const data = await fetchResults("/library");
        renderResults(data)

    });

    
// document
//     .getElementById("run-form")
//     .addEventListener("submit", async (event) => {
//         const resultsContainer = document.getElementById("results");

//         loader.innerHTML = "Loading";
//         loader.classList.remove("hidden-loader")

//         event.preventDefault();
//         const data = await fetchResults("/run");
//         renderResults(data)

//     });



function renderResults(books_info) {

    console.log("rendering...")
    const resultsContainer = document.getElementById("results");



    const books = books_info["books"];
    const new_books = books_info["new"];
    const removed_books = books_info["removed"];
    const req_type = books_info["type"]

    if (!books || books.length === 0) {
        resultsContainer.textContent = "No books found.";
        return;
    }

    /*
     * Find every unique library location across all books.
     *
     * Example:
     *
     * [
     *   "Henrietta Hankin Library",
     *   "Chester County Library"
     * ]
     */
    const locations = new Set();

    books.forEach(book => {
        if (!book.library_book) {
            return;
        }

        book.library_book.libraries.forEach(library => {
            locations.add(library.location);
        });
    });


    // Create table
    const table = document.createElement("table");
    table.className = "results-table";


    // ---------------------------------------------------------
    // Header
    // ---------------------------------------------------------

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    const bookHeader = document.createElement("th");
    bookHeader.textContent = "Book";

    headerRow.appendChild(bookHeader);

    locations.forEach(location => {
        const header = document.createElement("th");
        header.textContent = location;

        headerRow.appendChild(header);
    });

    if (req_type == "goodreads" || req_type == "home") {
        const watchlist = document.createElement("th");
        watchlist.textContent = "Status"
        headerRow.appendChild(watchlist);
    }

    thead.appendChild(headerRow);
    table.appendChild(thead);


    // ---------------------------------------------------------
    // Body
    // ---------------------------------------------------------

    const tbody = document.createElement("tbody");

    books.forEach(book => {

        const _id = book["id"];
        is_new = false; 
        is_removed = false; 


        new_books.forEach(b => {
            if (_id == b["id"]) is_new = true;
        })

        removed_books.forEach(b => {
            if (_id == b["id"]) is_removed = true;
        })


        const row = document.createElement("tr");
        row.id = book["id"]


        // Book name
        const bookCell = document.createElement("td");
        const book_div = document.createElement("div");
        const title_div = document.createElement("div");
        const author_div = document.createElement("div");

        title_div.textContent = capitalize(book.title) 
        title_div.className = "book-title"

        author_div.textContent = capitalize(book.author)
        author_div.className = "book-author"

        book_div.appendChild(title_div)
        book_div.appendChild(author_div)

        bookCell.appendChild(book_div)


        if (is_new) {
            const tag = document.createElement("span");
            tag.textContent = "newly added";
            tag.className = "book-tag new";
            title_div.appendChild(tag);        
        }

        if (is_removed) {
            const tag = document.createElement("span");
            tag.textContent = "removed";
            tag.className = "book-tag removed";
            title_div.appendChild(tag);
        }

        row.appendChild(bookCell);


        // Library columns
        locations.forEach(location => {

            const cell = document.createElement("td");

            const library = book.library_book?.libraries.find(
                library => library.location === location
            );

            if (!library) {
                cell.textContent = "—";
                cell.className = "unavailable";
            } else {
                const status_container = document.createElement("div");
                status_container.className = "library-status-cell";
                cell.appendChild(status_container);
                
                Object.entries(library.status).forEach(([status, count]) => {
                        const badge = document.createElement("div");
                        
                        badge.className = 'status-line'
                        badge.innerHTML = `${capitalize(status)}: <strong>${count}</strong>`;

                        status_container.appendChild(badge);
                        console.log("badge:", badge)
                        
                    })
                    

            
                
            }

            row.appendChild(cell);
        });


        // If its just /goodreads list, add a watchlist column
        if (req_type == "goodreads" || req_type == "home") {

            const watch_cell = document.createElement("td");
            const btn = document.createElement("button");

            btn.classList.add("watch-button")

            function updateWatchButton() {
                btn.textContent = book.watch ? "watching" : "watch"
                btn.classList.toggle("watching", book.watch)
            }

            updateWatchButton()
            
            btn.addEventListener("click", async () => {
                const new_watch_status = !book.watch

                console.log("Watching: ", "/watch")
                
                const url = "/watch"
                const body = {book_id: book.id, watch: new_watch_status}
                
                const response = await fetch(url,  {

                        method: 'POST', 
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(body)
                    })


                const data = response.json();

                console.log(data.msg, response.status)

                if (response.ok) {
                    book.watch = new_watch_status; 
                    updateWatchButton();
                }

            })

            watch_cell.appendChild(btn)


            row.appendChild(watch_cell)
        }
        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    console.log(table)

        // Clear previous results
    resultsContainer.innerHTML = "";

    resultsContainer.appendChild(table);


    const loader = document.getElementById("loader");
    loader.innerHTML = "Loading";
    loader.classList.add("hidden-loader")
}


function capitalize(str) {

    if (!str) return "";

    if (str.includes(",")) {
        str = str.toLowerCase().split(",").map(c => c.trim())
    } else {
        str = str.toLowerCase().split(" ").map(c => c.trim())
    }

    return str.map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
}


fetchResults("/stored-books").then(data => renderResults(data))
