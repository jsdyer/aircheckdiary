from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def main():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / 'aircheckdiary').symlink_to(ROOT / 'dist', target_is_directory=True)
        server = ThreadingHTTPServer(('127.0.0.1',0), partial(Quiet, directory=tmp))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=os.getenv('AIR_CHROMIUM'))
                page = browser.new_page(viewport={'width':1280,'height':900})
                errors=[]
                page.on('pageerror',lambda exc: errors.append(str(exc)))
                page.goto(f'http://127.0.0.1:{server.server_port}/aircheckdiary/')
                titles = page.locator('.slot h3')
                expect(titles).to_have_text(['Password','Jeopardy! Masters'])
                page.locator('.detail summary').first.click()
                expect(page.locator('.rawrow').first).to_contain_text('#731')
                page.locator('#time').select_option('79200')
                expect(titles).to_have_text(['Jeopardy! Masters','Password'])
                page.locator('#a').select_option('CBHT')
                page.locator('#b').select_option('CBUT')
                page.locator('#time').select_option('72000')
                expect(titles).to_have_text(['Still Standing','Still Standing'])
                page.locator('#query').fill('Password')
                expect(page.locator('.hit').first).to_contain_text('Password')
                page.locator('.hit').first.click()
                expect(titles.first).to_have_text('Password')
                link=page.url
                page.goto(link)
                expect(titles.first).to_have_text('Password')
                (ROOT / 'browser-checks').mkdir(exist_ok=True)
                page.screenshot(path=ROOT/'browser-checks/desktop.png')
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=ROOT/'browser-checks/mobile.png')
                assert not errors, errors
                browser.close()
        finally:
            server.shutdown()
if __name__ == '__main__':
    main()
