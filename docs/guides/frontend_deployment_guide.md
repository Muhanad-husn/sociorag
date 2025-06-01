# Frontend Deployment Guide

## Overview
This guide covers deployment strategies, environment configuration, and production optimization for the SocioRAG frontend application built with Preact + Vite.

## 🚀 Quick Deployment

### Production Build
```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Create production build
npm run build

# Preview build locally
npm run preview
```

The production build creates optimized assets in the `dist/` directory:
- **Bundle Size**: ~249.48 KB (93.81 KB gzipped)
- **Asset Optimization**: Minified CSS/JS, optimized images
- **Tree Shaking**: Unused code elimination
- **Code Splitting**: Automatic route-based splitting

## 🏗️ Build Configuration

### Environment Variables
Create environment files for different deployment stages:

**`.env.production`**
```env
VITE_API_BASE_URL=https://your-api-domain.com
VITE_API_VERSION=v1
VITE_ENABLE_ANALYTICS=true
VITE_SENTRY_DSN=your-sentry-dsn
```

**`.env.staging`**
```env
VITE_API_BASE_URL=https://staging-api.your-domain.com
VITE_API_VERSION=v1
VITE_ENABLE_ANALYTICS=false
```

**`.env.development`**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=v1
VITE_ENABLE_ANALYTICS=false
```

### Build Optimization
**`vite.config.ts`** optimizations:
```typescript
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';

export default defineConfig({
  plugins: [preact()],
  build: {
    // Optimize bundle size
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true
      }
    },
    // Enable gzip compression
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['preact', 'preact-router'],
          ui: ['lucide-preact', 'sonner']
        }
      }
    },
    // Optimize chunk size
    chunkSizeWarningLimit: 1000
  },
  // Enable source maps for debugging
  build: {
    sourcemap: process.env.NODE_ENV === 'development'
  }
});
```

## 🌐 Deployment Platforms

### Vercel (Recommended)
**Automatic Deployment from Git:**

1. **Connect Repository**:
   - Link GitHub/GitLab repository
   - Select `ui` as the root directory
   - Vercel auto-detects Vite configuration

2. **Environment Variables**:
   ```
   VITE_API_BASE_URL=https://your-api.vercel.app
   VITE_API_VERSION=v1
   ```

3. **Build Settings**:
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

4. **Domain Configuration**:
   - Custom domain setup
   - SSL/TLS certificates (automatic)
   - CDN optimization (automatic)

**`vercel.json` Configuration:**
```json
{
  "buildCommand": "cd ui && npm run build",
  "outputDirectory": "ui/dist",
  "installCommand": "cd ui && npm install",
  "framework": "vite",
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://your-backend-api.com/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### Netlify
**Deploy Configuration:**

1. **Build Settings**:
   - Build command: `cd ui && npm run build`
   - Publish directory: `ui/dist`

2. **Redirects** (`ui/public/_redirects`):
   ```
   # SPA routing
   /*    /index.html   200
   
   # API proxy
   /api/*  https://your-backend-api.com/api/:splat  200
   ```

3. **Headers** (`ui/public/_headers`):
   ```
   /*
     X-Frame-Options: DENY
     X-XSS-Protection: 1; mode=block
     X-Content-Type-Options: nosniff
     Referrer-Policy: strict-origin-when-cross-origin
   
   /assets/*
     Cache-Control: public, max-age=31536000, immutable
   ```

### Docker Deployment
**Multi-stage Dockerfile:**
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY ui/package*.json ./
RUN npm ci --only=production

COPY ui/ .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf:**
```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/javascript application/json;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend-api:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static assets caching
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "3000:80"
    environment:
      - NGINX_HOST=localhost
    depends_on:
      - backend
```

### AWS S3 + CloudFront
**S3 Static Hosting:**

1. **Build and Upload**:
   ```bash
   npm run build
   aws s3 sync dist/ s3://your-bucket-name --delete
   ```

2. **S3 Bucket Policy**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::your-bucket-name/*"
       }
     ]
   }
   ```

3. **CloudFront Distribution**:
   - Origin: S3 bucket
   - Default root object: `index.html`
   - Error pages: 404 → `/index.html` (for SPA routing)
   - Caching: Cache based on selected headers

## 🔧 CI/CD Pipeline

### GitHub Actions
**`.github/workflows/deploy.yml`:**
```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths: ['ui/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: ui/package-lock.json
    
    - name: Install dependencies
      run: cd ui && npm ci
    
    - name: Run tests
      run: cd ui && npm run test
    
    - name: Build
      run: cd ui && npm run build
      env:
        VITE_API_BASE_URL: ${{ secrets.API_BASE_URL }}
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID }}
        vercel-project-id: ${{ secrets.PROJECT_ID }}
        working-directory: ./ui
```

## 🔒 Security Configuration

### Content Security Policy
**Add to `index.html`:**
```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://your-api-domain.com wss://your-api-domain.com;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
">
```

### Environment Security
```typescript
// src/lib/config.ts
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  apiVersion: import.meta.env.VITE_API_VERSION || 'v1',
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  // Never expose sensitive data in frontend
  isDev: import.meta.env.DEV
};
```

## 📊 Performance Monitoring

### Bundle Analysis
```bash
# Analyze bundle size
npm run build
npx vite-bundle-analyzer dist

# Check for unused dependencies
npx depcheck
```

### Performance Metrics
- **Lighthouse Score**: Target 90+ for all metrics
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Bundle Size**: < 300KB total

### Monitoring Setup
```typescript
// src/lib/analytics.ts
export const trackPerformance = () => {
  if ('performance' in window && config.enableAnalytics) {
    window.addEventListener('load', () => {
      const perfData = performance.getEntriesByType('navigation')[0];
      console.log('Page Load Time:', perfData.loadEventEnd - perfData.fetchStart);
    });
  }
};
```

## 🔄 Health Checks

### Production Readiness Checklist
- [ ] All environment variables configured
- [ ] API endpoints accessible
- [ ] SSL/TLS certificates valid
- [ ] CDN/caching configured
- [ ] Error monitoring (Sentry) enabled
- [ ] Performance monitoring active
- [ ] Backup strategy in place

### Health Check Endpoint
```typescript
// Health check for load balancers
if (location.pathname === '/health') {
  document.body.innerHTML = 'OK';
}
```

## 🚨 Troubleshooting

### Common Issues

**Build Fails:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Environment Variables Not Working:**
- Ensure variables start with `VITE_`
- Check `.env` file location
- Verify build process includes env vars

**404 on Refresh:**
- Configure SPA routing redirects
- Check server/hosting platform settings
- Verify `index.html` fallback

**API Connection Issues:**
- Check CORS configuration on backend
- Verify environment-specific API URLs
- Test API endpoints independently

### Performance Issues
- Enable gzip compression
- Optimize images and assets
- Implement lazy loading
- Use CDN for static assets
- Monitor Core Web Vitals

## 📝 Deployment Checklist

**Pre-deployment:**
- [ ] Code review completed
- [ ] Tests passing
- [ ] Environment variables configured
- [ ] API integration tested
- [ ] Performance optimized
- [ ] Security headers configured

**Post-deployment:**
- [ ] Health checks passing
- [ ] All routes accessible
- [ ] API connectivity verified
- [ ] Performance metrics within targets
- [ ] Error monitoring active
- [ ] Backup verified

## 🔗 Related Documentation
- [Frontend Development Guide](frontend_development_guide.md)
- [Phase 7 Implementation Summary](phase7_implementation_summary.md)
- [API Documentation](api_documentation.md)
- [UI Component Documentation](ui_component_documentation.md)
