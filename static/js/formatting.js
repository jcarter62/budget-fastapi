
function fmtAcctNum(value) {
    // Accounting number format
    // Formats a number in accounting style: negative numbers are enclosed in parentheses

    if (value === null || value === undefined || isNaN(value)) {
        return '';
    }
    const num = parseFloat(value);
    const absNum = Math.abs(num);
    const isNegative = num < 0;
    let result = '';

    // If the absolute value is less than or equal to 0.0005, return a dash
    if (absNum <= 0.0005) {
        result = '-';
    } else {
        const formattedNumber = absNum.toLocaleString(
            undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        if (isNegative) {
            result = `(${formattedNumber})`;
        } else {
            result = formattedNumber;
        }
    }
    return result;
}

function fmtRJColumn(value, currencyChar = ' ') {
    // Right-justified column format with $ sign to left.
    const actual = fmtAcctNum(value);
    let rightChar = '&nbsp;';
    let result = '';
    let currencyText = '';

    if (actual === '-') {
        currencyText = '&nbsp;';
    } else {
        currencyText = '&nbsp;' + currencyChar;
    }
    // if last character of actual is ")", then set rightChar to ''
    if (actual.endsWith(')')) {
        rightChar = '';
    }

    if ( currencyChar === null || currencyChar === ' ' || currencyChar === '') {
        result += `<span style="display: flex; justify-content: space-between; width:100%;">`;
        result += `<span style="text-align: right; flex:1;">${actual}${rightChar}</span>`;
        result += `</span>`;
    } else {
        result += `<span style="display: flex; justify-content: space-between; width:100%;">`;
        result += `<span style="text-align: left;">${currencyText}</span>`;
        result += `<span style="text-align: right; flex:1;">${actual}${rightChar}</span>`;
        result += `</span>`;
    }

    return result;
}
