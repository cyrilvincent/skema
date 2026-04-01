import asyncio

from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 800, "height": 1024})
        page = await context.new_page()
        await page.goto("https://www.doctolib.fr/search?keyword=dermatologue&location=france&page=1&availabilitiesBefore=14")
        input("Cookies")
        print("await1")
        await page.wait_for_selector("footer")
        print("footer")
        content = await page.content()
        print(content)
        with open("out.html", "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == '__main__':
    asyncio.run(test())
