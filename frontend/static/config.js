// config.js
const isRender = window.location.hostname === "mysteelvn.onrender.com";

const hostname = isRender
  ? "mysteelvn.onrender.com"
  : "127.0.0.1:8000";

const protocol = isRender ? "https" : "http";

export const hosting = `${protocol}://${hostname}`
