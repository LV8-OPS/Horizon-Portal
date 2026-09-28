const enabled = (typeof process !== 'undefined' && process.env && process.env.NODE_ENV) !== 'production';
const marks = new Map();
export const perf = { enabled, mark:k=>enabled&&marks.set(k, performance.now()), measure:k=>enabled&&marks.has(k)?Math.round(performance.now()-marks.get(k)):null, report:d=>enabled&&console.debug('[PERF]', d) };
