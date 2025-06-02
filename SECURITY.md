# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within SocioRAG, please send an email to [security@yourcompany.com]. All security vulnerabilities will be promptly addressed.

Please do not report security vulnerabilities through public GitHub issues.

## Security Features

- **API Key Management**: Environment-based configuration
- **Input Validation**: Comprehensive sanitization of user inputs
- **Rate Limiting**: Built-in protection against abuse
- **Secure Headers**: CORS and security headers configured
- **Logging**: Security events are logged for monitoring

## Best Practices

1. **Never commit sensitive data** (API keys, passwords) to version control
2. **Use strong API keys** and rotate them regularly
3. **Monitor logs** for suspicious activity
4. **Keep dependencies updated** regularly
5. **Use HTTPS** in production environments
6. **Limit file upload sizes** and validate file types
7. **Implement proper access controls** for production deployments
