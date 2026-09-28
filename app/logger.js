const env = (typeof process !== 'undefined' && process.env && process.env.NODE_ENV) || 'development';
const levels = { debug: 10, info: 20, success: 25, warn: 30, error: 40 };
const active = env === 'development' ? levels.debug : levels.info;
const ts = () => new Date().toISOString().replace('T',' ').replace('Z','');
const sanitize = v => String(v ?? '').replace(/(password|token|api[_-]?key|cookie)\s*[:=]\s*[^\s]+/ig, '$1=[redacted]');
const emit = (lvl, mod, msg, data) => { if (levels[lvl] < active) return; const base = `[${ts()}] [${lvl.toUpperCase()}] [${mod}] ${sanitize(msg)}`; data !== undefined ? console.log(base, data) : console.log(base); };
export const logger = { debug:(m,msg,d)=>emit('debug',m,msg,d), info:(m,msg,d)=>emit('info',m,msg,d), success:(m,msg,d)=>emit('success',m,msg,d), warn:(m,msg,d)=>emit('warn',m,msg,d), error:(m,msg,e)=>emit('error',m,`${msg}${e?` | ${sanitize(e.message || e)}`:''}`, e?.stack) };
