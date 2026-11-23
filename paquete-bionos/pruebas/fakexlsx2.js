window.XLSX = {utils: {book_new: () => ({SheetNames: [], Sheets: {}}), aoa_to_sheet: rows => ({rows}), book_append_sheet: (wb, ws, n) => { wb.SheetNames.push(n); wb.Sheets[n] = ws; },
  sheet_to_json: (ws, o) => ws.rows},
  write: wb => new TextEncoder().encode(JSON.stringify(wb)).buffer,
  read: buf => JSON.parse(new TextDecoder().decode(new Uint8Array(buf)))};
