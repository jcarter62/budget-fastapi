
function fmtAcctNum(value) {
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
