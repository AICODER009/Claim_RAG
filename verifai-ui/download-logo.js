const https = require('https');
const fs = require('fs');
const path = require('path');

const url = 'https://picsvg.com/svg/myFPI.jpg';
const dest = path.join(__dirname, 'public', 'logo.png');

https.get(url, (res) => {
  const out = fs.createWriteStream(dest);
  res.pipe(out);
  out.on('finish', () => {
    out.close();
    console.log('Logo saved:', fs.statSync(dest).size, 'bytes');
  });
}).on('error', (e) => {
  console.error('Error:', e.message);
});
