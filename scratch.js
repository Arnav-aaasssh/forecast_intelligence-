
window.onerror = function(message, source, lineno, colno, error) {
  const errDiv = document.createElement('div');
  errDiv.style = 'background:red;color:white;position:fixed;top:0;left:0;z-index:9999;padding:20px;';
  errDiv.innerText = message + ' at ' + lineno + ':' + colno + ' ' + (error ? error.stack : '');
  document.body.appendChild(errDiv);
};
window.addEventListener('unhandledrejection', function(event) {
  const errDiv = document.createElement('div');
  errDiv.style = 'background:red;color:white;position:fixed;top:0;left:0;z-index:9999;padding:20px;';
  errDiv.innerText = 'Unhandled Promise Rejection: ' + event.reason;
  document.body.appendChild(errDiv);
});
