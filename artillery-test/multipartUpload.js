const fs = require('fs');
const path = require('path');

module.exports = {
  multipartUpload: function (requestParams, context, ee, next) {
    const boundary = '----MyBoundary';
    const filepath = path.resolve(__dirname, 'test.pdf');
    const fileContent = fs.readFileSync(filepath);
    const username = context.vars.username || 'unknown';

    const body = Buffer.concat([
      Buffer.from(
        `--${boundary}\r\n` +
        `Content-Disposition: form-data; name="username"\r\n\r\n` +
        `${username}\r\n`
      ),
      Buffer.from(
        `--${boundary}\r\n` +
        `Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n` +
        `Content-Type: application/pdf\r\n\r\n`
      ),
      fileContent,
      Buffer.from(`\r\n--${boundary}--\r\n`)
    ]);

    requestParams.body = body;
    requestParams.headers['Content-Type'] = `multipart/form-data; boundary=${boundary}`;
    return next();
  }
};
