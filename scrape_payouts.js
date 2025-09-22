/*
  Scrapes payout tables from apextraderfunding.com across pages 1..307
  and writes results to payouts.csv with proper CSV escaping.
*/

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const START_PAGE = 1;
const END_PAGE = 307;
const BASE_URL = 'https://apextraderfunding.com/payouts?p=';
const OUTPUT_CSV = path.resolve(__dirname, 'payouts.csv');

function csvEscape(value) {
  if (value === null || value === undefined) return '';
  const stringValue = String(value).replace(/\r?\n|\r/g, ' ').trim();
  if (stringValue.includes('"') || stringValue.includes(',') || stringValue.includes('\n')) {
    return '"' + stringValue.replace(/"/g, '""') + '"';
  }
  return stringValue;
}

async function extractTable(page) {
  return page.evaluate(() => {
    function text(el) {
      return (el?.textContent || '').replace(/\s+/g, ' ').trim();
    }

    // 1) Try real <table>
    const table = document.querySelector('table');
    if (table) {
      const headerCells = Array.from(table.querySelectorAll('thead tr th'));
      const headers = headerCells.length
        ? headerCells.map(th => text(th))
        : Array.from(table.querySelectorAll('tr:first-child th, tr:first-child td')).map(el => text(el));

      const dataRows = [];
      const bodyRows = table.querySelectorAll('tbody tr');
      const rows = bodyRows.length ? bodyRows : table.querySelectorAll('tr');
      rows.forEach((tr, idx) => {
        if (!bodyRows.length && idx === 0) return; // skip header duplicate
        const cells = Array.from(tr.querySelectorAll('td')).map(td => text(td));
        if (cells.length) dataRows.push(cells);
      });
      return { headers, rows: dataRows };
    }

    // 2) Try div-based table: .divTable.PA
    const container = document.querySelector('.divTable.PA, div.divTable.PA');
    if (container) {
      // Headers might be in a heading row or first row
      let headers = Array.from(container.querySelectorAll('.divTableHeading .divTableHead'))
        .map(h => text(h));
      if (!headers.length) {
        const firstRowCells = container.querySelectorAll('.divTableRow:first-child .divTableCell');
        headers = Array.from(firstRowCells).map(c => text(c));
      }

      const rows = [];
      const allRows = Array.from(container.querySelectorAll('.divTableBody .divTableRow, .divTableRow'));
      const startIndex = (headers.length && allRows.length) ? 1 : 0; // skip first if used as header
      for (let i = startIndex; i < allRows.length; i++) {
        const r = allRows[i];
        const cells = Array.from(r.querySelectorAll('.divTableCell, .divTableHead')).map(c => text(c));
        if (cells.length) rows.push(cells);
      }
      return { headers, rows };
    }

    return { headers: [], rows: [] };
  });
}

async function waitForTableOrEnd(page) {
  try {
    await page.waitForSelector('table, .divTable.PA', { timeout: 20000 });
    // Wait for rows within the container as well
    await page.waitForSelector('tbody tr, .divTable.PA .divTableRow', { timeout: 20000 });
  } catch (e) {
    // Continue even if not found; extractor will handle empty
  }
}

async function run() {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36');
  await page.setViewport({ width: 1280, height: 800 });

  const csvStream = fs.createWriteStream(OUTPUT_CSV, { encoding: 'utf8' });
  let wroteHeader = false;
  let headerColumns = [];

  try {
    for (let p = START_PAGE; p <= END_PAGE; p++) {
      const url = BASE_URL + p;
      console.log(`Navigating to ${url}`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await waitForTableOrEnd(page);

      // Some pages may hydrate content; attempt minimal wait for network
      try {
        await page.waitForNetworkIdle({ idleTime: 750, timeout: 15000 });
      } catch (_) {}

      const { headers, rows } = await extractTable(page);
      if (!headers.length && !rows.length) {
        console.warn(`No table found on page ${p}`);
        continue;
      }

      if (!wroteHeader) {
        headerColumns = headers.length ? headers : rows[0].map((_, i) => `col_${i + 1}`);
        csvStream.write(headerColumns.map(csvEscape).join(',') + '\n');
        wroteHeader = true;
      }

      for (const row of rows) {
        const normalized = row.slice(0, headerColumns.length);
        while (normalized.length < headerColumns.length) normalized.push('');
        csvStream.write(normalized.map(csvEscape).join(',') + '\n');
      }
    }
    console.log(`Finished. CSV written to ${OUTPUT_CSV}`);
  } catch (err) {
    console.error('Error during scraping:', err);
  } finally {
    await page.close().catch(() => {});
    await browser.close().catch(() => {});
    csvStream.end();
  }
}

if (require.main === module) {
  run();
}



