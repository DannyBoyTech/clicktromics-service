import asyncio
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
import random
from src.logger import Logger
from typing import List, Dict, Optional
from datetime import datetime
import json

logger = Logger.get_logger()

class AdvancedScraper:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15...",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0..."
    ]

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def _configure_browser(self):
        """Configure and return new browser and context instances"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        context = await browser.new_context(
            user_agent=random.choice(self.USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            bypass_csp=True
        )
        await context.add_init_script("""
            delete Object.getPrototypeOf(navigator).webdriver;
        """)
        return browser, context

    async def _scrape_page(
        self, 
        context,  # Add context parameter
        url: str,
        wait_selector: str = None,
        timeout: int = 500,
        max_retries: int = 3
    ) -> Optional[HTMLParser]:
        """
        Generalized page scraper with intelligent waiting
        
        Args:
            url: Target URL to scrape
            wait_selector: CSS selector to wait for (None for no waiting)
            timeout: Maximum wait time in milliseconds
            max_retries: Number of retry attempts
            
        Returns:
            HTMLParser object or None if failed
        """
        for attempt in range(1, max_retries + 1):
            page = None
            try:
                page = await context.new_page()
                
                # Human-like interaction pattern
                await page.mouse.move(
                    random.randint(0, 500),
                    random.randint(0, 500)
                )
                
                await page.goto(url, timeout=timeout)
                
                if wait_selector:
                    try:
                        await page.wait_for_selector(
                            f"{wait_selector}:visible",
                            timeout=timeout,
                            state="attached"
                        )
                    except Exception as e:
                        logger.warning(f"Primary wait failed ({attempt}/{max_retries}): {e}")
                        if await page.query_selector(wait_selector):
                            logger.info("Element found in DOM without visibility")
                        else:
                            raise

                await self._simulate_human_interaction(page)
                
                content = await page.content()
                dom = HTMLParser(content)
                
                if wait_selector and not dom.css(wait_selector):
                    raise Exception("Target selector missing from parsed DOM")
                    
                return dom
                
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {str(e)}")
                await self._capture_debug_screenshot(page)
                if attempt == max_retries:
                    return None
                await asyncio.sleep(2 ** attempt)
            finally:
                if page:
                    await page.close()
        return None


    async def _simulate_human_interaction(self, page):
        """Simulate natural browsing patterns"""
        # Random scroll pattern
        for _ in range(random.randint(1, 4)):
            await page.mouse.wheel(0, random.randint(300, 1000))
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Random mouse movements
        for _ in range(random.randint(2, 5)):
            x = random.randint(0, 1200)
            y = random.randint(0, 800)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.7))
        
        # Random click simulation
        if random.random() < 0.3:
            await page.mouse.click(
                random.randint(0, 1200),
                random.randint(0, 800),
                delay=random.randint(50, 200)
            )

    async def _capture_debug_screenshot(self, page):
        try:
            if page:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"debug_{timestamp}.png", full_page=True)
                logger.info(f"Saved debug screenshot: debug_{timestamp}.png")
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")

    async def fetch_from_abcam(self, gene: str) -> Optional[Dict]:
        browser, context = await self._configure_browser()
        try:
            dom = await self._scrape_page(
                context=context,
                url=f"https://www.abcam.com/en-us/search?productSorting=relevance&resourceSorting=relevance&keywords={gene}%2Bpeptide",
                wait_selector="body"
            )

            if not dom:
                return []

            # Find the <script id="__NEXT_DATA__"> node
            script = dom.css_first('script#__NEXT_DATA__')
            if not script:
                logger.error("Could not find __NEXT_DATA__ script")
                return []

            # Get the JSON text, parse it
            raw = script.text()  # contains the full JSON string
            data = json.loads(raw)
            proteins = []
            items = (
                data
                .get("props", {})
                .get("pageProps", {})
                .get("searchResults", {})
                .get("items", [])
            )

            # 2) for each hit, filter by target & then visit detail page
                    
            for item in items:
                logger.info(item)
                targets = []
                for target in item.get("targets", []):
                    for target_without_aliases in target.split("/"):
                        targets.append(target_without_aliases.strip().upper())

                if gene not in targets:
                    continue

                prod_id   = item.get("productSlug")
                detail_url = f"https://www.abcam.com/en-us/products/proteins-peptides/{prod_id}"

                page = await context.new_page()
                try:
                    await page.goto(detail_url, timeout=500)
                    seq_el = await page.wait_for_selector(
                        'xpath=//h3[normalize-space(text())="Amino acid sequence"]/following-sibling::p',
                        timeout=500
                    )

                    raw_seq = await seq_el.inner_text()
                    # collapse whitespace so it’s just a space‑separated string
                    sequence = " ".join(raw_seq.split())

                    desc_el = await page.wait_for_selector(
                        'css=div.overview_description-format__7E89b > p',
                        timeout=500
                    )
                    description = (await desc_el.inner_text()).strip()

                    proteins.append({
                        "id":           prod_id,
                        "name":         item.get("productName"),
                        "applications": item.get("applications"),
                        "targets":      item.get("targets"),
                        "form":         item.get("form"),
                        "sequence":     sequence.replace(" ", ""),
                        "description":  description,
                        "source": "abcam"
                    })

                except Exception as e:
                    logger.warning(f"Failed to fetch sequence for {prod_id}: {e}")
                finally:
                    await page.close()

            logger.info(f"Found {len(proteins)} items from abcam ")
            return proteins

        finally:
            await context.close()
            await browser.close()




    async def fetch_from_medchem(self, gene: str) -> Optional[List[Dict[str, str]]]:
        async def _scrape_sequence_shortening(context, path: str) -> Optional[str]:
            """Scrape sequence information from product detail page"""
            try:
                full_url = f"https://www.medchemexpress.com{path}"
                detail_page = await context.new_page()
            
                try:
                    await detail_page.goto(full_url, timeout=500)
                    seq_element = await detail_page.wait_for_selector(
                        '//tr[th[contains(@class, "details_info_th") and contains(., "Sequence Shortening")]]/td',
                        timeout=500,
                        state="attached"
                    )
                    
                    if not seq_element:
                        return None

                    sequence = await seq_element.inner_text()
                    return sequence.strip().replace('\u200e', '').replace('\n', '') or None
                    
                finally:
                    await detail_page.close()

            except Exception as e:
                logger.warning(f"Failed to get sequence for {path}: {str(e)}")
                return None
        
        url = f"https://www.medchemexpress.com/search.html?q={gene}&ft=&fa=&fp=&fsp=&ftag=&fsc=&fcc=&fol=&type=peptides"
        browser, context = await self._configure_browser()
        try:
            dom = await self._scrape_page(
                context=context,
                url=url,
                wait_selector="div.search_type_list_content ul.srh_rst_list_con"
            )
            
            if not dom:
                logger.error("Failed to retrieve DOM")
                return []

            # Find active tab using CSS selector
            active_title = dom.css_first('div.search_type_title > div.active')
            if not active_title:
                logger.error("No active product category tab found")
                return None

            # Get all title elements and find the active index
            titles = dom.css('div.search_type_title > div')
            try:
                active_index = titles.index(active_title)
            except ValueError:
                logger.error("Active tab not found in titles list")
                return None

            # Get corresponding content container
            containers = dom.css('div.search_type_list_content')
            try:
                container = containers[active_index]
            except IndexError:
                logger.error(f"No container found for active index {active_index}")
                return None

            # Get the specific UL within the third container
            product_list = container.css_first('ul.srh_rst_list_con')
            if not product_list:
                logger.error("srh_rst_list_con not found in third container")
                return []

            results = []
            for product in product_list.css('li'):
                try:
                    # Extract from nested table structure
                    table = product.css_first('table.srh_rst_list_tbl')
                    if not table:
                        continue
                    
                    href = self._safe_attr(table, 'th.s_pro_list_name a', 'href')
                    sequence = await _scrape_sequence_shortening(context, href)

                    result = {
                        'cat_no': self._safe_extract(product, 'dt.s_pro_list_cat a'),
                        'name': self._safe_extract(table, 'th.s_pro_list_name a strong'),
                        'href': href,
                        'targets': [
                            self._clean_text(span.text())
                            for span in table.css('th.s_pro_list_type a span')
                        ],
                        'research_areas': [
                            self._clean_text(span.text())
                            for span in table.css('th.s_pro_list_research a span')
                        ],
                        'brief': self._safe_extract(table, 'td.s_pro_list_brief'),
                        'sequence': sequence,
                        "source": "medchemexpress"
                    }

                    # Validate required fields
                    if result['name'] and result['href']:
                        results.append(result)

                except Exception as e:
                    logger.warning(f"Skipping product: {str(e)}")
                    continue

            logger.info(f"Found {len(results)} items from medchemexpress ")
            return results

        finally:
            await context.close()
            await browser.close()



    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        return text.strip().replace('\u200e', '') if text else ''

    def _safe_extract(self, node, selector: str) -> str:
        return (node.css_first(selector).text(strip=True) 
                if node.css_first(selector) else '')

    def _safe_attr(self, node, selector: str, attr: str) -> str:
        return (node.css_first(selector).attributes.get(attr, '')
                if node.css_first(selector) else '')

    async def _cleanup(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()