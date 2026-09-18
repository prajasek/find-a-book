console.log("js loaded")


let booksListInfo = {}

/**********************************  HELPERS  *************************************************/
async function fetchResults(url) {
    console.log("sdfsdf fetching results", url)
    const response = await fetch(url);
    const data = await response.json();
    
    if (!response.ok) {
        console.log("Errored!");
        console.log("Error message: ", data.message);
        return;
    }

    console.log("=====DATA======: ", data)
    booksListInfo = data;

    return data
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





/**********************************  SEARCH A BOOK  *************************************************/
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


    
/**********************************  HOME BUTTON  *************************************************/
document
    .getElementById("home")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const loader = document.getElementById("loader");
        loader.innerHTML = "Loading";
        loader.classList.remove("hidden-loader")

        console.log("loading homepage results")

        const data = await fetchResults("/stored-books");

        let searchInput = document.getElementById("search-list");
        let titleSearchBox = document.getElementById("title");
        let authorSearchBox = document.getElementById("author");

        searchInput.value = titleSearchBox.value = authorSearchBox.value = "";


        renderResults(data)

    });


/**********************************  GOODREADS  *************************************************/
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




/*************************** SEARCH LIBRARY FOR WATCHLIST BOOKS  *************************************************/
document
    .getElementById("library-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const loader = document.getElementById("loader");
        loader.innerHTML = "Loading";
        loader.classList.remove("hidden-loader")

        const data = await fetchResults("/library");
        renderResults(data)

    });


    
/**********************************  SEARCH BOOKS IN LIST  *************************************************/

const searchInput = document.getElementById("search-list");

searchInput.addEventListener("input", () => filterResults(searchInput.value))

function filterResults(query) {
    query = query.toLowerCase().trim()

    if (!query) {
        renderResults(booksListInfo);
        return;
    }

    function matchBook(book) {
       return (
        book.title.toLowerCase().includes(query) ||
        book.author.toLowerCase().includes(query)
        )
    }


    const filteredAllBooks = booksListInfo["books"].filter(matchBook);
    const filteredNew = booksListInfo["new"].filter(matchBook);
    const filteredRemoved = booksListInfo["removed"].filter(matchBook)

    filteredResults = {
        books: filteredAllBooks, 
        new: filteredNew, 
        removed: filteredRemoved, 
        type: booksListInfo["type"]
    };

    renderResults(filteredResults);
}



/*********************************************************************************************************
|                                       RENDER RESULTS TO TABLE
|
/*********************************************************************************************************/
function renderResults(books_info) {

    console.log("Rendering books table...")
    const resultsContainer = document.getElementById("results");
    const loader = document.getElementById("loader");


    const books = books_info["books"];
    const new_books = books_info["new"] || [];
    const removed_books = books_info["removed"] || [];
    const req_type = books_info["type"]
    
    if (!books || books.length === 0) {
        resultsContainer.textContent = "No books found.";
        loader.classList.add("hidden-loader")
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
        const watchlistHeader = document.createElement("th");
        watchlistHeader.textContent = ""
        headerRow.appendChild(watchlistHeader);


        const removeBookHeader = document.createElement("th");
        removeBookHeader.textContent = ""
        headerRow.appendChild(removeBookHeader);
    }

    if (req_type == "search") {
        const addBookHeader = document.createElement("th");
        addBookHeader.textContent = "Action"
        headerRow.appendChild(addBookHeader);
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

        /************ CREATE A ROW FOR EACH BOOK **************/
        const row = document.createElement("tr");
        row.id = book["id"]


        // Book name
        const bookCell = document.createElement("td");
        const book_div = document.createElement("div");
        const title_div = document.createElement("div");
        const author_div = document.createElement("div");

        if (req_type == "search") {
            title_div.textContent = capitalize(book.library_book.title) 
            title_div.className = "book-title"

            author_div.textContent = capitalize(book.library_book.author)
            author_div.className = "book-author"
        } else {
            title_div.textContent = capitalize(book.title) 
            title_div.className = "book-title"

            author_div.textContent = capitalize(book.author)
            author_div.className = "book-author"
        }

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


        // If its just /goodreads list, 
        if (req_type == "goodreads" || req_type == "home") {



            /********** ADD WATCHLIST BUTTON PER ROW *******************/
            const watch_cell = document.createElement("td");
            const watch_btn = document.createElement("button");

            watch_btn.classList.add("watch-button")

            function updateWatchButton() {
                watch_btn.textContent = book.watch ? "watching" : "watch"
                watch_btn.classList.toggle("watching", book.watch)
            }

            updateWatchButton()
            
            watch_btn.addEventListener("click", async () => {
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


                const data = await response.json();

                console.log(data.msg, response.status)

                if (response.ok) {
                    book.watch = new_watch_status; 
                    updateWatchButton();
                }

            })

            watch_cell.appendChild(watch_btn)
            row.appendChild(watch_cell)



            /********** ADD REMOVE BUTTON PER ROW *******************/
            const remove_cell = document.createElement("td");
            const remove_btn = document.createElement("button");
            remove_btn.textContent = "Remove"

            remove_btn.classList.add("watch-button")
    
            remove_btn.addEventListener("click", async () => {            
                
                const url = "/remove-book"
                const body = {book_id: book.id}
                
                const response = await fetch(url,  {
                        method: 'POST', 
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(body)
                    })


                const data = await response.json();

                console.log(data);

                if (response.ok) {
                    console.log(book.title + " removed");
                    row.classList.add("removing");

                    setTimeout(() => row.remove(), 400)
                }

            })

            remove_cell.appendChild(remove_btn)
            row.appendChild(remove_cell)

        }


        if (req_type == "search") {
            const book_exists = books_info["exists"]

            const add_cell = document.createElement("td");
            const btn = document.createElement("button");
            
            btn.classList.add("add-button")
          
            if (book_exists) {
                btn.textContent = "Book in list";
                btn.disabled = true; 
                btn.classList.add("already-added")
            } else {
                btn.textContent = "Add to list"
            }
            
            if (!book_exists) {
                    btn.addEventListener("click", async () => {
                        const url = "/add-book"
                        const body = {title: book.library_book.title, author: book.library_book.author}
                        
                        const response = await fetch(url,  {
                                method: 'POST', 
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(body)
                            })

                        const data = await response.json();
                            
                        console.log(data.msg, response.status)

                        if (response.ok) {
                                btn.textContent = "Book in list";
                                btn.disabled = true;
                                btn.classList.add("already-added");                        
                        }
                    });
            }
            console.log("Add button created: ", btn)
            add_cell.appendChild(btn)
            row.appendChild(add_cell)
        }

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    console.log(table)

        // Clear previous results
    resultsContainer.innerHTML = "";

    resultsContainer.appendChild(table);

    loader.classList.add("hidden-loader")
}
/**********************************  FINISH RENDER  *************************************************/




/**********************************  HOMEPAGE  ****************************************************/
fetchResults("/stored-books").then(data => renderResults(data))

async function getNotificationStatus() {
    try {
        const response = await fetch("/get-notification-status");
        const data = await response.json();
        console.log(data)
        if (!response.ok || !data.success) {
            console.log(response.ok, data.success)
            throw new Error(data.msg || "Failed to get notification status");
        }

        updateNotificationButton(data.status);

    } catch (error) {
        console.error("Error getting notification status:", error);

        const button = document.getElementById("notification-toggle");
        button.textContent = "Error";
    }
}


async function toggleNotification() {
    try {
        const response = await fetch("/toggle-notification");
        const data = await response.json();
        console.log(data);

        if (!response.ok || !data.success) {
            throw new Error(data.msg || "Failed to toggle notifications");
        }

        updateNotificationButton(data.status);

    } catch (error) {
        console.error("Error toggling notifications:", error);
    }
}


function updateNotificationButton(status) {
    console.log("updating button to: ", status)
    const button = document.getElementById("notification-toggle");

    if (status) {
        console.log("TOGGLE ON")
        button.textContent = "NOTIFICATION: ON";
        button.classList.add("enabled");
        button.classList.remove("disabled");
    } else {
        console.log("TOGGLE OFF")
        button.textContent = "NOTIFICATION: OFF";
        button.classList.add("disabled");
        button.classList.remove("enabled");
    }
}


document
    .getElementById("notification-toggle")
    .addEventListener("click", toggleNotification);


// Get initial status when page loads
getNotificationStatus();