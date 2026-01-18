# Phone Number Management System

A web application for managing phone numbers and endpoints across multiple organizations and service providers. Check availability, create endpoints, browse inventory, and view analytics - all with secure data storage.

## What It Does

Manage phone number inventory across different organizations (Axis Bank, IDFC, Mahindra Finance) and their providers. The app loads data from APIs, stores it temporarily in memory, and clears it automatically when you switch contexts or close the app.

### Supported Organizations

- **Axis Bank** - 1 provider (Exotel - Sarvam Axon)
- **IDFC** - 2 providers (Sarvam 1M, Axonwise 1M)
- **Mahindra Finance** - 3 providers (Sarvam, Axonwise 1M, MMFSL)

## Features

**Check Availability**
Verify if phone numbers are available before using them. Check single numbers or bulk check multiple numbers at once.

**Create Endpoints**
Create endpoints for single or multiple phone numbers. Option to check availability before creating.

**Browse Numbers**
View all available numbers in a table. Search by prefix, adjust page size, and download as CSV.

**Analytics**
See statistics about your phone numbers: total count, unique prefixes, distribution by area code, and visual charts.

## Installation

```bash
cd phone_numbers_automation
pip install -r requirements.txt
```

## Setup

Create a `.env` file in the project root:

```bash
AXISBANK_TOKEN=your_token_here
IDFC_TOKEN=your_token_here
MAHINDRAFINANCE_TOKEN=your_token_here
```

**Important:** Don't use quotes around the token values.

## How to Run

```bash
streamlit run main.py
```

Open your browser to `http://localhost:8501`

## Adding New Organizations

Want to add a new organization?

**Step 1:** Add the token to your `.env` file

```bash
NEWORG_TOKEN=the_token_value
```

**Step 2:** Edit `streamlit_app/utils/multi_org_config.py` and add:

```python
"New Organization": {
    "domain": "neworg.com",
    "workspace": "workspace-id",
    "token_key": "NEWORG_TOKEN",
    "providers": [
        {"name": "Provider Name", "connection": "connection-id"}
    ]
}
```

**Step 3:** Restart the app

## Contributing

Contributions are welcome! If you'd like to improve this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Ideas for contributions:**

- Add support for new organizations
- Improve UI/UX design
- Add new analytics features
- Fix bugs or improve documentation
- Performance optimizations

---

Made with ❤️ for streamlined phone number management
