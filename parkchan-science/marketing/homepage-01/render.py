import asyncio
from playwright.async_api import async_playwright
IDS=['profile_A','profile_B','title_A','title_B','pv_A','pv_B','mcover_A','mcover_B']+[f'b{n}_{v}' for v in 'AB' for n in range(1,6)]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium');pg=await b.new_page(viewport={'width':1400,'height':900})
        import pathlib;await pg.goto('file://'+str(pathlib.Path('home.html').resolve()));await pg.wait_for_timeout(500)
        for i in IDS: await pg.locator('#'+i).screenshot(path=f'out/{i}.png')
        await b.close()
import os;os.makedirs('out',exist_ok=True);asyncio.run(main())
