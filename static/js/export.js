/**
 * STATAU 导出功能模块
 * 支持导出为 Word、Excel、TXT、CSV 格式
 */

// 全局配置
const EXPORT_CONFIG = {
    defaultPrefix: 'STATAU_Results',
    word: { orientation: 'portrait' },
    excel: { sheetName: 'Results', columnWidth: 15 },
    txt: { columnWidth: 15, separator: '  ' }
};

// 生成时间戳
function getTimestamp() {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}_${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}${String(now.getSeconds()).padStart(2,'0')}`;
}

// 获取当前激活的模块
function getCurrentActiveModule() {
    const activeModule = document.querySelector('.analysis-module.active');
    return activeModule;
}

// 获取当前可见的表格（只从当前激活模块中查找）
function getCurrentTable() {
    const activeModule = getCurrentActiveModule();
    if (!activeModule) {
        return null;
    }
    
    // 在激活模块中查找可见的结果容器
    const resultContainer = activeModule.querySelector('[id$="-result-container"]');
    if (!resultContainer || resultContainer.style.display === 'none') {
        return null;
    }
    
    // 优先查找 academic-table
    let table = resultContainer.querySelector('.academic-table');
    if (table) return table;
    
    // 查找普通table
    table = resultContainer.querySelector('table');
    if (table) return table;
    
    return null;
}

// 获取表格标题
function getTableTitle() {
    const activeModule = getCurrentActiveModule();
    if (!activeModule) {
        return EXPORT_CONFIG.defaultPrefix;
    }
    
    // 在激活模块中查找可见的结果容器
    const resultContainer = activeModule.querySelector('[id$="-result-container"]');
    if (!resultContainer || resultContainer.style.display === 'none') {
        return EXPORT_CONFIG.defaultPrefix;
    }
    
    // 查找 table-title-input
    const titleInput = resultContainer.querySelector('.table-title-input');
    if (titleInput && titleInput.value) {
        return titleInput.value;
    }
    
    // 查找卡片标题
    const cardTitle = resultContainer.querySelector('.card-title, h5, h6');
    if (cardTitle) {
        return cardTitle.textContent.trim();
    }
    
    return EXPORT_CONFIG.defaultPrefix;
}

// 生成文件名
function generateFilename(ext) {
    const title = getTableTitle();
    const cleanTitle = title.replace(/[<>:"/\\|?*]/g, '_');
    return `${cleanTitle}_${getTimestamp()}.${ext}`;
}

// 检查表格是否存在
function hasExportableTable() {
    const table = getCurrentTable();
    if (!table) {
        alert('没有可导出的结果表格');
        return false;
    }
    return true;
}

// 导出为Word
function exportToWord() {
    if (!hasExportableTable()) return;
    try {
        const table = getCurrentTable();
        const title = getTableTitle();
        
        // 克隆表格以便处理
        const tableClone = table.cloneNode(true);
        
        // 提取注释内容（从tfoot的最后一行）
        let notes = '';
        const tfoot = tableClone.querySelector('tfoot');
        if (tfoot) {
            const lastRow = tfoot.querySelector('tr:last-child');
            if (lastRow) {
                const noteCell = lastRow.querySelector('td[colspan]');
                if (noteCell) {
                    notes = noteCell.innerHTML;
                    // 移除注释行
                    lastRow.remove();
                }
            }
        }
        
        // 确保thead有上边框
        const thead = tableClone.querySelector('thead');
        if (thead) {
            const firstRow = thead.querySelector('tr:first-child');
            if (firstRow) {
                const cells = firstRow.querySelectorAll('th');
                cells.forEach(cell => {
                    const currentStyle = cell.getAttribute('style') || '';
                    if (!currentStyle.includes('border-top')) {
                        cell.setAttribute('style', currentStyle + '; border-top: 1px solid black;');
                    }
                });
            }
        }
        
        // 确保tfoot第一行有上边框
        if (tfoot) {
            const firstRow = tfoot.querySelector('tr:first-child');
            if (firstRow) {
                const cells = firstRow.querySelectorAll('td');
                cells.forEach(cell => {
                    const currentStyle = cell.getAttribute('style') || '';
                    if (!currentStyle.includes('border-top')) {
                        cell.setAttribute('style', currentStyle + '; border-top: 1px solid black;');
                    }
                });
            }
            
            // 确保tfoot最后一行有下边框
            const lastRow = tfoot.querySelector('tr:last-child');
            if (lastRow) {
                const cells = lastRow.querySelectorAll('td');
                cells.forEach(cell => {
                    const currentStyle = cell.getAttribute('style') || '';
                    if (!currentStyle.includes('border-bottom')) {
                        cell.setAttribute('style', currentStyle + '; border-bottom: 1px solid black;');
                    }
                });
            }
        }
        
        const htmlContent = `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>${title}</title>
<style>
body {
    font-family: 'Times New Roman', serif;
    font-size: 12pt;
    margin: 1in;
    line-height: 1.0;
}
h1 {
    text-align: center;
    font-size: 14pt;
    font-weight: bold;
    margin-bottom: 20px;
    line-height: 1.0;
}
table {
    border-collapse: collapse;
    width: 80%;
    margin: 20px auto;
    line-height: 1.0;
}
th, td {
    padding: 6px 8px;
    text-align: center;
    line-height: 1.0;
    margin: 0;
}
th {
    font-weight: bold;
}
td:first-child, th:first-child {
    text-align: left;
}
.notes {
    width: 80%;
    margin: 10px auto 0 auto;
    font-size: 10pt;
    text-align: left;
    line-height: 1.0;
}
</style></head><body>
<h1>${title}</h1>
${tableClone.outerHTML}
${notes ? `<div class="notes">${notes}</div>` : ''}
</body></html>`;
        
        const converted = htmlDocx.asBlob(htmlContent);
        saveAs(converted, generateFilename('docx'));
        console.log('Word导出成功');
    } catch (error) {
        alert('Word导出失败: ' + error.message);
        console.error(error);
    }
}

// 导出为Excel
function exportToExcel() {
    if (!hasExportableTable()) return;
    try {
        const table = getCurrentTable();
        const wb = XLSX.utils.table_to_book(table, {sheet: EXPORT_CONFIG.excel.sheetName});
        const ws = wb.Sheets[EXPORT_CONFIG.excel.sheetName];
        
        const range = XLSX.utils.decode_range(ws['!ref']);
        const cols = [];
        for (let C = range.s.c; C <= range.e.c; ++C) {
            cols.push({wch: EXPORT_CONFIG.excel.columnWidth});
        }
        ws['!cols'] = cols;
        
        XLSX.writeFile(wb, generateFilename('xlsx'));
        console.log('Excel导出成功');
    } catch (error) {
        alert('Excel导出失败: ' + error.message);
        console.error(error);
    }
}

// 导出为TXT
function exportToTxt() {
    if (!hasExportableTable()) return;
    try {
        const table = getCurrentTable();
        const title = getTableTitle();
        const rows = table.querySelectorAll('tr');
        const lines = [title, '='.repeat(title.length), ''];
        
        rows.forEach((row, idx) => {
            const cells = row.querySelectorAll('th, td');
            const texts = Array.from(cells).map((cell, i) => {
                let text = cell.textContent.trim().replace(/\n/g, ' ').replace(/\s+/g, ' ');
                return i === 0 ? text.padEnd(EXPORT_CONFIG.txt.columnWidth) : text.padStart(EXPORT_CONFIG.txt.columnWidth);
            });
            lines.push(texts.join(EXPORT_CONFIG.txt.separator));
            if (idx === 0) lines.push('-'.repeat(texts.join(EXPORT_CONFIG.txt.separator).length));
        });
        
        lines.push('', `Exported from STATAU at ${new Date().toLocaleString('zh-CN')}`);
        const blob = new Blob([lines.join('\n')], {type: 'text/plain;charset=utf-8'});
        saveAs(blob, generateFilename('txt'));
        console.log('TXT导出成功');
    } catch (error) {
        alert('TXT导出失败: ' + error.message);
        console.error(error);
    }
}

// 导出为CSV
function exportToCSV() {
    if (!hasExportableTable()) return;
    try {
        const table = getCurrentTable();
        const rows = table.querySelectorAll('tr');
        const csvLines = [];
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('th, td');
            const texts = Array.from(cells).map(cell => {
                let text = cell.textContent.trim();
                if (text.includes(',') || text.includes('"') || text.includes('\n')) {
                    text = '"' + text.replace(/"/g, '""') + '"';
                }
                return text;
            });
            csvLines.push(texts.join(','));
        });
        
        const blob = new Blob(['\ufeff' + csvLines.join('\n')], {type: 'text/csv;charset=utf-8'});
        saveAs(blob, generateFilename('csv'));
        console.log('CSV导出成功');
    } catch (error) {
        alert('CSV导出失败: ' + error.message);
        console.error(error);
    }
}

// 更新导出按钮的显示状态
function updateExportButtonsVisibility() {
    const activeModule = getCurrentActiveModule();
    
    // 隐藏所有导出按钮
    const allExportButtons = document.querySelectorAll('[id^="export-buttons"]');
    allExportButtons.forEach(btn => {
        if (btn.style.display !== 'none') {
            btn.style.display = 'none';
        }
    });
    
    // 只显示当前激活模块的导出按钮
    if (activeModule) {
        const resultContainer = activeModule.querySelector('[id$="-result-container"]');
        if (resultContainer && resultContainer.style.display !== 'none') {
            const exportButtons = resultContainer.querySelector('[id^="export-buttons"]');
            const hasTable = resultContainer.querySelector('table') !== null;
            
            if (exportButtons && hasTable && exportButtons.style.display !== 'block') {
                exportButtons.style.display = 'block';
            }
        }
    }
}

// 初始化
function initExportFunctions() {
    console.log('导出功能已加载');
    
    // 使用防抖来避免频繁触发
    let updateTimeout = null;
    const debouncedUpdate = function() {
        if (updateTimeout) {
            clearTimeout(updateTimeout);
        }
        updateTimeout = setTimeout(updateExportButtonsVisibility, 100);
    };
    
    // 监听所有结果容器的变化
    const containers = document.querySelectorAll('[id$="-result-container"]');
    containers.forEach(container => {
        const observer = new MutationObserver(debouncedUpdate);
        observer.observe(container, {
            attributes: true,
            attributeFilter: ['style'],
            childList: true
        });
    });
    
    // 初始化时更新一次
    updateExportButtonsVisibility();
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initExportFunctions);
} else {
    initExportFunctions();
}
