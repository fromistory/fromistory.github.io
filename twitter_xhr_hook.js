// twitter_xhr_hook.js (save this as a separate file or keep as a multiline string in Python)
(function() {
    // Ensure my_data is initialized on the window object
    if (typeof window.interceptedTwitterData === 'undefined') {
        window.interceptedTwitterData = []; // This will store arrays of entries
    }

    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        this.addEventListener("load", function() {
//            console.log(url)

            let currentEntries = [];
            if (url.includes('SearchTimeline?')) {
            	console.log(url);

				let parsed = JSON.parse(this.response);
                let instructions = parsed['data']['search_by_raw_query']['search_timeline']['timeline']['instructions']
                for (let i of instructions)
                {
                    if (i['type'] === 'TimelineAddEntries')
                    {
                        let entries = i['entries']
                        currentEntries = currentEntries.concat(entries);
//                        console.log('SearchTimeline', entries.length, my_data.data.length);
                    }
                }
//                try {
//                    const parsed = JSON.parse(this.responseText);
//                    // Path: parsed.data.search_by_raw_query.search_timeline.timeline.instructions
//                    // Or sometimes directly parsed.instructions for older/different search types
//                    let instructions;
//                    if (parsed && parsed.data && parsed.data.search_by_raw_query &&
//                        parsed.data.search_by_raw_query.search_timeline &&
//                        parsed.data.search_by_raw_query.search_timeline.timeline &&
//                        parsed.data.search_by_raw_query.search_timeline.timeline.instructions) {
//                        instructions = parsed.data.search_by_raw_query.search_timeline.timeline.instructions;
//                    } else if (parsed && parsed.instructions) { // Fallback for simpler structures
//                        instructions = parsed.instructions;
//                    }
//
//                    if (instructions) {
//                        for (const instruction of instructions) {
//                            if (instruction.type === 'TimelineAddEntries' && instruction.entries) {
//                                currentEntries = currentEntries.concat(instruction.entries);
//                            }
//                            // Sometimes instructions are directly tweet entries or cursors
//                            // This might need more robust handling based on observed JSON
//                            else if (instruction.entries) { // A more generic catch
//                                currentEntries = currentEntries.concat(instruction.entries);
//                            }
//                        }
//                    }
//                } catch (e) {
//                    console.error("Error parsing SearchTimeline:", e, this.responseText);
//                }
            }
            else if (url.includes('UserMedia?'))
            {
                console.log(url);

				let parsed = JSON.parse(this.response);
				console.log(parsed)

                let instructions = parsed['data']['user']['result']['timeline']['timeline']['instructions']
                for (let i of instructions)
                {
//                    'TimelineAddToModule'
                    if (i['type'] === 'TimelineAddToModule')
                    {
                        console.log(i);
                        items = i['moduleItems']
                        currentEntries = currentEntries.concat(items);
//                        let entries = i['entries']
//                        currentEntries = currentEntries.concat(entries);
//                        console.log('SearchTimeline', entries.length, my_data.data.length);
//                        console.log(entries);
                    }
                }
            }
            else if (url.includes('TweetDetail?'))
            {
                console.log(url);
                let parsed = JSON.parse(this.response);
                let instructions = parsed['data']['threaded_conversation_with_injections_v2']['instructions']
                for (let i of instructions)
                {
//                    'TimelineAddToModule'
                    if (i['type'] === 'TimelineAddEntries')
                    {
                        console.log(i);
                        items = i['entries']
                        currentEntries = currentEntries.concat(items);
                    }
                }
            }

            if (currentEntries.length > 0) {
                window.interceptedTwitterData = window.interceptedTwitterData.concat(currentEntries); // Push the batch of entries
                 console.log('Added ' + currentEntries.length + ' entries. Total batches: ' + window.interceptedTwitterData.length);
            }
        });
        return originalOpen.apply(this, arguments);
    };
    console.log("Twitter XHR Hook activated.");
})();