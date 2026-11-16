import asyncio,os,pathlib
from playwright.async_api import async_playwright
async def m():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium');pg=await b.new_page(viewport={'width':1300,'height':900})
        await pg.goto('file://'+str(pathlib.Path('e.html').resolve()));await pg.wait_for_timeout(800)
        for i in ['tt','pv','mc','pf']+[f'b{n}' for n in range(1,6)]:
            await pg.locator('#'+i).screenshot(path=f'out/{i}.png')
        await b.close()
os.makedirs('out',exist_ok=True);asyncio.run(m())
