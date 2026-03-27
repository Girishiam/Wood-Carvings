# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-03-28

### Added - Render Deployment Optimization
- Created `render.yaml` for one-click deployment to Render
- Added `Dockerfile` for containerized deployment
- Implemented production CORS configuration with environment variable support
- Created comprehensive deployment documentation (`DEPLOYMENT.md`)
- Added frontend production configuration (`frontend/src/config.js`)
- Created `.dockerignore` to optimize Docker builds
- Added `.env.production` template for production environment variables
- Created `Procfile` for easy deployment
- Added `healthcheck.py` for service monitoring
- Created `start.sh` production startup script
- Added `runtime.txt` for Python version specification
- Organized development scripts into `scripts/` folder
- Updated `.gitignore` to exclude deployment artifacts and build files
- Enhanced frontend build configuration in `vite.config.js`
- Created comprehensive `README.md` with quick start guide

### Changed
- Updated main.py to use environment-based CORS origins
- Optimized project structure for production deployment
- Moved utility scripts to dedicated `scripts/` folder
- Enhanced frontend API configuration for environment-based URL handling

### Improved
- Project structure organization
- Documentation completeness
- Deployment process
- Security configuration
- Build optimization

### Security
- Environment-based CORS configuration
- Excluded sensitive files from Docker builds
- Service account authentication for GCP
- Proper environment variable management

## [0.1.0] - Initial Release

### Added
- FastAPI backend with Vertex AI integration
- React frontend with Vite
- 4-view character sheet generation
- Sketch and color rendering modes
- Difficulty level system (Beginner, Intermediate, Professional)
- Imagen 3 and Imagen 4 support
- Artist style guide integration
- Cache management system
