async function scroll_top()
{
    let last_height = 0
    let max_height = 0
    window.scroll_finished = false

    // keep trying to scroll every 500ms
    let handle = setInterval(function()
    {
        window.scrollBy({
		    top: window.scrollY + 1500,
            behavior: "smooth"
		});

		const btn = [...document.querySelectorAll('button')].find(b => /show replies/i.test(b.textContent) || /show probable spam/i.test(b.textContent));

        btn?.click();
    }, 2000);

    // if the scroll height hasn't changed for 10s, we are done
    while (true)
    {
        last_height = window.scrollY

//        await new Promise(resolve => setTimeout(resolve, 120000));
        await new Promise(resolve => setTimeout(resolve, 15000));

        if (window.scrollY === last_height)
        {
            clearInterval(handle);
            window.scroll_finished = true
            console.log('Finished!')
            return Promise.resolve("Finished")
        }
    }
}
scroll_top()
