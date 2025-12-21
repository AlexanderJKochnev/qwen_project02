# wine_project01

This repository contains a full-stack application with a Preact frontend and Python backend.

## Frontend: preact_front

The frontend is built with Preact and includes:

- Internationalization (i18n) support for English and Russian
- Language context with automatic detection and localStorage persistence
- Comprehensive translation dictionary with common UI terms
- Responsive design with Tailwind CSS and DaisyUI

### Language Context Features

- Automatic language detection based on browser language
- Persistent language preference using localStorage
- Comprehensive translation dictionary with common UI terms
- Easy-to-use translation function

To run the frontend:

```bash
cd preact_front
npm install
npm run dev
```

## Backend

The backend is built with Python and includes various components for a complete web application.

## Database Translation Service

The application includes an automated translation service that:

- Automatically translates model names to Russian and French when records are created or updated
- Handles Russian noun cases for Food model entries
- Provides bulk translation for all existing database records
- Supports Country, Region, Subregion, Category, Subcategory, Food, and Varietal models
- Integrates seamlessly with the existing service layer

To run bulk translation of all existing records:

```bash
python scripts/translate_db.py
```

To force update existing translations:

```bash
python scripts/translate_db.py --force
```